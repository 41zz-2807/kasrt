from datetime import date

from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.extensions import db
from app.models.finance import Invoice, Transaction
from app.models.master import House
from app.utils import staff_required, write_required

houses_bp = Blueprint("houses", __name__)


def _render(error=None, edit=None):
    houses = House.query.order_by(House.blok, House.nomor).all()
    return render_template("houses.html", houses=houses, error=error, edit=edit)


@houses_bp.route("/houses", methods=["GET"])
@staff_required
def houses():
    return _render()


@houses_bp.route("/houses", methods=["POST"])
@write_required
def houses_create():
    blok = request.form.get("blok", "").strip()
    nomor = request.form.get("nomor", "").strip()
    nama = request.form.get("nama_penghuni", "").strip()
    is_active = request.form.get("is_active") is not None
    start_period = None
    start_period_raw = request.form.get("start_period") or None
    if start_period_raw:
        try:
            start_period = date.fromisoformat(start_period_raw)
        except ValueError:
            start_period = None

    if not blok or not nomor or not nama:
        return _render(error="Blok, nomor rumah, dan nama penghuni wajib diisi.")
    if House.query.filter_by(blok=blok, nomor=nomor).first() is not None:
        return _render(error="Rumah dengan blok/nomor ini sudah ada.")

    db.session.add(House(blok=blok, nomor=nomor, nama_penghuni=nama, is_active=is_active, start_period=start_period))
    db.session.commit()
    return redirect(url_for("houses.houses"))


@houses_bp.route("/houses/<int:id>/edit", methods=["GET", "POST"])
@write_required
def houses_edit(id):
    house = db.session.get(House, id)
    if house is None:
        abort(404)
    if request.method == "GET":
        return _render(edit=house)

    blok = request.form.get("blok", "").strip()
    nomor = request.form.get("nomor", "").strip()
    nama = request.form.get("nama_penghuni", "").strip()
    if not blok or not nomor or not nama:
        return _render(error="Blok, nomor rumah, dan nama penghuni wajib diisi.", edit=house)

    duplicate = House.query.filter_by(blok=blok, nomor=nomor).first()
    if duplicate is not None and duplicate.id != id:
        return _render(error="Rumah dengan blok/nomor ini sudah ada.", edit=house)

    start_period_raw = request.form.get("start_period") or None
    start_period = None
    if start_period_raw:
        try:
            start_period = date.fromisoformat(start_period_raw)
        except ValueError:
            return _render(error="Format tanggal mulai tidak valid.", edit=house)

    house.blok = blok
    house.nomor = nomor
    house.nama_penghuni = nama
    house.is_active = request.form.get("is_active") is not None
    house.start_period = start_period
    db.session.commit()
    return redirect(url_for("houses.houses"))


@houses_bp.route("/houses/<int:id>/delete", methods=["POST"])
@write_required
def houses_delete(id):
    house = db.session.get(House, id)
    if house is None:
        abort(404)
    if Transaction.query.filter_by(house_id=id).first() is not None or Invoice.query.filter_by(house_id=id).first() is not None:
        return "Rumah sudah digunakan transaksi/tagihan dan tidak bisa dihapus.", 400
    db.session.delete(house)
    db.session.commit()
    return redirect(url_for("houses.houses"))
