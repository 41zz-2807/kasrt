from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models.finance import PeriodLock, Transaction
from app.models.master import DuesType, House
from app.services import finance_service
from app.utils import staff_required, write_required

payments_bp = Blueprint("payments", __name__)


def _render(error=None, edit=None):
    return render_template(
        "payments.html",
        transactions=Transaction.query.order_by(Transaction.id.desc()).all(),
        houses=House.query.order_by(House.id).all(),
        dues_types=DuesType.query.order_by(DuesType.id).all(),
        error=error,
        edit=edit,
    )


def _is_locked(transaction):
    period = f"{transaction.tanggal.year:04d}-{transaction.tanggal.month:02d}"
    return PeriodLock.query.filter_by(period=period).first() is not None


@payments_bp.route("/payments")
@staff_required
def payments():
    return _render()


@payments_bp.route("/payments", methods=["POST"])
@write_required
def payments_create():
    house_id = int(request.form.get("house_id") or 0)
    dues_type_id = int(request.form.get("dues_type_id") or 0)
    amount = int(request.form.get("amount") or 0)
    keterangan = request.form.get("keterangan") or ""
    category_id = int(request.form.get("category_id") or 0) or None
    kelebihan = request.form.get("kelebihan") or "B"
    bulan_list = [b.strip() for b in (request.form.get("bulan") or "").split(",") if b.strip()]

    if house_id <= 0 or dues_type_id <= 0 or amount <= 0:
        return "Data tidak valid.", 400

    finance_service.create_payment(
        house_id=house_id,
        dues_type_id=dues_type_id,
        amount=amount,
        keterangan=keterangan,
        created_by=current_user.id,
        category_id=category_id,
        bulan_list=bulan_list,
        kelebihan=kelebihan,
    )
    return redirect(url_for("payments.payments"))


@payments_bp.route("/payments/<int:id>/edit", methods=["GET", "POST"])
@write_required
def payments_edit(id):
    trx = db.session.get(Transaction, id)
    if trx is None:
        abort(404)
    if trx.status != "aktif":
        return "Transaksi sudah dibatalkan.", 400
    if request.method == "GET":
        return _render(edit=trx)
    if _is_locked(trx):
        return "Periode transaksi sudah dikunci.", 400

    trx.keterangan = (request.form.get("keterangan") or "").strip()
    db.session.commit()
    return redirect(url_for("payments.payments"))


@payments_bp.route("/payments/<int:id>/void", methods=["POST"])
@write_required
def payments_void(id):
    ok = finance_service.void_transaction(id, user_id=current_user.id, reason=request.form.get("void_reason") or "")
    if not ok:
        return "Gagal membatalkan transaksi.", 400
    return redirect(url_for("payments.payments"))
