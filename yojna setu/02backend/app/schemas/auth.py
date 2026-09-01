from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, model_validator
from app.models.user import UserRole


class UserRegisterRequest(BaseModel):
    email: Optional[EmailStr] = Field(default=None, description="User email address")
    phone: Optional[str] = Field(default=None, description="User phone number")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    role: Optional[UserRole] = Field(default=UserRole.BENEFICIARY, description="Requested user role")
    preferred_language: Optional[str] = Field(default="en", description="Preferred language code e.g. hi, bn, ta, te, mr")

    @model_validator(mode="after")
    def check_identifier_provided(self):
        if not self.email and not self.phone:
            raise ValueError("Registration requires at least an email or phone number.")
        if self.phone:
            cleaned = self.phone.strip()
            if len(cleaned) < 8 or len(cleaned) > 15:
                raise ValueError("Phone number must be between 8 and 15 digits.")
        return self


class UserLoginRequest(BaseModel):
    identifier: Optional[str] = Field(default=None, description="Email address or phone number")
    username: Optional[str] = Field(default=None, description="Alias for identifier")
    password: str = Field(..., description="User password")

    @model_validator(mode="after")
    def validate_identifier(self):
        if not self.identifier and self.username:
            self.identifier = self.username
        if not self.identifier:
            raise ValueError("Email address or phone number (identifier) is required.")
        return self


class GoogleLoginRequest(BaseModel):
    id_token: str = Field(..., description="Google ID Token issued by Google Identity Services")
    preferred_language: Optional[str] = Field(default="en", description="Citizen preferred language")


class UserResponse(BaseModel):
    user_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    auth_provider: Optional[str] = "LOCAL"
    role: str
    is_active: bool
    preferred_language: Optional[str] = "en"
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
