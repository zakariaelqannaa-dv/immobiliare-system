"""Pydantic validation schemas (service-layer input validation)."""
from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator, model_validator


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

    @field_validator("city", "address")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class ClientIn(BaseModel):
    first_name: str = Field(default="", max_length=80)
    last_name: str = Field(default="", max_length=80)
    email: str = Field(default="", max_length=160)
    max_price: float = Field(default=0, ge=0)
    min_price: float = Field(default=0, ge=0)

    @field_validator("email")
    @classmethod
    def _email(cls, v: str) -> str:
        v = v.strip().lower()
        if v and "@" not in v:
            raise ValueError("Email non valida")
        return v

    @model_validator(mode="after")
    def _price_range(self):
        if self.min_price and self.max_price and self.min_price > self.max_price:
            raise ValueError("Prezzo min superiore al max")
        return self


class ContractIn(BaseModel):
    number: str = Field(min_length=2, max_length=40)
    price: float = Field(ge=0)
    start_date: date
    end_date: date | None = None

    @field_validator("number")
    @classmethod
    def _num(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Numero obbligatorio")
        return v

    @model_validator(mode="after")
    def _dates(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("Data fine precedente all'inizio")
        return self


class PaymentIn(BaseModel):
    amount: float = Field(gt=0)
    due_date: date
    reference: str | None = Field(default=None, max_length=80)

    @field_validator("reference")
    @classmethod
    def _ref(cls, v):
        if v is None:
            return None
        v = v.strip() or None
        return v


class VisitIn(BaseModel):
    scheduled_at: datetime
    property_id: int = Field(gt=0)
    client_id: int = Field(gt=0)
