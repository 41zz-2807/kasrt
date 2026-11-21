"""Hapus hanya data dummy. Data nyata (admin, rumah, transaksi) tidak disentuh."""

from app import create_app, db
from app.models import (
    AuditLog,
    Category,
    DuesRate,
    DuesType,
    House,
    Invoice,
    NotificationOutbox,
    PaymentAllocation,
    PeriodLock,
    Setting,
    Transaction,
    User,
)

MARKER_KEY = "dummy_seed"
USER_PREFIX = "demo_"
EMAIL_SUFFIX = "@demo.local"
NAME_MARKER = "(Demo)"
TRX_PREFIX = "DEMO-"
HOUSE_BLOK = "DM"


def _delete(model, ids):
    if ids:
        db.session.query(model).filter(model.id.in_(ids)).delete(synchronize_session=False)


def clear_dummy_data():
    user_ids = [u.id for u in User.query.all() if u.username.startswith(USER_PREFIX)]
    house_ids = [
        h.id for h in House.query.all()
        if h.blok == HOUSE_BLOK or NAME_MARKER in (h.nama_penghuni or "")
    ]
    type_ids = [d.id for d in DuesType.query.all() if NAME_MARKER in d.nama]
    category_ids = [c.id for c in Category.query.all() if NAME_MARKER in c.nama]
    trx_ids = [
        t.id for t in Transaction.query.all()
        if t.trx_no.startswith(TRX_PREFIX)
        or (t.keterangan or "").startswith("[DEMO]")
        or t.house_id in house_ids
        or t.created_by in user_ids
    ]
    invoice_ids = [
        i.id for i in Invoice.query.all()
        if i.house_id in house_ids or i.dues_type_id in type_ids
    ]
    lock_ids = [p.id for p in PeriodLock.query.all() if p.locked_by in user_ids]
    audit_ids = [a.id for a in AuditLog.query.all() if a.user_id in user_ids]
    note_ids = [
        n.id for n in NotificationOutbox.query.all()
        if (n.to_email or "").endswith(EMAIL_SUFFIX)
    ]
    rate_ids = [
        r.id for r in DuesRate.query.all()
        if r.dues_type_id in type_ids or r.created_by in user_ids
    ]

    # Setting yang dibuat seeder dicatat id-nya di marker, jadi pengaturan asli aman.
    marker = Setting.query.filter_by(key=MARKER_KEY).first()
    setting_ids = [marker.id] if marker else []
    if marker:
        setting_ids += [int(x) for x in (marker.value or "").split(",") if x.strip().isdigit()]

    if trx_ids or invoice_ids:
        db.session.query(PaymentAllocation).filter(
            (PaymentAllocation.transaction_id.in_(trx_ids))
            | (PaymentAllocation.invoice_id.in_(invoice_ids))
        ).delete(synchronize_session=False)

    _delete(Invoice, invoice_ids)
    _delete(Transaction, trx_ids)
    _delete(PeriodLock, lock_ids)
    _delete(AuditLog, audit_ids)
    _delete(NotificationOutbox, note_ids)
    _delete(DuesRate, rate_ids)
    _delete(DuesType, type_ids)
    _delete(Category, category_ids)
    _delete(House, house_ids)
    _delete(User, user_ids)
    _delete(Setting, setting_ids)
    db.session.commit()


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        clear_dummy_data()
    print("Data dummy dihapus. Data asli dipertahankan.")
