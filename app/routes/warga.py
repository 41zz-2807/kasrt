from datetime import datetime

from flask import Blueprint, render_template, request

from app.extensions import db
from app.models.finance import Invoice, Transaction
from app.services import finance_service

warga_bp = Blueprint("warga", __name__)


@warga_bp.route("/warga")
def warga():
    now = datetime.now()
    period = f"{now.year:04d}-{now.month:02d}"
    pemasukan, pengeluaran = finance_service.rekap_bulanan(period)
    query = Transaction.query.filter_by(status="aktif").order_by(Transaction.id.desc())
    per_page = 10
    pages = max(1, (query.count() + per_page - 1) // per_page)
    page = min(max(request.args.get("page", 1, type=int) or 1, 1), pages)
    transactions = query.offset((page - 1) * per_page).limit(per_page).all()
    open_invoices = db.session.query(Invoice).filter(Invoice.status.in_(["belum", "sebagian"])).order_by(Invoice.period).all()
    return render_template(
        "warga.html",
        saldo_kas=finance_service.saldo_kas(),
        pemasukan=pemasukan,
        pengeluaran=pengeluaran,
        period=period,
        transactions=transactions,
        open_invoices=open_invoices,
        page=page,
        pages=pages,
        error=None,
    )
