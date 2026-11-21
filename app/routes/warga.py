from datetime import datetime

from flask import Blueprint, render_template

from app.extensions import db
from app.models.finance import Invoice, Transaction
from app.services import finance_service
from app.utils import paginate_query

warga_bp = Blueprint("warga", __name__)


@warga_bp.route("/warga")
def warga():
    now = datetime.now()
    period = f"{now.year:04d}-{now.month:02d}"
    pemasukan, pengeluaran = finance_service.rekap_bulanan(period)
    transactions, page, pages = paginate_query(
        Transaction.query.filter_by(status="aktif").order_by(Transaction.id.desc())
    )
    open_invoices, invoice_page, invoice_pages = paginate_query(
        db.session.query(Invoice)
        .filter(Invoice.status.in_(["belum", "sebagian"]))
        .order_by(Invoice.period),
        param="invoice_page",
    )
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
        invoice_page=invoice_page,
        invoice_pages=invoice_pages,
        error=None,
    )
