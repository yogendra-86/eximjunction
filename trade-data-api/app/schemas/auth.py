"""Pydantic schemas for auth endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- Customer signup/login ---

class CustomerSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str | None = Field(None, max_length=200)
    company_name: str | None = Field(None, max_length=200)
    phone: str | None = Field(None, max_length=40)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in_minutes: int


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    full_name: str | None = None
    company_name: str | None = None
    phone: str | None = None
    is_active: bool
    email_verified: bool
    created_at: datetime


class AdminUserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    is_active: bool
    created_at: datetime


# --- API keys ---

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)


class APIKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    key_prefix: str
    name: str
    tier: str
    daily_limit_override: int | None = None
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None = None


class APIKeyCreated(APIKeyOut):
    plaintext_key: str = Field(..., description="Save this NOW. It is shown only once.")


class APIKeyUsageStat(BaseModel):
    usage_date: str
    request_count: int


class APIKeyUsageReport(BaseModel):
    key_prefix: str
    name: str
    tier: str
    daily_limit: int | None
    total_requests_30d: int
    daily: list[APIKeyUsageStat]
