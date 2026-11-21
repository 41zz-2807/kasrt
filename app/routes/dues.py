from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models.finance import Invoice
from app.models.master import DuesRate, DuesType
from app.utils import staff_required, write_required

dues_bp = Blueprint("dues", __name__)


def _render_types(error=None, edit=None):
    return render_template(
        "dues_types.html",
        dues_types=DuesType.query.order_by(DuesType.id).all(),
        error=error,
        edit=edit,
    )


def _render_rates(error=None, edit=None):
    return render_template(
        "dues_rates.html",
        dues_types=DuesType.query.order_by(DuesType.id).all(),
        rates=DuesRate.query.order_by(DuesRate.id).all(),
        error=error,
        edit=edit,
    )


@dues_bp.route("/dues/types", methods=["GET"])
@staff_required
def dues_types():
    return _render_types()


@dues_bp.route("/dues/types", methods=["POST"])
@write_required
def dues_types_create():
    nama = request.form.get("nama", "").strip()
    is_active = request.form.get("is_active") is not None
    if not nama:
        return _render_types(error="Nama jenis iuran wajib diisi.")
    if DuesType.query.filter_by(nama=nama).first() is not None:
        return _render_types(error="Jenis iuran sudah ada.")

    db.session.add(DuesType(nama=nama, is_active=is_active))
    db.session.commit()
    return redirect(url_for("dues.dues_types"))


@dues_bp.route("/dues/types/<int:id>/edit", methods=["GET", "POST"])
@write_required
def dues_types_edit(id):
    dues_type = db.session.get(DuesType, id)
    if dues_type is None:
        abort(404)
    if request.method == "GET":
        return _render_types(edit=dues_type)

    nama = request.form.get("nama", "").strip()
    if not nama:
        return _render_types(error="Nama jenis iuran wajib diisi.", edit=dues_type)
    duplicate = DuesType.query.filter_by(nama=nama).first()
    if duplicate is not None and duplicate.id != id:
        return _render_types(error="Jenis iuran sudah ada.", edit=dues_type)

    dues_type.nama = nama
    dues_type.is_active = request.form.get("is_active") is not None
    db.session.commit()
    return redirect(url_for("dues.dues_types"))


@dues_bp.route("/dues/types/<int:id>/delete", methods=["POST"])
@write_required
def dues_types_delete(id):
    dues_type = db.session.get(DuesType, id)
    if dues_type is None:
        abort(404)
    if DuesRate.query.filter_by(dues_type_id=id).first() is not None or Invoice.query.filter_by(dues_type_id=id).first() is not None:
        return "Jenis iuran sudah digunakan tagihan/nominal dan tidak bisa dihapus.", 400
    db.session.delete(dues_type)
    db.session.commit()
    return redirect(url_for("dues.dues_types"))


@dues_bp.route("/dues/rates", methods=["GET"])
@staff_required
def dues_rates():
    return _render_rates()


@dues_bp.route("/dues/rates", methods=["POST"])
@write_required
def dues_rates_create():
    dues_type_id = request.form.get("dues_type_id")
    nominal = request.form.get("nominal")
    effective_period = request.form.get("effective_period", "").strip()
    try:
        nominal_int = int(nominal or 0)
    except (TypeError, ValueError):
        nominal_int = 0
    if not dues_type_id or not effective_period or nominal_int <= 0:
        return _render_rates(error="Kategori iuran, nominal, dan periode wajib valid.")
    if DuesRate.query.filter_by(dues_type_id=int(dues_type_id), effective_period=effective_period).first() is not None:
        return _render_rates(error="Riwayat nominal untuk periode ini sudah ada.")

    db.session.add(
        DuesRate(
            dues_type_id=int(dues_type_id),
            nominal=nominal_int,
            effective_period=effective_period,
            created_by=current_user.id,
        )
    )
    db.session.commit()
    return redirect(url_for("dues.dues_rates"))


@dues_bp.route("/dues/rates/<int:id>/edit", methods=["GET", "POST"])
@write_required
def dues_rates_edit(id):
    rate = db.session.get(DuesRate, id)
    if rate is None:
        abort(404)
    if request.method == "GET":
        return _render_rates(edit=rate)

    dues_type_id = request.form.get("dues_type_id")
    effective_period = request.form.get("effective_period", "").strip()
    try:
        nominal_int = int(request.form.get("nominal") or 0)
    except (TypeError, ValueError):
        nominal_int = 0
    if not dues_type_id or not effective_period or nominal_int <= 0:
        return _render_rates(error="Kategori iuran, nominal, dan periode wajib valid.", edit=rate)
    duplicate = DuesRate.query.filter_by(dues_type_id=int(dues_type_id), effective_period=effective_period).first()
    if duplicate is not None and duplicate.id != id:
        return _render_rates(error="Riwayat nominal untuk periode ini sudah ada.", edit=rate)

    rate.dues_type_id = int(dues_type_id)
    rate.nominal = nominal_int
    rate.effective_period = effective_period
    db.session.commit()
    return redirect(url_for("dues.dues_rates"))


@dues_bp.route("/dues/rates/<int:id>/delete", methods=["POST"])
@write_required
def dues_rates_delete(id):
    rate = db.session.get(DuesRate, id)
    if rate is None:
        abort(404)
    db.session.delete(rate)
    db.session.commit()
    return redirect(url_for("dues.dues_rates"))
