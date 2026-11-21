from datetime import datetime

from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.extensions import db
from app.models.finance import PeriodLock
from app.utils import paginate_query, superuser_required

periods_bp = Blueprint("periods", __name__)


def _render(error=None, edit=None):
    locks, page, pages = paginate_query(PeriodLock.query.order_by(PeriodLock.period))
    return render_template("periods.html", locks=locks, page=page, pages=pages, error=error, edit=edit)


@periods_bp.route("/periods")
@superuser_required
def periods():
    return _render()


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


@periods_bp.route("/periods/<int:id>/edit", methods=["GET", "POST"])
@superuser_required
def period_edit(id):
    lock = db.session.get(PeriodLock, id)
    if lock is None:
        abort(404)
    if request.method == "GET":
        return _render(edit=lock)

    period = request.form.get("period") or ""
    if not period:
        return _render(error="Periode wajib diisi.", edit=lock)
    duplicate = PeriodLock.query.filter_by(period=period).first()
    if duplicate is not None and duplicate.id != id:
        return _render(error="Periode sudah terkunci.", edit=lock)

    lock.period = period
    db.session.commit()
    return redirect(url_for("periods.periods"))


@periods_bp.route("/periods/<int:id>/delete", methods=["POST"])
@superuser_required
def period_delete(id):
    lock = db.session.get(PeriodLock, id)
    if lock is None:
        abort(404)
    db.session.delete(lock)
    db.session.commit()
    return redirect(url_for("periods.periods"))
