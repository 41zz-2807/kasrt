from datetime import date

from flask import Blueprint, redirect, render_template, request, url_for

from app.extensions import db
from app.models.master import House
from app.utils import staff_required, write_required

houses_bp = Blueprint("houses", __name__)


@houses_bp.route("/houses", methods=["GET"])
@staff_required
def houses():
    houses = House.query.order_by(House.blok, House.nomor).all()
    return render_template("houses.html", houses=houses, error=None)


@houses_bp.route("/houses", methods=["POST"])
@write_required
def houses_create():
    error = None
    blok = request.form.get("blok", "").strip()
    nomor = request.form.get("nomor", "").strip()
    nama = request.form.get("nama_penghuni", "").strip()
    is_active = request.form.get("is_active") is not None
    start_period_raw = request.form.get("start_period") or None
    start_period = None
    if start_period_raw:
        try:
            start_period = date.fromisoformat(start_period_raw)
        except ValueError:
            start_period = None

    if not blok or not nomor or not nama:
        error = "Blok, nomor rumah, dan nama penghuni wajib diisi."
    elif House.query.filter_by(blok=blok, nomor=nomor).first() is not None:
        error = "Rumah dengan blok/nomor ini sudah ada."
    else:
        db.session.add(
            House(
                blok=blok,
                nomor=nomor,
                nama_penghuni=nama,
                is_active=is_active,
                start_period=start_period,
            )
        )
        db.session.commit()
        return redirect(url_for("houses.houses"))

    houses = House.query.order_by(House.blok, House.nomor).all()
    return render_template("houses.html", houses=houses, error=error)
