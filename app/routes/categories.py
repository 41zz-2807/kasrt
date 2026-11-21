from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.extensions import db
from app.models.master import Category
from app.utils import staff_required, write_required

categories_bp = Blueprint("categories", __name__)


def _render(error=None, edit=None, form=None):
    return render_template(
        "categories.html",
        categories=Category.query.order_by(Category.id).all(),
        error=error,
        category_form=form,
        edit=edit,
    )


@categories_bp.route("/categories", methods=["GET"])
@staff_required
def categories():
    return _render()


@categories_bp.route("/categories", methods=["POST"])
@write_required
def categories_create():
    nama = request.form.get("nama", "").strip()
    jenis = request.form.get("jenis", "masuk") or "masuk"
    is_active = request.form.get("is_active") is not None
    form = {"nama": nama, "jenis": jenis, "is_active": is_active}

    if not nama:
        return _render(error="Nama kategori wajib diisi.", form=form)
    if Category.query.filter_by(nama=nama).first() is not None:
        return _render(error="Kategori sudah ada.", form=form)

    db.session.add(Category(nama=nama, jenis=jenis, is_system=False, is_active=is_active))
    db.session.commit()
    return redirect(url_for("categories.categories"))


@categories_bp.route("/categories/<int:id>/edit", methods=["GET", "POST"])
@write_required
def categories_edit(id):
    category = db.session.get(Category, id)
    if category is None:
        abort(404)
    if category.is_system:
        return "Kategori sistem tidak boleh diubah.", 400
    if request.method == "GET":
        return _render(edit=category)

    nama = request.form.get("nama", "").strip()
    jenis = request.form.get("jenis", "masuk") or "masuk"
    if not nama:
        return _render(error="Nama kategori wajib diisi.", edit=category)
    duplicate = Category.query.filter_by(nama=nama).first()
    if duplicate is not None and duplicate.id != id:
        return _render(error="Kategori sudah ada.", edit=category)

    category.nama = nama
    category.jenis = jenis
    category.is_active = request.form.get("is_active") is not None
    db.session.commit()
    return redirect(url_for("categories.categories"))


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
