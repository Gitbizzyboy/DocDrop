import os
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

from models import db
from models.user import User
from models.client import Client  # noqa: F401 — ensure models are registered
from models.document import Document  # noqa: F401


def create_app():
    app = Flask(__name__)

    # ── Config ────────────────────────────────────────────────────────────────
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///docdrop_dev.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    upload_folder = os.environ.get("UPLOAD_FOLDER", "static/uploads")
    app.config["UPLOAD_FOLDER"] = upload_folder
    app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_UPLOAD_MB", 25)) * 1024 * 1024
    app.config["MAX_UPLOAD_MB"] = int(os.environ.get("MAX_UPLOAD_MB", 25))

    app.config["STRIPE_SECRET_KEY"] = os.environ.get("STRIPE_SECRET_KEY", "")
    app.config["STRIPE_PUBLISHABLE_KEY"] = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    app.config["STRIPE_WEBHOOK_SECRET"] = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    app.config["STRIPE_MONTHLY_PRICE_ID"] = os.environ.get("STRIPE_MONTHLY_PRICE_ID", "")
    app.config["BASE_URL"] = os.environ.get("BASE_URL", "http://localhost:5000")

    # Fix postgres:// → postgresql:// for SQLAlchemy 2.x
    db_url = app.config["SQLALCHEMY_DATABASE_URI"]
    if db_url.startswith("postgres://"):
        app.config["SQLALCHEMY_DATABASE_URI"] = db_url.replace("postgres://", "postgresql://", 1)

    # ── Extensions ────────────────────────────────────────────────────────────
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access your dashboard."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Upload folder ─────────────────────────────────────────────────────────
    os.makedirs(upload_folder, exist_ok=True)

    # ── Blueprints ────────────────────────────────────────────────────────────
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.clients import clients_bp
    from routes.portal import portal_bp
    from routes.stripe_webhook import stripe_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(stripe_bp)

    # ── Landing / misc routes ─────────────────────────────────────────────────
    from flask import request as flask_request
    from services.stripe_service import create_checkout_session
    from flask_login import current_user, login_required

    @app.route("/")
    def landing():
        return render_template("landing.html")

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    @app.route("/upgrade")
    @login_required
    def upgrade():
        try:
            checkout_url = create_checkout_session(current_user.email, current_user.id)
            return redirect(checkout_url)
        except Exception as e:
            app.logger.error(f"Stripe checkout error: {e}")
            from flask import flash
            flash("Could not start checkout. Please try again or contact support.", "danger")
            return redirect(url_for("dashboard.index"))

    @app.route("/billing")
    @login_required
    def billing():
        if not current_user.stripe_customer_id:
            return redirect(url_for("upgrade"))
        try:
            from services.stripe_service import create_customer_portal_session
            portal_url = create_customer_portal_session(current_user.stripe_customer_id)
            return redirect(portal_url)
        except Exception as e:
            app.logger.error(f"Billing portal error: {e}")
            from flask import flash
            flash("Could not open billing portal. Please try again.", "danger")
            return redirect(url_for("dashboard.index"))

    # ── Error handlers ────────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        from flask import flash, redirect, request as req
        flash(f"File too large. Maximum size is {app.config['MAX_UPLOAD_MB']}MB.", "danger")
        return redirect(req.referrer or url_for("landing"))

    # ── DB init ───────────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()

    # Make landing accessible from blueprints via url_for("main.landing") aliases
    app.add_url_rule("/", endpoint="main.landing", view_func=app.view_functions["landing"])

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
