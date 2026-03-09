# Swagger v0.1 Draft (Archived)

This document captures the initial API draft before v1.0 finalization.

## Public Endpoints
- `POST /register`
- `POST /auth/token`

## Core Protected Endpoints
- `POST /customers`
- `GET /customers/{customer_id}`
- `POST /accounts`
- `GET /accounts/{account_id}`
- `GET /accounts/{account_id}/balance`
- `POST /transfers/initiate`

## Out of Scope in v0.1
- Transfer execution settlement (`/transfers/{id}/execute`)
- System ledger verification endpoints
- WebSocket event stream

## Notes
- Current live OpenAPI after upgrades is available at `/openapi.json` and `/docs`.
- Project version now targets `v1.0.0`.
