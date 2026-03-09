from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.audit.service import log_action
from app.auth.schemas import TokenResponse, UserRegisterRequest, UserResponse
from app.auth.service import authenticate_user, register_user
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.models.entities import User

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)) -> User:
    try:
        user = register_user(db, payload.email, payload.password, payload.role)
        log_action(db, user.id, "user.register", "SUCCESS")
        db.commit()
        db.refresh(user)
        return user
    except ValueError as exc:
        db.rollback()
        log_action(db, None, "user.register", "FAILED")
        db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/auth/token", response_model=TokenResponse)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        log_action(db, None, "user.login", "FAILED")
        db.commit()
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(subject=str(user.id), expires_delta=access_token_expires)
    log_action(db, user.id, "user.login", "SUCCESS")
    db.commit()
    return TokenResponse(access_token=access_token)


@router.get("/auth/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
