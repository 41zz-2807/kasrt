from app import db
from app.models.audit import AuditLog
from app.models.finance import Transaction
from app.models.notification import NotificationOutbox
from app.services import export_service, finance_service, notification_service


def test_outbox_process_sends(client, superuser, app, monkeypatch):
    sent = []

    def fake_send(to_email, subject, body):
        sent.append((to_email, subject, body))

    monkeypatch.setattr(notification_service, "_send", fake_send)
    with app.app_context():
        row = notification_service.create_outbox(to_email="ketua@kasrt.local", subject="Notif", body="Halo")
        notification_service.process_outbox()
        outbox = db.session.get(NotificationOutbox, row.id)
        assert outbox.status == "sent"
        assert len(sent) == 1


def test_export_rekap_excel_and_pdf(app):
    with app.app_context():
        assert len(export_service.export_rekap_excel("2026-11")) > 0
        assert len(export_service.export_rekap_pdf("2026-11")) > 0


def test_audit_log_written_on_payment(client, superuser, app):
    with app.app_context():
        from app.models.master import DuesType, DuesRate, House

        house = House(blok="B", nomor="12", nama_penghuni="Budi", is_active=True, start_period=None)
        db.session.add(house)
        db.session.commit()
        dues_type = DuesType(nama="Iuran", is_active=True)
        db.session.add(dues_type)
        db.session.commit()
        db.session.add(DuesRate(dues_type_id=dues_type.id, nominal=50000, effective_period="2026-01", created_by=1))
        db.session.commit()

        before_count = db.session.query(AuditLog).count()
        finance_service.create_payment(
            house_id=house.id,
            dues_type_id=dues_type.id,
            amount=50000,
            keterangan="Bayar 50 rb",
            created_by=1,
            category_id=None,
            bulan_list=[],
            kelebihan="B",
        )
        after_count = db.session.query(AuditLog).count()
        assert after_count == before_count + 1
        trx = Transaction.query.filter_by(jenis="iuran").order_by(Transaction.id.desc()).first()
        assert trx is not None
        assert trx.jumlah == 50000
