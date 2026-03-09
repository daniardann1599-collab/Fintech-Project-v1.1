# Security Notes

## Authentication and Authorization
- JWT bearer authentication is required for protected endpoints.
- `/auth/token` issues short-lived access tokens.
- Role-based access control is enforced for `ADMIN` and `CUSTOMER` operations.

## API Security Controls
- Input validation via Pydantic schemas and field constraints.
- Standardized secure error envelope:
  - `error.code`
  - `error.message`
  - `error.request_id`
- CORS is configurable through `CORS_ALLOWED_ORIGINS`.
- Security headers middleware sets:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: no-referrer`
  - `Cache-Control: no-store`
- Rate limiting middleware is configurable via:
  - `RATE_LIMIT_REQUESTS`
  - `RATE_LIMIT_WINDOW_SECONDS`

## Audit and Traceability
- Audit logs include:
  - `user_id`
  - `action`
  - `timestamp`
  - `outcome`
- Request logging is structured JSON with `request_id`, method, path, status, and latency.

## Secrets Management
- Runtime secrets are loaded from environment variables.
- `.env` is ignored by Git.
- `.env.example` provides a safe local template.
- Production recommendation: use secret manager or CI/CD protected secrets, never hardcode.

## Ledger Integrity
- Ledger is append-only at API behavior level.
- Balance is computed from ledger entries (`credit - debit`).
- Verification endpoints:
  - `GET /ledger/accounts/{account_id}/verify`
  - `GET /ledger/verify/system` (admin)
