from flask import Blueprint, jsonify


health_bp = Blueprint("health", __name__, url_prefix="")


@health_bp.route("/healthz")
def healthz():
    return jsonify(status="ok", service="kasrt"), 200
