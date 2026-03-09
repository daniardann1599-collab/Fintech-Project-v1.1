from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.models.entities import User


def register_user(db: Session, email: str, password: str, role: str) -> User:
    existing_user = db.scalar(select(User).where(User.email == email))
    if existing_user:
        raise ValueError("User with this email already exists")

    user = User(email=email, password_hash=get_password_hash(password), role=role)
    db.add(user)
    db.flush()
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
