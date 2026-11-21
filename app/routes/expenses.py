from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user

from app.models.finance import Transaction
from app.models.master import Category
from app.services import finance_service
from app.utils import paginate_query, staff_required, write_required

expenses_bp = Blueprint("expenses", __name__)


@expenses_bp.route("/expenses")
@staff_required
def expenses():
    categories = Category.query.filter_by(jenis="keluar").order_by(Category.id).all()
    transactions, page, pages = paginate_query(
        Transaction.query.filter_by(jenis="pengeluaran", status="aktif").order_by(Transaction.id.desc())
    )
    return render_template(
        "expenses.html", categories=categories, transactions=transactions,
        page=page, pages=pages, error=None,
    )


@expenses_bp.route("/expenses", methods=["POST"])
@write_required
def expenses_create():
    amount = int(request.form.get("amount") or 0)
    keterangan = request.form.get("keterangan") or ""
    category_id = int(request.form.get("category_id") or 0) or None
    house_id = int(request.form.get("house_id") or 0) or None
    if amount <= 0:
        return "Data tidak valid.", 400
    finance_service.create_pengeluaran(
        amount=amount, keterangan=keterangan, created_by=current_user.id, category_id=category_id, house_id=house_id
    )
    return redirect(url_for("expenses.expenses"))
