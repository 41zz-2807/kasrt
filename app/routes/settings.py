from flask import Blueprint, redirect, render_template, request, url_for

from app.extensions import db
from app.models.master import Setting
from app.utils import superuser_required

settings_bp = Blueprint("settings", __name__)

SETTING_KEYS = ("nama_rt", "saldo_awal_kas", "email_ketua_rt", "email_bendahara", "tampilkan_nama_penghuni")


@settings_bp.route("/settings", methods=["GET"])
@superuser_required
def settings():
    rows = {row.key: row.value for row in Setting.query.all()}
    form = {
        "nama_rt": rows.get("nama_rt", ""),
        "saldo_awal_kas": rows.get("saldo_awal_kas", ""),
        "email_ketua_rt": rows.get("email_ketua_rt", ""),
        "email_bendahara": rows.get("email_bendahara", ""),
        "tampilkan_nama_penghuni": rows.get("tampilkan_nama_penghuni", "0"),
    }
    return render_template("settings.html", settings=rows, form=form)


@settings_bp.route("/settings", methods=["POST"])
@superuser_required
def settings_save():
    values = {
        "nama_rt": request.form.get("nama_rt", "").strip(),
        "saldo_awal_kas": request.form.get("saldo_awal_kas", "").strip(),
        "email_ketua_rt": request.form.get("email_ketua_rt", "").strip(),
        "email_bendahara": request.form.get("email_bendahara", "").strip(),
        "tampilkan_nama_penghuni": "1" if request.form.get("tampilkan_nama_penghuni") else "0",
    }
    for key, value in values.items():
        row = Setting.query.filter_by(key=key).first()
        if row is None:
            row = Setting(key=key, value=value)
            db.session.add(row)
        row.value = value
    db.session.commit()
    return redirect(url_for("settings.settings"))
