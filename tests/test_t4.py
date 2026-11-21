from datetime import datetime

from app import db
from app.models.master import Category, DuesRate, DuesType, House
from app.models.finance import Invoice, Transaction
from app.services import finance_service


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


def test_dashboard_renders(client, superuser):
    assert client.post(
        "/login",
        data={"username": "admin", "password": "supersecret1", "csrf_token": client_csrf(client)},
        follow_redirects=False,
    ).status_code == 302
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert 'id="menu-toggle"' in body
    assert 'id="sidebar-backdrop"' in body
    assert "/static/js/sidebar.js?v=" in body


def client_csrf(client):
    import hashlib
    import os

    from itsdangerous import URLSafeTimedSerializer

    value = hashlib.sha1(os.urandom(64)).hexdigest()
    with client.session_transaction() as sess:
        sess["csrf_token"] = value
    return URLSafeTimedSerializer(client.application.secret_key, salt="wtf-csrf-token").dumps(value)


def test_create_expense(client, superuser):
    assert client.post(
        "/login",
        data={"username": "admin", "password": "supersecret1", "csrf_token": client_csrf(client)},
        follow_redirects=False,
    ).status_code == 302
    with client.application.app_context():
        category = Category(nama="Belanja", jenis="keluar", is_system=False, is_active=True)
        db.session.add(category)
        db.session.commit()
        cid = category.id
    resp = client.post("/expenses", data={"amount": "25000", "keterangan": "Beli sapu", "category_id": str(cid), "csrf_token": client_csrf(client)}, follow_redirects=False)
    assert resp.status_code == 302
    with client.application.app_context():
        trx = Transaction.query.filter_by(jenis="pengeluaran").order_by(Transaction.id.desc()).first()
        assert trx is not None
        assert trx.jumlah == 25000


def test_period_lock_blocks_void(client, superuser, app):
    assert client.post(
        "/login",
        data={"username": "admin", "password": "supersecret1", "csrf_token": client_csrf(client)},
        follow_redirects=False,
    ).status_code == 302
    resp = client.post("/periods/lock", data={"period": "2026-11", "csrf_token": client_csrf(client)}, follow_redirects=False)
    assert resp.status_code == 302
    with app.app_context():
        house = _make_house(app)
        dues_type = _make_dues_type(app)
        inv = Invoice(house_id=house.id, dues_type_id=dues_type.id, period="2026-11", nominal=50000, paid_amount=0, status="belum")
        db.session.add(inv)
        db.session.commit()
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
        trx_id = trx.id
    resp = client.post(f"/payments/{trx_id}/void", data={"void_reason": "x", "csrf_token": client_csrf(client)}, follow_redirects=False)
    assert resp.status_code == 400


def test_warga_page(client, warga):
    assert client.post(
        "/login",
        data={"username": "warga", "password": "supersecret1", "csrf_token": client_csrf(client)},
        follow_redirects=False,
    ).status_code == 302
    resp = client.get("/warga")
    assert resp.status_code == 200


def test_rekap_page(client, superuser):
    assert client.post(
        "/login",
        data={"username": "admin", "password": "supersecret1", "csrf_token": client_csrf(client)},
        follow_redirects=False,
    ).status_code == 302
    resp = client.get("/rekap?bulan=2026-11")
    assert resp.status_code == 200
