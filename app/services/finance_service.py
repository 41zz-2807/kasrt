from datetime import datetime, timezone
from uuid import uuid4

from app.extensions import db
from app.models.master import Category, DuesRate, DuesType, House, Setting
from app.models.finance import Invoice, PeriodLock, PaymentAllocation, Transaction

OPEN_STATUSES = ("belum", "sebagian")
ACTIVE_STATUS = "aktif"
TRX_KIND_DUE = "iuran"


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _trx_no() -> str:
    return f"TRX-{uuid4().hex[:10].upper()}"


def _receipt_no() -> str:
    return f"KW-{uuid4().hex[:8].upper()}"


def _period_of(dt: datetime) -> str:
    return f"{dt.year:04d}-{dt.month:02d}"


def rate_nominal(dues_type_id: int, period: str) -> int:
    rates = DuesRate.query.filter_by(dues_type_id=dues_type_id).order_by(DuesRate.effective_period.desc()).all()
    chosen = None
    for r in rates:
        if r.effective_period <= period:
            chosen = r
    return chosen.nominal if chosen is not None else 0


def generate_invoices(period: str, created_by: int) -> int:
    """Create missing invoices for period (YYYY-MM) for active houses. Idempotent."""
    created = 0
    houses = House.query.filter_by(is_active=True).all()
    types = DuesType.query.filter_by(is_active=True).all()
    for house in houses:
        for dues_type in types:
            if Invoice.query.filter_by(house_id=house.id, dues_type_id=dues_type.id, period=period).first() is not None:
                continue
            db.session.add(
                Invoice(
                    house_id=house.id,
                    dues_type_id=dues_type.id,
                    period=period,
                    nominal=rate_nominal(dues_type.id, period),
                    paid_amount=0,
                    status="belum",
                )
            )
            created += 1
    db.session.commit()
    return created


def pay_invoices(house_id: int, dues_type_id: int, amount: int, transaction_id: int):
    """Allocate amount across open invoices of house+type, oldest period first.

    Returns leftover amount (surplus).
    """
    leftover = amount
    invoices = (
        db.session.query(Invoice)
        .filter(Invoice.house_id == house_id, Invoice.dues_type_id == dues_type_id, Invoice.status.in_(OPEN_STATUSES))
        .order_by(Invoice.period)
        .all()
    )
    for inv in invoices:
        if leftover <= 0:
            break
        open_amount = inv.nominal - inv.paid_amount
        alloc = min(open_amount, leftover)
        inv.paid_amount += alloc
        leftover -= alloc
        inv.status = "lunas" if inv.paid_amount >= inv.nominal else "sebagian"
        db.session.add(PaymentAllocation(transaction_id=transaction_id, invoice_id=inv.id, amount=alloc))
    db.session.commit()
    return leftover


def _next_period(period: str) -> str:
    year, month = int(period[:4]), int(period[5:7])
    month += 1
    if month > 12:
        year, month = year + 1, 1
    return f"{year:04d}-{month:02d}"


def create_pengeluaran(amount: int, keterangan: str, created_by: int, category_id: int = None, house_id: int = None) -> Transaction:
    trx = Transaction(
        trx_no=_trx_no(),
        tanggal=_now(),
        jenis="pengeluaran",
        category_id=category_id,
        house_id=house_id,
        jumlah=amount,
        keterangan=keterangan or "Pengeluaran",
        status="aktif",
        receipt_no=None,
        created_by=created_by,
    )
    db.session.add(trx)
    db.session.commit()
    return trx


def create_payment(
    house_id: int,
    dues_type_id: int,
    amount: int,
    keterangan: str,
    created_by: int,
    category_id: int = None,
    bulan_list=None,
    kelebihan: str = "B",
) -> Transaction:
    trx = Transaction(
        trx_no=_trx_no(),
        tanggal=_now(),
        jenis=TRX_KIND_DUE,
        category_id=category_id,
        house_id=house_id,
        jumlah=amount,
        keterangan=keterangan or "Pembayaran iuran",
        status="aktif",
        receipt_no=_receipt_no(),
        created_by=created_by,
    )
    db.session.add(trx)
    db.session.commit()

    leftover = amount
    bulan_list = list(bulan_list or [])
    if bulan_list:
        for period in bulan_list:
            generate_invoices(period, created_by)
            inv = (
                Invoice.query.filter_by(house_id=house_id, dues_type_id=dues_type_id, period=period)
                .order_by(Invoice.id)
                .first()
            )
            if inv is not None and inv.status in OPEN_STATUSES:
                leftover -= pay_invoices(house_id=house_id, dues_type_id=dues_type_id, amount=inv.nominal, transaction_id=trx.id)
    else:
        leftover = pay_invoices(house_id=house_id, dues_type_id=dues_type_id, amount=amount, transaction_id=trx.id)

    if leftover > 0 and kelebihan:
        if kelebihan == "A":
            open_inv = (
                Invoice.query.filter_by(house_id=house_id, dues_type_id=dues_type_id, status__in=list(OPEN_STATUSES))
                .order_by(Invoice.period)
                .first()
            )
            if open_inv is not None:
                next_period = _next_period(open_inv.period)
                generate_invoices(next_period, created_by)
                inv = (
                    Invoice.query.filter_by(house_id=house_id, dues_type_id=dues_type_id, period=next_period)
                    .order_by(Invoice.id)
                    .first()
                )
                if inv is not None and inv.status in OPEN_STATUSES:
                    pay_invoices(house_id=house_id, dues_type_id=dues_type_id, amount=leftover, transaction_id=trx.id)
                    leftover = 0
        if leftover > 0:
            system_category = Category.query.filter_by(nama="Sumbangan warga", is_system=True).first()
            db.session.add(
                Transaction(
                    trx_no=_trx_no(),
                    tanggal=_now(),
                    jenis="non_rutin",
                    category_id=system_category.id if system_category is not None else None,
                    house_id=house_id,
                    jumlah=leftover,
                    keterangan=keterangan or "Kelebihan pembayaran iuran",
                    status="aktif",
                    receipt_no=_receipt_no(),
                    created_by=created_by,
                )
            )
            db.session.commit()
    return trx


def void_transaction(transaction_id: int, user_id: int, reason: str) -> bool:
    trx = db.session.get(Transaction, transaction_id)
    if trx is None:
        return False
    if trx.status != ACTIVE_STATUS:
        return False
    if PeriodLock.query.filter_by(period=_period_of(trx.tanggal)).first() is not None:
        return False
    trx.status = "void"
    trx.void_reason = reason
    trx.voided_by = user_id
    trx.voided_at = _now()
    allocations = PaymentAllocation.query.filter_by(transaction_id=trx.id).all()
    for alloc in allocations:
        inv = db.session.get(Invoice, alloc.invoice_id)
        if inv is not None:
            inv.paid_amount = max(0, inv.paid_amount - alloc.amount)
            if inv.paid_amount >= inv.nominal:
                inv.status = "lunas"
            elif inv.paid_amount > 0:
                inv.status = "sebagian"
            else:
                inv.status = "belum"
        db.session.delete(alloc)
    db.session.commit()
    return True


def saldo_kas() -> int:
    awal = 0
    setting = Setting.query.filter_by(key="saldo_awal_kas").first()
    if setting is not None:
        try:
            awal = int(setting.value or 0)
        except (TypeError, ValueError):
            awal = 0
    aktif = [t for t in Transaction.query.filter(Transaction.status == ACTIVE_STATUS).all() if t.jenis in ("iuran", "non_rutin")]
    keluar = [t for t in Transaction.query.filter(Transaction.status == ACTIVE_STATUS).all() if t.jenis == "pengeluaran"]
    masuk = sum(t.jumlah for t in aktif)
    pengeluaran = sum(t.jumlah for t in keluar)
    return awal + masuk - pengeluaran


def open_unpaid_houses() -> int:
    rows = db.session.query(Invoice.house_id).filter(Invoice.status.in_(OPEN_STATUSES)).distinct().all()
    return len(rows)


def rekap_bulanan(period: str):
    """Return (pemasukan, pengeluaran) aktif for period 'YYYY-MM'."""
    start = f"{period}-01"
    end = f"{period}-32"
    pemasukan = 0
    pengeluaran = 0
    for t in db.session.query(Transaction).filter(Transaction.status == ACTIVE_STATUS).all():
        if not (start <= t.tanggal.strftime("%Y-%m-%d") <= end):
            continue
        if t.jenis in ("iuran", "non_rutin"):
            pemasukan += t.jumlah
        elif t.jenis == "pengeluaran":
            pengeluaran += t.jumlah
    return pemasukan, pengeluaran


def rekap_6_bulan():
    result = []
    now = datetime.now()
    year, month = now.year, now.month
    for _ in range(5, -1, -1):
        period = f"{year:04d}-{month:02d}"
        pemasukan, pengeluaran = rekap_bulanan(period)
        result.append((period, pemasukan, pengeluaran))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return result
