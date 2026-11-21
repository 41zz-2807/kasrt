from datetime import datetime

from app.extensions import db
from app.models import House, Invoice, Setting, Transaction, User
from scripts.clear_dummy import MARKER_KEY, clear_dummy_data
from scripts.seed_dummy import PASSWORD, seed_dummy_data


def test_seed_then_clear_keeps_real_data(app):
    with app.app_context():
        real_user = User(username="admin", password_hash="real", role="superuser", must_change_password=False)
        db.session.add(real_user)
        db.session.flush()
        real_house = House(
            blok="B3", nomor="07", nama_penghuni="Aziz", is_active=True,
            start_period=None,
        )
        db.session.add(real_house)
        db.session.flush()
        real_trx = Transaction(
            trx_no="REAL-1", tanggal=datetime(2026, 11, 21), jenis="iuran",
            jumlah=50000, keterangan="Pembayaran asli", status="aktif",
            created_by=real_user.id,
        )
        db.session.add(real_trx)
        db.session.commit()
        real_ids = (real_user.id, real_house.id, real_trx.id)

        result = seed_dummy_data()
        assert result["houses"] == 12
        assert User.query.filter(User.username.startswith("demo_")).count() == 5
        assert Invoice.query.count() > 0
        assert Setting.query.filter_by(key=MARKER_KEY).first() is not None
        assert db.session.get(User, real_ids[0]) is not None
        assert db.session.get(House, real_ids[1]) is not None
        assert db.session.get(Transaction, real_ids[2]) is not None
        assert User.query.filter_by(username="demo_admin").first().check_password(PASSWORD)

        clear_dummy_data()
        assert User.query.filter(User.username.startswith("demo_")).count() == 0
        assert House.query.filter_by(blok="DM").count() == 0
        assert Transaction.query.filter(Transaction.trx_no.startswith("DEMO-")).count() == 0
        assert Invoice.query.count() == 0
        assert Setting.query.filter_by(key=MARKER_KEY).first() is None
        assert db.session.get(User, real_ids[0]) is not None
        assert db.session.get(House, real_ids[1]) is not None
        assert db.session.get(Transaction, real_ids[2]) is not None


def test_warga_dashboard_has_no_menu_and_ten_transactions(app, client):
    with app.app_context():
        seed_dummy_data()
        warga_id = User.query.filter_by(username="demo_warga").first().id
    with client.session_transaction() as sess:
        sess["_user_id"] = str(warga_id)
        sess["_fresh"] = True

    body = client.get("/warga").get_data(as_text=True)
    assert 'id="sidebar"' not in body
    assert 'id="menu-toggle"' not in body
    assert "Dashboard Warga" in body
    assert body.count("[DEMO]") == 10
    assert "Halaman 1 dari" in body
    assert "Berikutnya" in body
