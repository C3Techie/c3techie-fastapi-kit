from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, HttpUrl
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.utils.validators import (
    validate_username,
    validate_optional_password,
    validate_optional_username,
    validate_phone_number,
    validate_name,
    empty_string_to_none
)
from app.core.password_policy import PasswordPolicy

PHONE_NUMBER_REGEX = r"^\+?[1-9]\d{1,14}$"


class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr = Field(..., max_length=100)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8, max_length=255)
    phone_number: Optional[str] = Field(None, pattern=PHONE_NUMBER_REGEX)
    profile_image_url: Optional[HttpUrl] = Field(None, max_length=255)

    @field_validator('email')
    @classmethod
    def normalize_and_validate_email(cls, v):
        if v is None:
            return v
        return v.lower()

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        """Ensures password meets security requirements."""
        return PasswordPolicy.validate(v)

    @field_validator('username')
    @classmethod
    def normalize_and_validate_username(cls, v):
        """Lowercases and validates the username."""
        v = v.lower()
        return validate_username(v)

    @field_validator('first_name', 'last_name')
    @classmethod
    def name_format(cls, v):
        return validate_name(v)

    @field_validator('phone_number')
    @classmethod
    def phone_validation(cls, v):
        """Validates E.164 phone number format when provided."""
        if v is None:
            return v
        return validate_phone_number(v, strict=True)

    @field_validator('profile_image_url', mode='before')
    @classmethod
    def handle_empty_string(cls, v):
        return empty_string_to_none(v)


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: Optional[EmailStr] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    password: Optional[str] = Field(None, min_length=8, max_length=255)
    phone_number: Optional[str] = Field(None, pattern=PHONE_NUMBER_REGEX)
    profile_image_url: Optional[HttpUrl] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    email_verified: Optional[bool] = None

    @field_validator('email')
    @classmethod
    def normalize_and_validate_email(cls, v):
        if v is None:
            return v
        return v.lower()

    @field_validator('password')
    @classmethod
    def password_strength(cls, v):
        """Conditional password validation when provided."""
        return validate_optional_password(v)

    @field_validator('username')
    @classmethod
    def normalize_and_validate_username(cls, v):
        if v is None:
            return v
        v = v.lower()
        return validate_optional_username(v)

    @field_validator('first_name', 'last_name')
    @classmethod
    def name_format_optional(cls, v):
        if v is None:
            return v
        return validate_name(v)

    @field_validator('phone_number')
    @classmethod
    def phone_validation(cls, v):
        """Validates E.164 phone number format when provided."""
        if v is None:
            return v
        return validate_phone_number(v, strict=True)

    @model_validator(mode='after')
    def check_at_least_one_field(self):
        """Ensures at least one field is provided for update."""
        if not any(field is not None for field in self.model_dump().values()):
            raise ValueError("At least one field must be provided")
        return self


class UserRead(UserBase):
    """Schema for reading user information."""
    id: UUID
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    email_verified: bool
    phone_number: Optional[str] = None
    profile_image_url: Optional[HttpUrl] = Field(None, max_length=255)

    class Config:
        from_attributes = True


class UserList(BaseModel):
    """Schema for paginated user listing."""
    users: List[UserRead]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class UserLogin(BaseModel):
    """Schema for user login."""
    identifier: str = Field(..., description="Username or email")
    password: str = Field(..., min_length=1, max_length=255)

    @field_validator('identifier')
    @classmethod
    def normalize_identifier(cls, v):
        return v.lower()


class UserPasswordChange(BaseModel):
    """Schema for changing user password."""
    current_password: str = Field(..., min_length=1, max_length=255)
    new_password: str = Field(..., min_length=8, max_length=255)

    @field_validator('new_password')
    @classmethod
    def password_strength(cls, v):
        """Ensures new password meets security requirements."""
        return PasswordPolicy.validate(v)
