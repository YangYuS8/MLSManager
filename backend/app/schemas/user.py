"""User schemas for API validation."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique username for login",
        examples=["johndoe"],
    )
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["john@example.com"],
    )
    full_name: str | None = Field(
        None,
        max_length=100,
        description="User's display name",
        examples=["John Doe"],
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (8-100 characters)",
        examples=["securepassword123"],
    )
    role: UserRole = Field(
        default=UserRole.MEMBER,
        description="User role (superadmin/admin/member)",
    )


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    email: EmailStr | None = Field(None, description="New email address")
    full_name: str | None = Field(None, description="New display name")
    role: UserRole | None = Field(None, description="New user role")
    is_active: bool | None = Field(None, description="Account active status")


class UserRead(UserBase):
    """Schema for reading user data."""

    id: int = Field(..., description="Unique user ID", examples=[1])
    role: UserRole = Field(..., description="User role")
    is_active: bool = Field(..., description="Whether account is active")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT token response."""

    access_token: str = Field(
        ...,
        description="JWT access token for authentication",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."],
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')",
    )


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str = Field(..., description="Subject (username)")
    exp: datetime = Field(..., description="Token expiration timestamp")
