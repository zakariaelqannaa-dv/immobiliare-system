from datetime import date
from app.services import property_service as psvc
from app.services import people_service as people
from app.services import deal_service as deal
from app.services import platform_service as plat


def _prop(i=1):
    return {"code": f"TST-{i:03d}", "city": "Milano", "address": f"Via T {i}",
            "price": 100000 + i, "surface": 80, "rooms": 3, "bedrooms": 2,
            "bathrooms": 1, "ptype": "apartment", "listing": "sale", "status": "available"}


def test_property_crud(db, admin):
    p = psvc.create_property(db, admin, _prop(1))
    assert p.id
    rows, total = psvc.search_properties(db, {"city": "Milano"})
    assert total >= 1
    p2 = psvc.update_property(db, admin, p.id, {"price": 123456})
    assert p2.price == 123456
    # duplicate code rejected
    try:
        psvc.create_property(db, admin, _prop(1))
        assert False, "expected duplicate"
    except ValueError:
        pass


def test_client_crud_and_matching(db, admin):
    c = people.create_client(db, admin, {"first_name": "A", "last_name": "B",
                                         "email": "ab@x.local", "max_price": 500000,
                                         "min_surface": 50, "desired_cities": "Milano",
                                         "desired_rooms": 2})
    psvc.create_property(db, admin, _prop(11))
    res = plat.match_properties_for_client(db, c.id)
    assert len(res) >= 1
    assert any("Citt" in ";".join(r["reasons"]) or "Prezzo" in ";".join(r["reasons"]) for r in res)


def test_contract_payment_flow(db, admin):
    p = psvc.create_property(db, admin, _prop(21))
    c = people.create_client(db, admin, {"first_name": "C", "last_name": "D",
                                         "email": "cd@x.local"})
    k = deal.create_contract(db, admin, {"number": "CTR-T1", "ctype": "rental",
                                         "property_id": p.id, "client_id": c.id,
                                         "price": 1000, "start_date": date(2026, 1, 1),
                                         "status": "draft"})
    assert k.id
    pay = deal.create_payment(db, admin, {"contract_id": k.id, "amount": 1000,
                                          "due_date": date(2026, 9, 30),
                                          "reference": "REF-T1"})
    assert pay.status.value in ("pending", "late")
    pay2 = deal.set_payment_status(db, admin, pay.id, "paid")
    assert pay2.status.value == "paid"


def test_permission_enforced(db):
    from app.services.platform_service import create_user
    v = create_user(db, None, "viewer1", "vw@x.local", "Strong123!", "V", ["VIEWER"])
    db.refresh(v)
    try:
        psvc.create_property(db, v, _prop(31))
        assert False
    except PermissionError:
        pass
