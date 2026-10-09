"""Normalized SQLAlchemy models with constraints, indexes, soft-delete, timestamps."""
from __future__ import annotations

import enum
from datetime import datetime, date, timezone
from typing import Optional
from sqlalchemy import (
    Boolean, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text,
    UniqueConstraint, Index, Table, Column,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------- Enums ----------
class PropertyType(str, enum.Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    VILLA = "villa"
    OFFICE = "office"
    SHOP = "shop"
    WAREHOUSE = "warehouse"
    LAND = "land"
    GARAGE = "garage"
    OTHER = "other"


class ListingType(str, enum.Enum):
    SALE = "sale"
    RENT = "rent"
    BOTH = "both"


class PropertyStatus(str, enum.Enum):
    DRAFT = "draft"
    AVAILABLE = "available"
    RESERVED = "reserved"
    UNDER_OFFER = "under_offer"
    SOLD = "sold"
    RENTED = "rented"
    ARCHIVED = "archived"


class EnergyClass(str, enum.Enum):
    A4 = "A4"; A3 = "A3"; A2 = "A2"; A1 = "A1"; B = "B"; C = "C"; D = "D"
    E = "E"; F = "F"; G = "G"; NC = "NC"


class ContractType(str, enum.Enum):
    RENTAL = "rental"
    SALE = "sale"


class ContractStatus(str, enum.Enum):
    DRAFT = "draft"; ACTIVE = "active"; EXPIRED = "expired"
    TERMINATED = "terminated"; CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"; PAID = "paid"; LATE = "late"; CANCELLED = "cancelled"


class VisitStatus(str, enum.Enum):
    SCHEDULED = "scheduled"; CONFIRMED = "confirmed"; COMPLETED = "completed"
    CANCELLED = "cancelled"; NO_SHOW = "no_show"


class AppointmentType(str, enum.Enum):
    VISIT = "visit"; MEETING = "meeting"; CONTRACT_DEADLINE = "contract_deadline"
    PAYMENT_DEADLINE = "payment_deadline"; TASK = "task"; REMINDER = "reminder"; OTHER = "other"


class TaskStatus(str, enum.Enum):
    TODO = "todo"; IN_PROGRESS = "in_progress"; DONE = "done"; CANCELLED = "cancelled"


# ---------- Association tables ----------
user_roles = Table(
    "user_roles", Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)

role_permissions = Table(
    "role_permissions", Base.metadata,
    Column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class SoftDeleteMixin:
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


# ---------- RBAC ----------
class Permission(Base):
    __tablename__ = "permissions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), default="")


class Role(Base, TimestampMixin):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), default="")
    permissions: Mapped[list[Permission]] = relationship(secondary=role_permissions, lazy="selectin")


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), default="")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reset_token: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    reset_expires: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    roles: Mapped[list[Role]] = relationship(secondary=user_roles, lazy="selectin")


# ---------- People ----------
class Owner(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "owners"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), default="person")  # person|company
    first_name: Mapped[str] = mapped_column(String(80), default="")
    last_name: Mapped[str] = mapped_column(String(80), default="")
    company_name: Mapped[str] = mapped_column(String(160), default="")
    email: Mapped[str] = mapped_column(String(160), default="", index=True)
    phone: Mapped[str] = mapped_column(String(60), default="")
    address: Mapped[str] = mapped_column(String(255), default="")
    city: Mapped[str] = mapped_column(String(100), default="", index=True)
    fiscal_code: Mapped[str] = mapped_column(String(32), default="", index=True)
    vat: Mapped[str] = mapped_column(String(32), default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    properties: Mapped[list[Property]] = relationship(back_populates="owner")

    @property
    def display_name(self) -> str:
        if self.kind == "company":
            return self.company_name or f"Owner #{self.id}"
        return f"{self.first_name} {self.last_name}".strip() or f"Owner #{self.id}"


class Agent(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "agents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(160), default="", index=True)
    phone: Mapped[str] = mapped_column(String(60), default="")
    commission_pct: Mapped[float] = mapped_column(Float, default=3.0)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Client(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80), default="")
    last_name: Mapped[str] = mapped_column(String(80), default="")
    email: Mapped[str] = mapped_column(String(160), default="", index=True)
    phone: Mapped[str] = mapped_column(String(60), default="")
    client_type: Mapped[str] = mapped_column(String(20), default="buyer")  # buyer|tenant|both|seller
    desired_type: Mapped[str] = mapped_column(String(20), default="")
    min_price: Mapped[float] = mapped_column(Float, default=0)
    max_price: Mapped[float] = mapped_column(Float, default=0)
    min_surface: Mapped[float] = mapped_column(Float, default=0)
    desired_cities: Mapped[str] = mapped_column(String(500), default="")
    desired_rooms: Mapped[int] = mapped_column(Integer, default=0)
    desired_bedrooms: Mapped[int] = mapped_column(Integer, default=0)
    requirements: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or f"Client #{self.id}"


class ClientFavorite(Base):
    __tablename__ = "client_favorites"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    __table_args__ = (UniqueConstraint("client_id", "property_id", name="uq_fav"),)


# ---------- Property ----------
class Property(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "properties"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    ptype: Mapped[PropertyType] = mapped_column(Enum(PropertyType), default=PropertyType.APARTMENT, index=True)
    listing: Mapped[ListingType] = mapped_column(Enum(ListingType), default=ListingType.SALE, index=True)
    status: Mapped[PropertyStatus] = mapped_column(Enum(PropertyStatus), default=PropertyStatus.DRAFT, index=True)
    address: Mapped[str] = mapped_column(String(255), default="")
    city: Mapped[str] = mapped_column(String(100), default="", index=True)
    province: Mapped[str] = mapped_column(String(10), default="", index=True)
    region: Mapped[str] = mapped_column(String(100), default="")
    cap: Mapped[str] = mapped_column(String(10), default="", index=True)
    floor: Mapped[str] = mapped_column(String(20), default="")
    rooms: Mapped[int] = mapped_column(Integer, default=0)
    bedrooms: Mapped[int] = mapped_column(Integer, default=0)
    bathrooms: Mapped[int] = mapped_column(Integer, default=0)
    surface: Mapped[float] = mapped_column(Float, default=0, index=True)
    commercial_surface: Mapped[float] = mapped_column(Float, default=0)
    garden: Mapped[bool] = mapped_column(Boolean, default=False)
    terrace: Mapped[bool] = mapped_column(Boolean, default=False)
    balcony: Mapped[bool] = mapped_column(Boolean, default=False)
    garage: Mapped[bool] = mapped_column(Boolean, default=False)
    parking: Mapped[bool] = mapped_column(Boolean, default=False)
    elevator: Mapped[bool] = mapped_column(Boolean, default=False)
    heating: Mapped[str] = mapped_column(String(60), default="")
    ac: Mapped[bool] = mapped_column(Boolean, default=False)
    furnished: Mapped[bool] = mapped_column(Boolean, default=False)
    pets: Mapped[bool] = mapped_column(Boolean, default=False)
    energy_class: Mapped[EnergyClass] = mapped_column(Enum(EnergyClass), default=EnergyClass.G)
    energy_consumption: Mapped[float] = mapped_column(Float, default=0)
    price: Mapped[float] = mapped_column(Float, default=0, index=True)
    monthly_rent: Mapped[float] = mapped_column(Float, default=0, index=True)
    condo_fees: Mapped[float] = mapped_column(Float, default=0)
    deposit: Mapped[float] = mapped_column(Float, default=0)
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("owners.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)

    owner: Mapped[Optional[Owner]] = relationship(back_populates="properties")
    images: Mapped[list[PropertyImage]] = relationship(back_populates="property", cascade="all, delete-orphan", order_by="PropertyImage.sort_order")

    __table_args__ = (
        Index("ix_prop_city_status", "city", "status"),
        Index("ix_prop_price", "price"),
    )


class PropertyImage(Base):
    __tablename__ = "property_images"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    thumb_path: Mapped[str] = mapped_column(String(500), default="")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    property: Mapped[Property] = relationship(back_populates="images")


# ---------- Operational ----------
class Visit(Base, TimestampMixin):
    __tablename__ = "visits"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    agent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("agents.id", ondelete="SET NULL"), index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[VisitStatus] = mapped_column(Enum(VisitStatus), default=VisitStatus.SCHEDULED, index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    follow_up: Mapped[str] = mapped_column(Text, default="")


class Appointment(Base, TimestampMixin):
    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    atype: Mapped[AppointmentType] = mapped_column(Enum(AppointmentType), default=AppointmentType.MEETING, index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    property_id: Mapped[Optional[int]] = mapped_column(ForeignKey("properties.id", ondelete="SET NULL"), index=True)
    client_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"), index=True)
    agent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("agents.id", ondelete="SET NULL"), index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)


class Contract(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "contracts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    number: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    ctype: Mapped[ContractType] = mapped_column(Enum(ContractType), default=ContractType.RENTAL, index=True)
    status: Mapped[ContractStatus] = mapped_column(Enum(ContractStatus), default=ContractStatus.DRAFT, index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="RESTRICT"), index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="RESTRICT"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("owners.id", ondelete="SET NULL"), index=True)
    agent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("agents.id", ondelete="SET NULL"), index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    renewal_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    price: Mapped[float] = mapped_column(Float, default=0)
    deposit: Mapped[float] = mapped_column(Float, default=0)
    conditions: Mapped[str] = mapped_column(Text, default="")


class Payment(Base, TimestampMixin):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_id: Mapped[Optional[int]] = mapped_column(ForeignKey("contracts.id", ondelete="SET NULL"), index=True)
    client_id: Mapped[Optional[int]] = mapped_column(ForeignKey("clients.id", ondelete="SET NULL"), index=True)
    property_id: Mapped[Optional[int]] = mapped_column(ForeignKey("properties.id", ondelete="SET NULL"), index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    paid_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    method: Mapped[str] = mapped_column(String(30), default="transfer")
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    reference: Mapped[Optional[str]] = mapped_column(String(80), default=None, nullable=True, index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    __table_args__ = (UniqueConstraint("reference", name="uq_payment_ref"),)


class Expense(Base, TimestampMixin):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[Optional[int]] = mapped_column(ForeignKey("properties.id", ondelete="SET NULL"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("owners.id", ondelete="SET NULL"), index=True)
    category: Mapped[str] = mapped_column(String(60), default="maintenance", index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="")


class Document(Base, TimestampMixin):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_type: Mapped[str] = mapped_column(String(20), index=True)  # property|owner|client|contract|payment
    owner_id: Mapped[int] = mapped_column(Integer, index=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime: Mapped[str] = mapped_column(String(100), default="")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(60), default="general")
    __table_args__ = (Index("ix_doc_owner", "owner_type", "owner_id"),)


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.TODO, index=True)
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    property_id: Mapped[Optional[int]] = mapped_column(ForeignKey("properties.id", ondelete="SET NULL"))
    priority: Mapped[int] = mapped_column(Integer, default=1)


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    username: Mapped[str] = mapped_column(String(80), default="")
    action: Mapped[str] = mapped_column(String(60), index=True)
    entity: Mapped[str] = mapped_column(String(60), index=True)
    entity_id: Mapped[str] = mapped_column(String(40), default="")
    old_value: Mapped[str] = mapped_column(Text, default="")
    new_value: Mapped[str] = mapped_column(Text, default="")
    result: Mapped[str] = mapped_column(String(20), default="ok")


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class BackupRecord(Base):
    __tablename__ = "backups"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
    note: Mapped[str] = mapped_column(String(255), default="")
