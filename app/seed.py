"""Safe development seed (fake data only). Usage: python -m app.seed [--reset]"""
from __future__ import annotations

import argparse
import random
from datetime import date, datetime, timedelta

from app.config.settings import settings
from app.database.connection import init_db, get_session
from app.database import models as m
from app.services.platform_service import ensure_roles_permissions, create_user


CITIES = ["Milano", "Roma", "Torino", "Bologna", "Firenze", "Napoli", "Verona"]


def seed(reset: bool = False) -> None:
    settings.ensure_dirs()
    if reset:
        import pathlib
        p = settings.db_url.replace("sqlite:///", "", 1)
        try:
            pathlib.Path(p).unlink(missing_ok=True)
        except Exception:
            pass
    init_db()
    db = get_session()
    try:
        ensure_roles_permissions(db)
        # users
        specs = [("admin", "admin@immobiliare.local", "Admin123!", "Amministratore", ["ADMIN"]),
                 ("manager", "manager@immobiliare.local", "Manager123!", "Manager", ["MANAGER"]),
                 ("agente", "agente@immobiliare.local", "Agente123!", "Agente Rossi", ["AGENT"]),
                 ("contabile", "contabile@immobiliare.local", "Contabile123!", "Contabile", ["ACCOUNTANT"]),
                 ("viewer", "viewer@immobiliare.local", "Viewer123!", "Ospite", ["VIEWER"])]
        for username, email, pw, name, roles in specs:
            if not db.query(m.User).filter_by(username=username).first():
                try:
                    create_user(db, None, username, email, pw, name, roles)
                except Exception as e:
                    print("seed user:", e)
        # agents
        if db.query(m.Agent).count() == 0:
            for i, (fn, ln) in enumerate([("Marco", "Rossi"), ("Laura", "Bianchi")]):
                db.add(m.Agent(first_name=fn, last_name=ln,
                               email=f"agente{i}@demo.local", phone=f"33300000{i}"))
            db.commit()
        # owners
        if db.query(m.Owner).count() == 0:
            for i in range(5):
                db.add(m.Owner(first_name=f"Prop{i}", last_name="Demo",
                               email=f"prop{i}@demo.local", phone=f"34000000{i}",
                               city=random.choice(CITIES), fiscal_code=f"DEMO{i:05d}"))
            db.commit()
        # clients
        if db.query(m.Client).count() == 0:
            for i in range(8):
                db.add(m.Client(first_name=f"Cliente{i}", last_name="Demo",
                                email=f"cli{i}@demo.local", phone=f"34700000{i}",
                                client_type="buyer", max_price=150000 + i * 50000,
                                min_surface=50 + i * 5,
                                desired_cities="Milano, Roma",
                                desired_rooms=2 + (i % 3)))
            db.commit()
        # properties
        if db.query(m.Property).count() == 0:
            owners = db.query(m.Owner).all()
            agents = db.query(m.Agent).all()
            for i in range(12):
                city = random.choice(CITIES)
                listing = m.ListingType.SALE if i % 2 == 0 else m.ListingType.RENT
                db.add(m.Property(
                    code=f"IMM-{i + 1:04d}", ptype=random.choice(list(m.PropertyType)),
                    listing=listing, status=m.PropertyStatus.AVAILABLE,
                    address=f"Via Demo {i + 1}", city=city, province="MI",
                    cap=f"201{i:02d}", surface=60 + i * 7, rooms=2 + (i % 4),
                    bedrooms=1 + (i % 3), bathrooms=1 + (i % 2),
                    price=120000 + i * 25000 if listing == m.ListingType.SALE else 0,
                    monthly_rent=0 if listing == m.ListingType.SALE else 700 + i * 60,
                    garage=bool(i % 2), elevator=bool(i % 3 == 0), furnished=bool(i % 2 == 0),
                    owner_id=random.choice(owners).id if owners else None,
                    agent_id=random.choice(agents).id if agents else None,
                    description="Immobile demo generato dal seed (dati fittizi)."))
            db.commit()
        # visits / contracts / payments
        if db.query(m.Visit).count() == 0:
            props = db.query(m.Property).limit(5).all()
            clis = db.query(m.Client).limit(5).all()
            for p, c in zip(props, clis):
                db.add(m.Visit(property_id=p.id, client_id=c.id,
                               scheduled_at=datetime.utcnow() + timedelta(days=2),
                               status=m.VisitStatus.SCHEDULED, notes="Visita demo"))
            db.commit()
        if db.query(m.Contract).count() == 0:
            props = db.query(m.Property).limit(3).all()
            clis = db.query(m.Client).limit(3).all()
            for i, (p, c) in enumerate(zip(props, clis)):
                db.add(m.Contract(number=f"CTR-2026-{i + 1:03d}",
                                  ctype=m.ContractType.RENTAL, status=m.ContractStatus.ACTIVE,
                                  property_id=p.id, client_id=c.id,
                                  start_date=date(2026, 1, 1), price=900 + i * 100,
                                  deposit=1800))
            db.commit()
        if db.query(m.Payment).count() == 0:
            contracts = db.query(m.Contract).all()
            for i, c in enumerate(contracts):
                db.add(m.Payment(contract_id=c.id, amount=c.price,
                                 due_date=date(2026, 9, 5 + i), method="transfer",
                                 status=m.PaymentStatus.PENDING, reference=f"PAY-2026-{i + 1:04d}"))
            db.commit()
        print("Seed completato (dati fittizi).")
    finally:
        db.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()
    seed(reset=args.reset)
