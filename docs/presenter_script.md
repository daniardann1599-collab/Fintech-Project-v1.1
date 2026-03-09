# Presenter Script (Teacher Demo)

## Week 1 Script (8-10 min)

### 1) Opening (30 sec)
"Today we present a modular monolith web banking system. Our architecture is organized by banking domains: auth, customers, accounts, ledger, transfers, and audit."

### 2) Architecture (2 min)
"The data flow is: Client frontend -> FastAPI backend -> PostgreSQL database. Event publishing is done through a database outbox pattern. The ledger is the single source of truth for balances."

"In our module boundaries:
- Auth handles registration/login and JWT.
- Customers handles KYC profile and customer status.
- Accounts handles account lifecycle and funding operations.
- Transfers handles transfer initiation and execution.
- Ledger stores immutable financial entries.
- Audit logs actor/action/time/outcome for traceability."

### 3) Technology choices (2 min)
"We selected FastAPI for fast REST development and built-in OpenAPI docs. PostgreSQL is used because transactional consistency is critical for ledger data. Docker Compose gives reproducible local deployment."

### 4) Week 1 API demo (3 min)
"I will open Swagger at `/docs`.
- Create user with `POST /register`.
- Login with `POST /auth/token`.
- Create customer with `POST /customers`.
- Create account with `POST /accounts`.
- Fetch account by `GET /accounts/{id}`.
- Start transfer with `POST /transfers/initiate` and show `PENDING`."

### 5) Risks + Week 2 plan (1-2 min)
"Main risks were security hardening, transfer settlement validation, and audit compliance coverage. Week 2 plan was: add JWT/RBAC, rate limit/security middleware, structured logs, WebSocket events, audit admin views, and frontend integration."

---

## Week 2 Script (12-15 min)

### 1) Security implementation (3 min)
"Security controls now include:
- JWT auth and RBAC (Admin/Customer).
- Input validation across all payloads.
- Rate limiting middleware.
- CORS configuration by environment.
- Secure error envelope with request IDs.
- Security headers.
- Structured JSON logs for request/audit/event visibility."

"Security documentation is in `docs/security_notes.md`."

### 2) Ledger verification (2-3 min)
"Ledger remains append-only at API behavior level. Balances are derived from ledger entries only. We added verification endpoints:
- `GET /ledger/accounts/{account_id}/verify`
- `GET /ledger/verify/system` (admin)
These report account-level and system-level integrity checks."

### 3) UI/mobile integration demo (4-5 min)
"We built a working web frontend:
- Public landing page.
- Register/Login forms.
- Role-based redirect to customer/admin dashboards.
- Customer dashboard: account overview, transfer form, ledger history, profile/KYC.
- Admin dashboard: audit logs, transactions monitor, customer management, balance controls."

### 4) Lessons learned (1-2 min)
"The key lesson is that banking flows become much simpler when ledger and audit are designed as first-class modules. Security middleware and centralized error handling also improve operational readiness significantly."

### 5) Week 2 end-to-end demo statement (30 sec)
"At this stage we can authenticate, manage customer/account resources, initiate and execute transfers, inspect ledger integrity, and review admin audit trails in one integrated stack."

---

## Week 3 Final End-to-End Script (Live Flow)

### Demo narrative (say while executing)
"Now I will show the full banking flow from scratch:
1. Register a user and log in.
2. Create customer profile (KYC).
3. Open accounts.
4. Post initial deposit.
5. Initiate transfer.
6. Execute transfer with validation.
7. Verify ledger entries and balances.
8. Review audit logs as admin."

### Exact talk track
"First, we register and authenticate."
"Now we create the customer KYC profile."
"Next, we open two accounts under this customer."
"We perform an initial deposit to fund the source account."
"Now we initiate a transfer, which starts in `PENDING` state."
"Then we execute the transfer through the settlement endpoint."
"You can see updated balances: source decreased, destination increased."
"Now we call ledger verification to confirm integrity checks pass."
"Finally, admin opens audit logs and we can trace each action with user, timestamp, and outcome."

### Closing sentence
"This demonstrates a complete, auditable, role-secured, ledger-driven banking transaction lifecycle in our modular monolith architecture."
