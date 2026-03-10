# Presenter Script 

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


**Checklist**

**1. Assignment Objective**
- `1.1` Design system architecture — **Done**
- `1.2` Technology trade‑off decisions — **Done** (documented)
- `1.3` Secure financial workflows — **Done**
- `1.4` DevOps tools — **Done** (Docker + CI)
- `1.5` Weekly presentations — **Not Done** (presentation is on you)

**2. Learning Outcomes**
- `2.2` Core banking architecture — **Done**
- `2.3` Ledger‑based transactions — **Done**
- `2.4` Secure APIs (auth/authorization) — **Done**
- `2.5` Docker containerization — **Done**
- `2.6` GitHub collaboration — **Not Done** (team process)
- `2.7` Financial data transfer & events — **Done**
- `2.8` Explain architecture in FinTech terms — **Done** (docs)

**3. Team Roles**
- `3.1–3.3`
- 3.2.) 1. System Architect Khumora / Project Lead Temirlan

3.2.1) Defines system boundaries and architecture Khumora

3.2.2) Maintains backlog and task prioritization Khumora

3.2.3) Leads weekly presentations — Temirlan 

3.2.4) 2. Backend & Data Engineer - Temirlan

3.2.5) Implements APIs and business logic

3.2.6) Designs database and ledger structure

3.2.7) Handles events and data consistency

3.3) Frontend Engineer - Khumora

3.3.1) Builds web interfaces

3.3.2) Sets up Docker and CI pipelines

3.3.3) Ensures deployment and demo readiness


**4. System Scope**
- `4.1.1` Customer creation — **Done**
- `4.1.2` Mock KYC — **Done**
- `4.1.3` Customer status management — **Done**
- `4.2.1` Account creation — **Done**
- `4.2.2` Balance inquiry — **Done**
- `4.2.3` Ownership linkage — **Done**
- `4.3.1` Ledger entry for every movement — **Done**
- `4.3.2` Append‑only ledger — **Done** (API behavior)
- `4.3.3` No balance change without ledger — **Done**
- `4.4.1` Deposits/withdrawals — **Done**
- `4.4.2` Updates via ledger — **Done**
- `4.5.1` Internal transfers — **Done**
- `4.5.2` Validation/authorization/recording — **Done**
- `4.6.1` Audit logs — **Done**
- `4.6.1` Admin audit access — **Done**

**5. Architecture Option**
- `5.1` Modular monolith — **Done**

**6. Technology Stack**
- `6.1` Backend: FastAPI — **Done**
- `6.1.6.1` REST API — **Done**
- `6.1.6.2` OpenAPI/Swagger — **Done**
- `6.1.6.3` Input validation — **Done**
- `6.1.6.4` Structured logging — **Done**
- `6.2` DB: PostgreSQL — **Done**
- `6.3.3` Database outbox — **Done**
- `6.3.5.1` TransferCreated — **Done** (outbox `TRANSFER_INITIATED`)
- `6.3.5.2` TransferCompleted — **Done** (outbox `TRANSFER_EXECUTED`)
- `6.3.5.3` AccountDebited — **Not Done** (explicit event name not emitted)
- `6.3.5.4` AccountCredited — **Not Done** (explicit event name not emitted)
- `6.4.1` Frontend: HTML/CSS/JS — **Done**
- `6.4.4.1` Login screen — **Done**
- `6.4.4.2` Account list — **Done**
- `6.4.4.3` Transfer form — **Done**
- `6.4.4.4` Ledger view — **Done**
- `6.4.4.5` Admin audit view — **Done**
- `6.5` Mobile app — **Not Done** (optional)

**7. Financial Data Transfer**
- `7.1` REST/JSON — **Done**
- `7.2` gRPC — **Not Done** (optional)
- `7.3` WebSockets — **Done**
- Standards mapping (ISO 20022/SWIFT/EMV/Open Banking) — **Done** (docs)

**8. Security Requirements**
- `8.1` Auth & authorization — **Done**
- `8.2` JWT — **Done**
- `8.3` RBAC — **Done**
- `8.4` API security — **Done**
- `8.5` Input validation — **Done**
- `8.6` Rate limiting — **Done**
- `8.7` CORS — **Done**
- `8.8` Secure error responses — **Done**
- `8.9` Audit logging — **Done**
- `8.10` User ID — **Done**
- `8.11` Action — **Done**
- `8.12` Timestamp — **Done**
- `8.13` Outcome — **Done**
- `8.14.1` `.env.example` — **Done**
- `8.14.2` No secrets in git — **Done**

**9. Docker & Deployment**
- `9.1` Docker Compose — **Done**
- `9.1.2` `docker compose up --build` — **Done**
- `9.1.4` Backend service — **Done**
- `9.1.5` Database service — **Done**
- `9.2` Backend Dockerfile — **Done**

**10. GitHub Workflow (CI/CD)**
- `10.1` Version control — **Not Done** (team process)
- `10.2` main/dev/feature branches — **Not Done** (team process)
- `10.3` Pull requests — **Not Done** (team process)
- `10.5` ≥3 PRs — **Not Done** (team process)
- `10.6` Issue board usage — **Not Done** (team process)
- `10.7` CI/CD — **Done** (GitHub Actions)
- `10.8` GitHub Actions — **Done**
- `10.9` Linting + testing — **Done** (CI)

**11. Repository Structure**
- `/docs/architecture.png` — **Done**
- `/docs/api.yaml` — **Done**
- `/docs/security_notes.md` — **Done**
- `/backend` — **Done**
- `/frontend` — **Done**
- `/infra/docker-compose.yml` — **Done**
- `.env.example` — **Done**
- `README.md` — **Done**

**12. Three‑Week Timeline**
- Week 1 Deliverables (architecture, Swagger v0.1, Docker, core APIs) — **Done**
- Week 1 Presentation — **Not Done** (presentation is on you)
- Week 2 Deliverables (JWT/RBAC, ledger verification, audit logs, UI demo, CI, Swagger v1.0, final arch, security overview, end‑to‑end demo) — **Done**
- Week 2 Presentation — **Not Done** (presentation is on you)
- Week 3 Flow (register→login→customer→account→deposit→transfer execute→verify ledger/balance→audit) — **Done**

**13. Evaluation Rubric**
- Architecture/modularity — **Done**
- Backend/data correctness — **Done**
- Security implementation — **Done**
- UI usability — **Done**
- DevOps/CI — **Done**
- Documentation/presentation — **Docs Done / Presentations Not Done**
