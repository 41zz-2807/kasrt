from datetime import datetime

from itsdangerous import URLSafeTimedSerializer

from app import db
from app.models.finance import PeriodLock, Transaction
from app.models.master import Category, DuesRate, DuesType, House
from app.models.user import User


def _csrf(client):
    value = "crud-test-token"
    with client.session_transaction() as sess:
        sess["csrf_token"] = value
    return URLSafeTimedSerializer(client.application.secret_key, salt="wtf-csrf-token").dumps(value)


def _login(client, token):
    resp = client.post(
        "/login",
        data={"username": "admin", "password": "supersecret1", "csrf_token": token},
    )
    assert resp.status_code == 302


def test_house_edit_and_delete_guard(client, superuser):
    token = _csrf(client)
    _login(client, token)
    with client.application.app_context():
        house = House(blok="A", nomor="1", nama_penghuni="Budi", is_active=True)
        db.session.add(house)
        db.session.commit()
        hid = house.id

    resp = client.post(
        f"/houses/{hid}/edit",
        data={"blok": "B", "nomor": "2", "nama_penghuni": "Budi U", "is_active": "1", "csrf_token": token},
    )
    assert resp.status_code == 302
    with client.application.app_context():
        house = db.session.get(House, hid)
        assert (house.blok, house.nomor, house.nama_penghuni) == ("B", "2", "Budi U")

    with client.application.app_context():
        trx = Transaction(
            trx_no="TRX-CRUD-1", tanggal=datetime(2026, 11, 1), jenis="iuran",
            jumlah=1000, keterangan="", created_by=1, house_id=hid,
        )
        db.session.add(trx)
        db.session.commit()
        trx_id = trx.id

    assert client.post(f"/houses/{hid}/delete", data={"csrf_token": token}).status_code == 400
    with client.application.app_context():
        db.session.delete(db.session.get(Transaction, trx_id))
        db.session.commit()
    assert client.post(f"/houses/{hid}/delete", data={"csrf_token": token}).status_code == 302
    with client.application.app_context():
        assert db.session.get(House, hid) is None


def test_dues_type_edit_and_delete_guard(client, superuser):
    token = _csrf(client)
    _login(client, token)
    with client.application.app_context():
        dues_type = DuesType(nama="Iuran", is_active=True)
        db.session.add(dues_type)
        db.session.commit()
        tid = dues_type.id

    assert client.post(
        f"/dues/types/{tid}/edit",
        data={"nama": "Iuran Baru", "is_active": "1", "csrf_token": token},
    ).status_code == 302
    with client.application.app_context():
        assert db.session.get(DuesType, tid).nama == "Iuran Baru"

    with client.application.app_context():
        db.session.add(DuesRate(dues_type_id=tid, nominal=50000, effective_period="2026-01", created_by=1))
        db.session.commit()
    assert client.post(f"/dues/types/{tid}/delete", data={"csrf_token": token}).status_code == 400
    with client.application.app_context():
        rate = DuesRate.query.filter_by(dues_type_id=tid).first()
        db.session.delete(rate)
        db.session.commit()
        rate_id = rate.id
    assert client.post(f"/dues/types/{tid}/delete", data={"csrf_token": token}).status_code == 302


def test_dues_rate_edit_and_delete(client, superuser):
    token = _csrf(client)
    _login(client, token)
    with client.application.app_context():
        db.session.add(DuesType(nama="Iuran", is_active=True))
        db.session.commit()
        tid = DuesType.query.first().id
        rate = DuesRate(dues_type_id=tid, nominal=50000, effective_period="2026-01", created_by=1)
        db.session.add(rate)
        db.session.commit()
        rid = rate.id

    assert client.post(
        f"/dues/rates/{rid}/edit",
        data={"dues_type_id": str(tid), "nominal": "75000", "effective_period": "2026-02", "csrf_token": token},
    ).status_code == 302
    with client.application.app_context():
        rate = db.session.get(DuesRate, rid)
        assert (rate.nominal, rate.effective_period) == (75000, "2026-02")

    bad = client.post(
        f"/dues/rates/{rid}/edit",
        data={"dues_type_id": str(tid), "nominal": "100", "effective_period": "2026-13", "csrf_token": token},
    )
    assert bad.status_code == 200
    assert "YYYY-MM" in bad.get_data(as_text=True)

    assert client.post(f"/dues/rates/{rid}/delete", data={"csrf_token": token}).status_code == 302
    with client.application.app_context():
        assert db.session.get(DuesRate, rid) is None


def test_category_edit_and_system_guard(client, superuser):
    token = _csrf(client)
    _login(client, token)
    with client.application.app_context():
        category = Category(nama="Listrik", jenis="keluar", is_system=False, is_active=True)
        system = Category(nama="Sistem", jenis="masuk", is_system=True, is_active=True)
        db.session.add_all([category, system])
        db.session.commit()
        cid, sid = category.id, system.id

    assert client.post(
        f"/categories/{cid}/edit",
        data={"nama": "Listrik RT", "jenis": "keluar", "is_active": "1", "csrf_token": token},
    ).status_code == 302
    with client.application.app_context():
        assert db.session.get(Category, cid).nama == "Listrik RT"
    assert client.get(f"/categories/{sid}/edit").status_code == 400
    assert client.post(f"/categories/{sid}/delete", data={"csrf_token": token}).status_code == 400
    assert client.post(f"/categories/{cid}/delete", data={"csrf_token": token}).status_code == 302


def test_user_edit_and_delete_guards(client, superuser):
    token = _csrf(client)
    _login(client, token)
    admin_id = 1
    with client.application.app_context():
        other = User(username="aziz", role="superuser", is_active=True, must_change_password=False)
        other.set_password("tanyamaryam")
        db.session.add(other)
        db.session.commit()
        oid = other.id

    assert client.post(
        f"/users/{oid}/edit",
        data={"username": "aziz2", "email": "", "role": "bendahara", "is_active": "1", "csrf_token": token},
    ).status_code == 302
    with client.application.app_context():
        other = db.session.get(User, oid)
        assert (other.username, other.role) == ("aziz2", "bendahara")

    assert client.post(f"/users/{admin_id}/delete", data={"csrf_token": token}).status_code == 400
    assert client.post(f"/users/{oid}/delete", data={"csrf_token": token}).status_code == 302
    with client.application.app_context():
        assert db.session.get(User, oid) is None


def test_period_edit_and_delete(client, superuser):
    token = _csrf(client)
    _login(client, token)
    assert client.post("/periods/lock", data={"period": "2026-11", "csrf_token": token}).status_code == 302
    with client.application.app_context():
        pid = PeriodLock.query.first().id

    assert client.post(
        f"/periods/{pid}/edit", data={"period": "2026-12", "csrf_token": token}
    ).status_code == 302
    with client.application.app_context():
        assert db.session.get(PeriodLock, pid).period == "2026-12"
    assert client.post(f"/periods/{pid}/delete", data={"csrf_token": token}).status_code == 302
    with client.application.app_context():
        assert db.session.get(PeriodLock, pid) is None


def test_transaction_edit_and_void(client, superuser):
    token = _csrf(client)
    _login(client, token)
    with client.application.app_context():
        trx = Transaction(
            trx_no="TRX-CRUD-2", tanggal=datetime(2026, 11, 1), jenis="pengeluaran",
            jumlah=25000, keterangan="Beli sapu", created_by=1,
        )
        db.session.add(trx)
        db.session.commit()
        tid = trx.id

    assert client.post(
        f"/payments/{tid}/edit", data={"keterangan": "Beli sapu dan ember", "csrf_token": token}
    ).status_code == 302
    with client.application.app_context():
        assert db.session.get(Transaction, tid).keterangan == "Beli sapu dan ember"
    assert client.post(
        f"/payments/{tid}/void", data={"void_reason": "salah input", "csrf_token": token}
    ).status_code == 302
    with client.application.app_context():
        assert db.session.get(Transaction, tid).status == "void"
    assert client.post(
        f"/payments/{tid}/edit", data={"keterangan": "x", "csrf_token": token}
    ).status_code == 400
