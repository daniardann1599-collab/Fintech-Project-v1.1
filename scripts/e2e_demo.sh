#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
SUFFIX="$(date +%s)"
ADMIN_EMAIL="demo-admin-${SUFFIX}@example.com"
CUSTOMER_EMAIL="demo-customer-${SUFFIX}@example.com"

json_field() {
  local file="$1"
  local field="$2"
  python3 - "$file" "$field" <<'PY'
import json,sys
f,field=sys.argv[1],sys.argv[2]
with open(f) as fp:
    data=json.load(fp)
print(data.get(field,""))
PY
}

echo "[1/10] Register admin and customer"
curl -sS -X POST "$BASE_URL/register" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"AdminPass123\",\"role\":\"ADMIN\"}" >/tmp/e2e_admin.json
curl -sS -X POST "$BASE_URL/register" -H 'Content-Type: application/json' \
  -d "{\"email\":\"$CUSTOMER_EMAIL\",\"password\":\"CustomerPass123\",\"role\":\"CUSTOMER\"}" >/tmp/e2e_customer.json

CUSTOMER_USER_ID="$(json_field /tmp/e2e_customer.json id)"

echo "[2/10] Login users"
curl -sS -X POST "$BASE_URL/auth/token" -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "username=$ADMIN_EMAIL&password=AdminPass123" >/tmp/e2e_admin_token.json
curl -sS -X POST "$BASE_URL/auth/token" -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "username=$CUSTOMER_EMAIL&password=CustomerPass123" >/tmp/e2e_customer_token.json

ADMIN_TOKEN="$(json_field /tmp/e2e_admin_token.json access_token)"
CUSTOMER_TOKEN="$(json_field /tmp/e2e_customer_token.json access_token)"

echo "[3/10] Create customer profile (KYC)"
curl -sS -X POST "$BASE_URL/customers" -H "Authorization: Bearer $CUSTOMER_TOKEN" -H 'Content-Type: application/json' \
  -d "{\"user_id\":$CUSTOMER_USER_ID,\"kyc_full_name\":\"Demo User\",\"kyc_document_id\":\"DEMO-001\"}" >/tmp/e2e_customer_profile.json
CUSTOMER_ID="$(json_field /tmp/e2e_customer_profile.json id)"

echo "[4/10] Open two accounts"
curl -sS -X POST "$BASE_URL/accounts" -H "Authorization: Bearer $CUSTOMER_TOKEN" -H 'Content-Type: application/json' \
  -d "{\"customer_id\":$CUSTOMER_ID,\"currency\":\"USD\"}" >/tmp/e2e_account1.json
curl -sS -X POST "$BASE_URL/accounts" -H "Authorization: Bearer $CUSTOMER_TOKEN" -H 'Content-Type: application/json' \
  -d "{\"customer_id\":$CUSTOMER_ID,\"currency\":\"USD\"}" >/tmp/e2e_account2.json
A1="$(json_field /tmp/e2e_account1.json id)"
A2="$(json_field /tmp/e2e_account2.json id)"

echo "[5/10] Initial deposit"
curl -sS -X POST "$BASE_URL/accounts/$A1/deposit" -H "Authorization: Bearer $CUSTOMER_TOKEN" -H 'Content-Type: application/json' \
  -d '{"amount":150,"reference_id":"demo-initial-deposit"}' >/tmp/e2e_deposit.json

echo "[6/10] Initiate transfer"
curl -sS -X POST "$BASE_URL/transfers/initiate" -H "Authorization: Bearer $CUSTOMER_TOKEN" -H 'Content-Type: application/json' \
  -d "{\"from_account\":$A1,\"to_account\":$A2,\"amount\":40}" >/tmp/e2e_transfer_init.json
TRANSFER_ID="$(json_field /tmp/e2e_transfer_init.json id)"

echo "[7/10] Execute transfer (full validation)"
curl -sS -X POST "$BASE_URL/transfers/$TRANSFER_ID/execute" -H "Authorization: Bearer $CUSTOMER_TOKEN" >/tmp/e2e_transfer_exec.json

echo "[8/10] Check balances"
curl -sS -H "Authorization: Bearer $CUSTOMER_TOKEN" "$BASE_URL/accounts/$A1/balance" >/tmp/e2e_balance_a1.json
curl -sS -H "Authorization: Bearer $CUSTOMER_TOKEN" "$BASE_URL/accounts/$A2/balance" >/tmp/e2e_balance_a2.json

echo "[9/10] Verify ledger integrity"
curl -sS -H "Authorization: Bearer $CUSTOMER_TOKEN" "$BASE_URL/ledger/accounts/$A1/verify" >/tmp/e2e_verify_a1.json


echo "[10/10] Review admin audit logs"
curl -sS -H "Authorization: Bearer $ADMIN_TOKEN" "$BASE_URL/audit/logs" >/tmp/e2e_audit.json

python3 - <<'PY'
import json
files = {
  "transfer_execution": "/tmp/e2e_transfer_exec.json",
  "balance_from": "/tmp/e2e_balance_a1.json",
  "balance_to": "/tmp/e2e_balance_a2.json",
  "ledger_verify": "/tmp/e2e_verify_a1.json",
  "audit_logs": "/tmp/e2e_audit.json",
}
result = {}
for key, path in files.items():
    with open(path) as f:
        result[key] = json.load(f)

summary = {
    "transfer_status": result["transfer_execution"].get("transfer", {}).get("status"),
    "from_balance": result["balance_from"].get("balance"),
    "to_balance": result["balance_to"].get("balance"),
    "ledger_valid": result["ledger_verify"].get("is_valid"),
    "audit_count": len(result["audit_logs"]) if isinstance(result["audit_logs"], list) else None,
}
print(json.dumps(summary, indent=2))
PY
