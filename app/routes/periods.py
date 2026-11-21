from datetime import datetime

from flask import Blueprint, redirect, render_template, request, url_for

from app.extensions import db
from app.models.finance import PeriodLock
from app.utils import superuser_required

periods_bp = Blueprint("periods", __name__)


@periods_bp.route("/periods")
@superuser_required
def periods():
    locks = PeriodLock.query.order_by(PeriodLock.period).all()
    return render_template("periods.html", locks=locks, error=None)


@periods_bp.route("/periods/lock", methods=["POST"])
@superuser_required
def period_lock():
    period = request.form.get("period") or ""
    if not period:
        return "Periode wajib diisi.", 400
    if PeriodLock.query.filter_by(period=period).first() is not None:
        return "Periode sudah terkunci.", 400
    db.session.add(PeriodLock(period=period, locked_by=1, locked_at=datetime.now().replace(microsecond=0)))
    db.session.commit()
    return redirect(url_for("periods.periods"))


@periods_bp.route("/periods/unlock", methods=["POST"])
@superuser_required
def period_unlock():
    period = request.form.get("period") or ""
    if not period:
        return "Periode wajib diisi.", 400
    lock = PeriodLock.query.filter_by(period=period).first()
    if lock is None:
        return "Periode tidak terkunci.", 400
    db.session.delete(lock)
    db.session.commit()
    return redirect(url_for("periods.periods"))
