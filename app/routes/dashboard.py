from datetime import datetime

from flask import Blueprint, render_template
from flask_login import current_user

from app.services import finance_service
from app.utils import staff_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@staff_required
def dashboard():
    now = datetime.now()
    period = f"{now.year:04d}-{now.month:02d}"
    pemasukan, pengeluaran = finance_service.rekap_bulanan(period)
    return render_template(
        "dashboard.html",
        user=current_user,
        saldo_kas=finance_service.saldo_kas(),
        pemasukan_bulan=pemasukan,
        pengeluaran_bulan=pengeluaran,
        open_unpaid=finance_service.open_unpaid_houses(),
        chart=finance_service.rekap_6_bulan(),
        period=period,
    )
