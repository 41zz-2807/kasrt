from datetime import datetime

from flask import Blueprint, render_template

from app.extensions import db
from app.models.finance import Invoice, Transaction
from app.services import finance_service

warga_bp = Blueprint("warga", __name__)


@warga_bp.route("/warga")
def warga():
    now = datetime.now()
    period = f"{now.year:04d}-{now.month:02d}"
    pemasukan, pengeluaran = finance_service.rekap_bulanan(period)
    transactions = Transaction.query.filter_by(status="aktif").order_by(Transaction.id.desc()).all()
    open_invoices = db.session.query(Invoice).filter(Invoice.status.in_(["belum", "sebagian"])).order_by(Invoice.period).all()
    return render_template(
        "warga.html",
        saldo_kas=finance_service.saldo_kas(),
        pemasukan=pemasukan,
        pengeluaran=pengeluaran,
        period=period,
        transactions=transactions,
        open_invoices=open_invoices,
        error=None,
    )
