from pydantic import BaseModel, EmailStr, Field

from app.models.entities import UserRole


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    role: UserRole = UserRole.CUSTOMER


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
