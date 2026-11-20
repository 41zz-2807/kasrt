from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models.master import DuesRate, DuesType
from app.utils import staff_required, write_required

dues_bp = Blueprint("dues", __name__)


@dues_bp.route("/dues/types", methods=["GET"])
@staff_required
def dues_types():
    dues_types = DuesType.query.order_by(DuesType.id).all()
    return render_template("dues_types.html", dues_types=dues_types, error=None, dues_types_form=None)


@dues_bp.route("/dues/types", methods=["POST"])
@write_required
def dues_types_create():
    error = None
    nama = request.form.get("nama", "").strip()
    is_active = request.form.get("is_active") is not None
    if not nama:
        error = "Nama jenis iuran wajib diisi."
    elif DuesType.query.filter_by(nama=nama).first() is not None:
        error = "Jenis iuran sudah ada."
    else:
        db.session.add(DuesType(nama=nama, is_active=is_active))
        db.session.commit()
        return redirect(url_for("dues.dues_types"))

    dues_types = DuesType.query.order_by(DuesType.id).all()
    return render_template("dues_types.html", dues_types=dues_types, error=error, dues_types_form={"nama": nama, "is_active": is_active})


@dues_bp.route("/dues/rates", methods=["GET"])
@staff_required
def dues_rates():
    dues_types = DuesType.query.order_by(DuesType.id).all()
    rates = DuesRate.query.order_by(DuesRate.id).all()
    return render_template("dues_rates.html", dues_types=dues_types, rates=rates, error=None, rate_form=None)


@dues_bp.route("/dues/rates", methods=["POST"])
@write_required
def dues_rates_create():
    error = None
    dues_type_id = request.form.get("dues_type_id")
    nominal = request.form.get("nominal")
    effective_period = request.form.get("effective_period", "").strip()
    try:
        nominal_int = int(nominal or 0)
    except (TypeError, ValueError):
        nominal_int = 0
    if not dues_type_id or not effective_period or nominal_int <= 0:
        error = "Kategori iuran, nominal, dan periode wajib valid."
    elif DuesRate.query.filter_by(dues_type_id=int(dues_type_id), effective_period=effective_period).first() is not None:
        error = "Riwayat nominal untuk periode ini sudah ada."
    else:
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

    dues_types = DuesType.query.order_by(DuesType.id).all()
    rates = DuesRate.query.order_by(DuesRate.id).all()
    return render_template("dues_rates.html", dues_types=dues_types, rates=rates, error=error, rate_form={"dues_type_id": dues_type_id, "nominal": nominal, "effective_period": effective_period})
