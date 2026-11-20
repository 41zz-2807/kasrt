import hashlib
import os
from datetime import datetime, timezone

from itsdangerous import URLSafeTimedSerializer

from app import db
from app.models.master import Category, DuesRate, DuesType, House
from app.models.finance import Invoice, PeriodLock, Transaction


def _csrf_serializer(client):
    return URLSafeTimedSerializer(client.application.secret_key, salt="wtf-csrf-token")


def csrf_token(client):
    value = hashlib.sha1(os.urandom(64)).hexdigest()
    with client.session_transaction() as sess:
        sess["csrf_token"] = value
    return _csrf_serializer(client).dumps(value)


def login(client, username, password):
    return client.post(
        "/login",
        data={"username": username, "password": password, "csrf_token": csrf_token(client)},
        follow_redirects=False,
    )


def _make_house(app, blok="B", nomor="12", nama="Budi"):
    house = House(blok=blok, nomor=nomor, nama_penghuni=nama, is_active=True, start_period=None)
    db.session.add(house)
    db.session.commit()
    return house


def _make_dues_type(app, nama="Iuran", nominal=50000, effective_period="2026-01"):
    dues_type = DuesType(nama=nama, is_active=True)
    db.session.add(dues_type)
    db.session.commit()
    db.session.add(DuesRate(dues_type_id=dues_type.id, nominal=nominal, effective_period=effective_period, created_by=1))
    db.session.commit()
    return dues_type


def _make_invoice(app, house, dues_type, period, nominal, status="belum"):
    inv = Invoice(house_id=house.id, dues_type_id=dues_type.id, period=period, nominal=nominal, paid_amount=0, status=status)
    db.session.add(inv)
    db.session.commit()
    return inv


def test_pay_less_than_due_is_sebatan(client, superuser, app):
    assert login(client, "admin", "supersecret1").status_code == 302
    with app.app_context():
        house = _make_house(app)
        dues_type = _make_dues_type(app)
        inv = _make_invoice(app, house, dues_type, "2026-11", 50000)

        from app.services import finance_service

        finance_service.create_payment(
            house_id=house.id,
            dues_type_id=dues_type.id,
            amount=30000,
            keterangan="Bayar 30 rb",
            created_by=1,
            category_id=None,
            bulan_list=[],
            kelebihan="B",
        )
        inv = db.session.get(Invoice, inv.id)
        assert inv.status == "sebagian"
        assert inv.paid_amount == 30000


def test_pay_three_open_months_lunas(client, superuser, app):
    assert login(client, "admin", "supersecret1").status_code == 302
    with app.app_context():
        house = _make_house(app)
        dues_type = _make_dues_type(app)
        inv9 = _make_invoice(app, house, dues_type, "2026-09", 50000)
        inv10 = _make_invoice(app, house, dues_type, "2026-10", 50000)
        inv11 = _make_invoice(app, house, dues_type, "2026-11", 50000)

        from app.services import finance_service

        finance_service.create_payment(
            house_id=house.id,
            dues_type_id=dues_type.id,
            amount=150000,
            keterangan="Bayar 3 bulan",
            created_by=1,
            category_id=None,
            bulan_list=[],
            kelebihan="B",
        )
        assert db.session.get(Invoice, inv9.id).status == "lunas"
        assert db.session.get(Invoice, inv9.id).paid_amount == 50000
        assert db.session.get(Invoice, inv10.id).status == "lunas"
        assert db.session.get(Invoice, inv11.id).status == "lunas"


def test_advance_payment_creates_and_luns_months(client, superuser, app):
    assert login(client, "admin", "supersecret1").status_code == 302
    with app.app_context():
        house = _make_house(app)
        dues_type = _make_dues_type(app)
        from app.services import finance_service

        trx = finance_service.create_payment(
            house_id=house.id,
            dues_type_id=dues_type.id,
            amount=150000,
            keterangan="Bayar di muka 3 bulan",
            created_by=1,
            category_id=None,
            bulan_list=["2026-12", "2027-01", "2027-02"],
            kelebihan="B",
        )
        invs = db.session.query(Invoice).filter(Invoice.house_id == house.id, Invoice.period.in_(["2026-12", "2027-01", "2027-02"])).all()
        assert len(invs) == 3
        for inv in invs:
            assert inv.status == "lunas"
            assert inv.paid_amount == inv.nominal


def test_overpay_option_b_creates_sumbangan_warga(client, superuser, app):
    assert login(client, "admin", "supersecret1").status_code == 302
    with app.app_context():
        house = _make_house(app)
        dues_type = _make_dues_type(app)
        inv = _make_invoice(app, house, dues_type, "2026-11", 50000)
        system_category = Category(nama="Sumbangan warga", jenis="masuk", is_system=True, is_active=True)
        db.session.add(system_category)
        db.session.commit()

        from app.services import finance_service

        finance_service.create_payment(
            house_id=house.id,
            dues_type_id=dues_type.id,
            amount=80000,
            keterangan="Bayar 80 rb",
            created_by=1,
            category_id=None,
            bulan_list=[],
            kelebihan="B",
        )
        inv = db.session.get(Invoice, inv.id)
        assert inv.status == "lunas"
        surplus = Transaction.query.filter_by(jenis="non_rutin", house_id=house.id).order_by(Transaction.id.desc()).first()
        assert surplus is not None
        assert surplus.jumlah == 30000
        category = Category.query.filter_by(nama="Sumbangan warga", is_system=True).first()
        assert category is not None
        assert surplus.category_id == category.id


def test_void_reverses_invoice_and_blocked_when_locked(client, superuser, app):
    assert login(client, "admin", "supersecret1").status_code == 302
    with app.app_context():
        house = _make_house(app)
        dues_type = _make_dues_type(app)
        inv = _make_invoice(app, house, dues_type, "2026-11", 50000)

        from app.services import finance_service

        trx = finance_service.create_payment(
            house_id=house.id,
            dues_type_id=dues_type.id,
            amount=50000,
            keterangan="Bayar 50 rb",
            created_by=1,
            category_id=None,
            bulan_list=[],
            kelebihan="B",
        )
        inv = db.session.get(Invoice, inv.id)
        assert inv.status == "lunas"

        ok = finance_service.void_transaction(trx.id, user_id=1, reason="Salah input")
        assert ok is True
        inv = db.session.get(Invoice, inv.id)
        assert inv.paid_amount == 0
        assert inv.status == "belum"
        assert db.session.get(Transaction, trx.id).status == "void"

        db.session.add(PeriodLock(period="2026-11", locked_by=1, locked_at=datetime.now(timezone.utc).replace(tzinfo=None)))
        db.session.commit()
        trx2 = finance_service.create_payment(
            house_id=house.id,
            dues_type_id=dues_type.id,
            amount=50000,
            keterangan="Bayar 2",
            created_by=1,
            category_id=None,
            bulan_list=[],
            kelebihan="B",
        )
        assert finance_service.void_transaction(trx2.id, user_id=1, reason="x") is False
