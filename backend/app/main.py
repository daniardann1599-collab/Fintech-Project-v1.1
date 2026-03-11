from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.accounts.router import router as accounts_router
from app.audit.router import router as audit_router
from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import configure_logging
from app.core.middleware import RateLimitMiddleware, RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.customers.router import router as customers_router
from app.events.router import router as events_router
from app.ledger.router import router as ledger_router
from app.models import entities  # noqa: F401
from app.transfers.router import router as transfers_router
from app.investments.router import router as investments_router
from app.time_deposits.router import router as time_deposits_router
from app.loans.router import router as loans_router
from app.profile.router import router as profile_router
from app.cards.router import router as cards_router

configure_logging(settings.log_level)

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
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


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
        "modules": ["auth", "customers", "accounts", "ledger", "transfers", "audit", "events"],
        "principles": [
            "JWT Auth",
            "REST API",
            "WebSocket event stream",
            "Ledger is single source of truth",
            "Audit logging",
            "Outbox events",
            "Structured logging",
            "Rate limiting",
        ],
    }


app.include_router(auth_router)
app.include_router(customers_router)
app.include_router(accounts_router)
app.include_router(ledger_router)
app.include_router(transfers_router)
app.include_router(audit_router)
app.include_router(events_router)
app.include_router(investments_router)
app.include_router(time_deposits_router)
app.include_router(loans_router)
app.include_router(profile_router)
app.include_router(cards_router)
