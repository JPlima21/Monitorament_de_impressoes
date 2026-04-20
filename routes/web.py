from flask import Blueprint, render_template


def create_web_blueprint():
    web_bp = Blueprint("web", __name__)

    @web_bp.route("/")
    def home():
        return render_template("index.html")

    return web_bp
