# Final Architecture Diagram

```mermaid
flowchart LR
  Client["Client Web App"] --> Auth["Auth Layer (JWT)"]
  Auth --> API["FastAPI Modular Monolith\nauth / customers / accounts / ledger / transfers / audit"]

  API --> DB[(PostgreSQL)]
  API --> Audit["Audit Logs"]
  API --> Outbox["Outbox Events"]
  Outbox --> WS["WebSocket Event Stream"]

  API --> RBAC["RBAC Guard\nADMIN / CUSTOMER"]
  API --> Rate["Rate Limiter"]
  API --> Validate["Input Validation"]
  API --> StructLogs["Structured Request Logs"]

  DB --> Ledger["Ledger Entries\nSingle Source of Truth"]
  Ledger --> Verify["Ledger Verification APIs"]
```

## Data Flow Summary
1. User authenticates and receives JWT.
2. JWT + RBAC gate all protected operations.
3. Financial writes are recorded in ledger and business tables transactionally.
4. Audit logs capture actor/action/outcome/timestamp.
5. Outbox events are emitted for async/event consumers and WebSocket snapshots.
