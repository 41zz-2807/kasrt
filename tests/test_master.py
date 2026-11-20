import hashlib
import os

from itsdangerous import URLSafeTimedSerializer

from app import db
from app.models.master import Category, DuesRate, DuesType, House, Setting


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


def test_create_house_success(client, superuser):
    assert login(client, "admin", "supersecret1").status_code == 302
    resp = client.post(
        "/houses",
        data={"blok": "B", "nomor": "12", "nama_penghuni": "Budi", "is_active": "1", "csrf_token": csrf_token(client)},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    with client.application.app_context():
        assert House.query.filter_by(blok="B", nomor="12").count() == 1


def test_create_house_duplicate_rejected(client, superuser):
    assert login(client, "admin", "supersecret1").status_code == 302
    for expected in (302, 200):
        resp = client.post(
            "/houses",
            data={"blok": "B", "nomor": "12", "nama_penghuni": "Budi", "is_active": "1", "csrf_token": csrf_token(client)},
            follow_redirects=False,
        )
        assert resp.status_code == expected


def test_create_dues_type(client, superuser):
    assert login(client, "admin", "supersecret1").status_code == 302
    resp = client.post("/dues/types", data={"nama": "Kebersihan", "is_active": "1", "csrf_token": csrf_token(client)}, follow_redirects=False)
    assert resp.status_code == 302
    resp = client.get("/dues/types")
    assert resp.status_code == 200
    assert b"Kebersihan" in resp.data


def test_create_dues_rate(client, superuser):
    assert login(client, "admin", "supersecret1").status_code == 302
    with client.application.app_context():
        t = DuesType(nama="Keamanan", is_active=True)
        db.session.add(t)
        db.session.commit()
        tid = t.id
    resp = client.post(
        "/dues/rates",
        data={"dues_type_id": str(tid), "nominal": "50000", "effective_period": "2026-11", "csrf_token": csrf_token(client)},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    with client.application.app_context():
        assert DuesRate.query.count() == 1


def test_system_category_cannot_be_deleted(client, superuser):
    assert login(client, "admin", "supersecret1").status_code == 302
    with client.application.app_context():
        system = Category(nama="Sumbangan warga", jenis="masuk", is_system=True, is_active=True)
        db.session.add(system)
        db.session.commit()
        cid = system.id
    resp = client.post(f"/categories/{cid}/delete", data={"csrf_token": csrf_token(client)}, follow_redirects=False)
    assert resp.status_code == 400
    with client.application.app_context():
        assert db.session.get(Category, cid) is not None


def test_settings_save(client, superuser):
    assert login(client, "admin", "supersecret1").status_code == 302
    resp = client.post(
        "/settings",
        data={
            "nama_rt": "RT 05",
            "saldo_awal_kas": "150000",
            "email_ketua_rt": "ketua@kasrt.local",
            "email_bendahara": "bendahara@kasrt.local",
            "tampilkan_nama_penghuni": "1",
            "csrf_token": csrf_token(client),
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    resp = client.get("/settings")
    assert resp.status_code == 200
    with client.application.app_context():
        assert Setting.query.filter_by(key="nama_rt").first().value == "RT 05"


def test_warga_cannot_write_master(client, warga):
    assert login(client, "warga", "supersecret1").status_code == 302
    resp = client.post(
        "/houses",
        data={"blok": "B", "nomor": "12", "nama_penghuni": "Budi", "is_active": "1", "csrf_token": csrf_token(client)},
        follow_redirects=False,
    )
    assert resp.status_code == 403
