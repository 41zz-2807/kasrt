from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.extensions import db
from app.models.master import Category
from app.utils import staff_required, write_required

categories_bp = Blueprint("categories", __name__)


@categories_bp.route("/categories", methods=["GET"])
@staff_required
def categories():
    categories = Category.query.order_by(Category.id).all()
    return render_template("categories.html", categories=categories, error=None, category_form=None)


@categories_bp.route("/categories", methods=["POST"])
@write_required
def categories_create():
    error = None
    nama = request.form.get("nama", "").strip()
    jenis = request.form.get("jenis", "masuk") or "masuk"
    is_active = request.form.get("is_active") is not None
    if not nama:
        error = "Nama kategori wajib diisi."
    elif Category.query.filter_by(nama=nama).first() is not None:
        error = "Kategori sudah ada."
    else:
        db.session.add(Category(nama=nama, jenis=jenis, is_system=False, is_active=is_active))
        db.session.commit()
        return redirect(url_for("categories.categories"))

    categories = Category.query.order_by(Category.id).all()
    return render_template("categories.html", categories=categories, error=error, category_form={"nama": nama, "jenis": jenis, "is_active": is_active})


@categories_bp.route("/categories/<int:id>/delete", methods=["POST"])
@write_required
def categories_delete(id):
    category = db.session.get(Category, id)
    if category is None:
        abort(404)
    if category.is_system:
        return "Kategori sistem tidak boleh dihapus.", 400
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for("categories.categories"))
