from pydantic import BaseModel, EmailStr, Field

from app.models.entities import CustomerStatus


class ProfileResponse(BaseModel):
    user_id: int
    customer_id: int | None
    status: CustomerStatus | None
    email: EmailStr
    full_name: str | None
    document_id: str | None
    phone: str | None
    address: str | None
    city: str | None
    country: str | None


class ProfileUpdateRequest(BaseModel):
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)
