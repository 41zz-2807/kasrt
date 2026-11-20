from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user

from app.models.finance import Transaction
from app.models.master import DuesType, House
from app.services import finance_service
from app.utils import staff_required, write_required

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/payments")
@staff_required
def payments():
    transactions = Transaction.query.order_by(Transaction.id.desc()).all()
    houses = House.query.order_by(House.id).all()
    dues_types = DuesType.query.order_by(DuesType.id).all()
    return render_template("payments.html", transactions=transactions, houses=houses, dues_types=dues_types, error=None)


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

    trx = finance_service.create_payment(
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


@payments_bp.route("/payments/<int:id>/void", methods=["POST"])
@write_required
def payments_void(id):
    ok, err = finance_service.void_transaction(id, user_id=current_user.id, reason=request.form.get("void_reason") or "")
    if not ok:
        return err or "Gagal membatalkan transaksi.", 400
    return redirect(url_for("payments.payments"))
