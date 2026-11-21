from datetime import datetime

from flask import Blueprint, render_template, request

from app.services import finance_service

rekap_bp = Blueprint("rekap", __name__)


@rekap_bp.route("/rekap")
def rekap():
    period = request.args.get("bulan") or f"{datetime.now().year:04d}-{datetime.now().month:02d}"
    pemasukan, pengeluaran = finance_service.rekap_bulanan(period)
    return render_template("rekap.html", period=period, pemasukan=pemasukan, pengeluaran=pengeluaran, error=None)
