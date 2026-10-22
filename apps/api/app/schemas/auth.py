import uuid
from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=150)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    status: str

    model_config = {"from_attributes": True}


class WorkspaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    role: str = "OWNER"

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserResponse
    workspace: WorkspaceResponse
