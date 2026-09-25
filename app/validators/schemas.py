"""Pydantic validation schemas (service-layer input validation)."""
from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator


class PropertyIn(BaseModel):
    code: str = Field(min_length=2, max_length=30)
    city: str = Field(min_length=1, max_length=100)
    address: str = Field(default="", max_length=255)
    price: float = Field(default=0, ge=0)
    monthly_rent: float = Field(default=0, ge=0)
    surface: float = Field(default=0, ge=0)
    rooms: int = Field(default=0, ge=0, le=60)
    bedrooms: int = Field(default=0, ge=0, le=40)
    bathrooms: int = Field(default=0, ge=0, le=30)

    @field_validator("code")
    @classmethod
    def _code(cls, v: str) -> str:
        v = v.strip().upper()
        if not v:
            raise ValueError("Codice obbligatorio")
        return v


class ClientIn(BaseModel):
    first_name: str = Field(default="", max_length=80)
    last_name: str = Field(default="", max_length=80)
    email: str = Field(default="", max_length=160)
    max_price: float = Field(default=0, ge=0)
    min_price: float = Field(default=0, ge=0)


class ContractIn(BaseModel):
    number: str = Field(min_length=2, max_length=40)
    price: float = Field(ge=0)
    start_date: date


class PaymentIn(BaseModel):
    amount: float = Field(gt=0)
    due_date: date


class VisitIn(BaseModel):
    scheduled_at: datetime
