from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.accounts.router import router as accounts_router
from app.audit.router import router as audit_router
from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.database import Base, engine
from app.customers.router import router as customers_router
from app.ledger.router import router as ledger_router
from app.models import entities  # noqa: F401
from app.transfers.router import router as transfers_router

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "Modular Monolith Banking API with JWT auth, PostgreSQL ledger, "
        "audit logging, and outbox events."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/architecture")
def architecture() -> dict:
    return {
        "scheme": "Client -> Backend API -> Database; Event layer from DB outbox",
        "modules": ["auth", "customers", "accounts", "ledger", "transfers", "audit"],
        "principles": [
            "JWT Auth",
            "REST API",
            "Ledger is single source of truth",
            "Audit logging",
            "Outbox events",
        ],
    }


app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(accounts_router)
app.include_router(ledger_router)
app.include_router(transfers_router)
app.include_router(audit_router)
