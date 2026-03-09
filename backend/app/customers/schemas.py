from datetime import datetime

from pydantic import BaseModel, Field

from app.models.entities import CustomerStatus


class CustomerCreateRequest(BaseModel):
    user_id: int
    kyc_full_name: str = Field(min_length=2, max_length=255)
    kyc_document_id: str = Field(min_length=3, max_length=100)


class CustomerStatusUpdateRequest(BaseModel):
    status: CustomerStatus


class CustomerResponse(BaseModel):
    id: int
    user_id: int
    status: CustomerStatus
    kyc_full_name: str
    kyc_document_id: str
    created_at: datetime

    class Config:
        from_attributes = True
