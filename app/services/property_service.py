"""Property business logic: CRUD, advanced search, photos, status transitions."""
from __future__ import annotations

from pathlib import Path
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import models as m
from app.database.models import utcnow
from app.repositories.audit import record
from app.security.permissions import require
from app.utils.duplicates import find_duplicate_property
from app.utils.files import validate_upload, store_photo
from app.validators.schemas import PropertyIn

_DENY = {"id", "created_at", "updated_at", "deleted_at"}


def _check(user, perm: str) -> None:
    if user is not None:
        require(user, perm)


def create_property(db: Session, user, data: dict) -> m.Property:
    _check(user, "properties.create")
    validated = PropertyIn(code=data.get("code", ""), city=data.get("city", ""),
                           address=data.get("address", ""), price=float(data.get("price") or 0),
                           monthly_rent=float(data.get("monthly_rent") or 0),
                           surface=float(data.get("surface") or 0),
                           rooms=int(data.get("rooms") or 0),
                           bedrooms=int(data.get("bedrooms") or 0),
                           bathrooms=int(data.get("bathrooms") or 0))
    if db.query(m.Property).filter(m.Property.code == validated.code).first():
        raise ValueError(f"Codice immobile duplicato: {validated.code}")
    dup = find_duplicate_property(db, validated.city, validated.address, validated.surface)
    if dup:
        raise ValueError(f"Possibile duplicato: {dup.code} ({dup.city}, {dup.address})")
    obj = m.Property(**{**data, "code": validated.code})
    # normalize enums from strings
    for f, enum in (("ptype", m.PropertyType), ("listing", m.ListingType),
                    ("status", m.PropertyStatus), ("energy_class", m.EnergyClass)):
        v = getattr(obj, f, None)
        if isinstance(v, str) and v:
            try:
                setattr(obj, f, enum(v))
            except ValueError:
                pass
    db.add(obj)
    db.flush()
    record(db, user, "create", "property", str(obj.id), new={"code": obj.code})
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(obj)
    return obj


def update_property(db: Session, user, prop_id: int, data: dict) -> m.Property:
    _check(user, "properties.edit")
    obj = db.get(m.Property, prop_id)
    if obj is None:
        raise ValueError("Immobile non trovato")
    old = {"code": obj.code, "status": str(obj.status), "price": obj.price}
    if "code" in data and data["code"] != obj.code:
        if db.query(m.Property).filter(m.Property.code == data["code"],
                                       m.Property.id != prop_id).first():
            raise ValueError("Codice immobile duplicato")
    for k, v in data.items():
        if hasattr(obj, k) and k not in _DENY:
            setattr(obj, k, v)
    for f, enum in (("ptype", m.PropertyType), ("listing", m.ListingType),
                    ("status", m.PropertyStatus), ("energy_class", m.EnergyClass)):
        v = getattr(obj, f, None)
        if isinstance(v, str) and v:
            try:
                setattr(obj, f, enum(v))
            except ValueError:
                pass
    record(db, user, "update", "property", str(obj.id), old=old,
           new={"code": obj.code, "status": str(obj.status), "price": obj.price})
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(obj)
    return obj


def archive_property(db: Session, user, prop_id: int) -> m.Property:
    _check(user, "properties.delete")
    obj = db.get(m.Property, prop_id)
    if obj is None:
        raise ValueError("Immobile non trovato")
    old = str(obj.status)
    obj.status = m.PropertyStatus.ARCHIVED
    obj.is_active = False
    obj.deleted_at = utcnow()
    record(db, user, "archive", "property", str(obj.id), old={"status": old}, new={"status": "archived"})
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return obj


def delete_property(db: Session, user, prop_id: int, hard: bool = False) -> None:
    _check(user, "properties.delete")
    obj = db.get(m.Property, prop_id)
    if obj is None:
        raise ValueError("Immobile non trovato")
    # keep history: block hard delete if contracts/payments exist
    n_contracts = db.query(m.Contract).filter(m.Contract.property_id == prop_id).count()
    if n_contracts and hard:
        raise ValueError("Impossibile eliminare: esistono contratti collegati. Usa archiviazione.")
    record(db, user, "delete", "property", str(prop_id), old={"code": obj.code})
    if hard and not n_contracts:
        db.delete(obj)
    else:
        obj.is_active = False
        obj.deleted_at = utcnow()
        obj.status = m.PropertyStatus.ARCHIVED
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def search_properties(db: Session, filters: dict, limit: int = 200, offset: int = 0) -> tuple[list[m.Property], int]:
    q = db.query(m.Property)
    if filters.get("only_active", True):
        q = q.filter(m.Property.is_active.is_(True))
    if filters.get("text"):
        t = f"%{filters['text']}%"
        q = q.filter(or_(m.Property.code.ilike(t), m.Property.city.ilike(t),
                         m.Property.address.ilike(t), m.Property.cap.ilike(t)))
    if filters.get("code"):
        q = q.filter(m.Property.code.ilike(f"%{filters['code']}%"))
    for f in ("city", "cap", "province"):
        if filters.get(f):
            q = q.filter(getattr(m.Property, f).ilike(f"%{filters[f]}%"))
    for f in ("ptype", "listing", "status", "energy_class"):
        if filters.get(f):
            try:
                enum_cls = {"ptype": m.PropertyType, "listing": m.ListingType,
                            "status": m.PropertyStatus, "energy_class": m.EnergyClass}[f]
                q = q.filter(getattr(m.Property, f) == enum_cls(filters[f]))
            except ValueError:
                pass
    if filters.get("price_min") not in (None, ""):
        q = q.filter(m.Property.price >= float(filters["price_min"]))
    if filters.get("price_max") not in (None, ""):
        q = q.filter(m.Property.price <= float(filters["price_max"]))
    if filters.get("rent_min") not in (None, ""):
        q = q.filter(m.Property.monthly_rent >= float(filters["rent_min"]))
    if filters.get("rent_max") not in (None, ""):
        q = q.filter(m.Property.monthly_rent <= float(filters["rent_max"]))
    if filters.get("surface_min") not in (None, ""):
        q = q.filter(m.Property.surface >= float(filters["surface_min"]))
    if filters.get("surface_max") not in (None, ""):
        q = q.filter(m.Property.surface <= float(filters["surface_max"]))
    for f in ("rooms", "bedrooms", "bathrooms"):
        if filters.get(f) not in (None, ""):
            q = q.filter(getattr(m.Property, f) >= int(filters[f]))
    for f in ("garage", "parking", "elevator", "garden", "terrace", "furnished"):
        if filters.get(f) in (True, "1", 1, "true", "True"):
            q = q.filter(getattr(m.Property, f).is_(True))
    if filters.get("owner_id"):
        q = q.filter(m.Property.owner_id == int(filters["owner_id"]))
    if filters.get("agent_id"):
        q = q.filter(m.Property.agent_id == int(filters["agent_id"]))
    total = q.count()
    rows = q.order_by(m.Property.updated_at.desc()).limit(limit).offset(offset).all()
    return rows, total


def add_photo(db: Session, user, property_id: int, src_path: str | Path) -> m.PropertyImage:
    _check(user, "properties.edit")
    obj = db.get(m.Property, property_id)
    if obj is None:
        raise ValueError("Immobile non trovato")
    src = validate_upload(src_path, kind="image")
    dest, thumb = store_photo(src, obj.code)
    existing = db.query(m.PropertyImage).filter(
        m.PropertyImage.property_id == property_id).count()
    img = m.PropertyImage(property_id=property_id, file_path=str(dest),
                          thumb_path=str(thumb),
                          is_primary=(existing == 0), sort_order=existing)
    db.add(img)
    db.flush()
    record(db, user, "create", "property_image", str(img.id), new={"property": obj.code})
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(img)
    return img


def set_primary_photo(db: Session, user, image_id: int) -> None:
    _check(user, "properties.edit")
    img = db.get(m.PropertyImage, image_id)
    if img is None:
        raise ValueError("Immagine non trovata")
    try:
        db.query(m.PropertyImage).filter(
            m.PropertyImage.property_id == img.property_id).update({"is_primary": False})
        img.is_primary = True
        record(db, user, "update", "property_image", str(img.id), new={"primary": True})
        db.commit()
    except Exception:
        db.rollback()
        raise


def delete_photo(db: Session, user, image_id: int) -> None:
    _check(user, "properties.edit")
    img = db.get(m.PropertyImage, image_id)
    if img is None:
        return
    record(db, user, "delete", "property_image", str(image_id))
    for p in (img.file_path, img.thumb_path):
        try:
            if p:
                Path(p).unlink(missing_ok=True)
        except Exception:
            pass
    db.delete(img)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
