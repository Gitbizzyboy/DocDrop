from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, jsonify, current_app
)
from flask_login import login_required, current_user
from models import db
from models.client import Client

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")


@clients_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_client():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        company = request.form.get("company", "").strip()
        notes = request.form.get("notes", "").strip()

        if not name:
            flash("Client name is required.", "danger")
            return render_template("dashboard/add_client.html")

        client = Client(
            user_id=current_user.id,
            name=name,
            email=email or None,
            company=company or None,
            portal_token=Client.generate_token(),
            notes=notes or None,
        )
        db.session.add(client)
        db.session.commit()

        flash(f"Client '{name}' added! Their portal link is ready to share.", "success")
        return redirect(url_for("dashboard.client_view", client_id=client.id))

    return render_template("dashboard/add_client.html")


@clients_bp.route("/<int:client_id>/edit", methods=["GET", "POST"])
@login_required
def edit_client(client_id):
    client = Client.query.filter_by(id=client_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Client name is required.", "danger")
            return render_template("dashboard/add_client.html", client=client, editing=True)

        client.name = name
        client.email = request.form.get("email", "").strip() or None
        client.company = request.form.get("company", "").strip() or None
        client.notes = request.form.get("notes", "").strip() or None
        db.session.commit()

        flash("Client updated.", "success")
        return redirect(url_for("dashboard.client_view", client_id=client.id))

    return render_template("dashboard/add_client.html", client=client, editing=True)


@clients_bp.route("/<int:client_id>/delete", methods=["POST"])
@login_required
def delete_client(client_id):
    client = Client.query.filter_by(id=client_id, user_id=current_user.id).first_or_404()
    name = client.name
    db.session.delete(client)
    db.session.commit()
    flash(f"Client '{name}' and all their documents have been deleted.", "success")
    return redirect(url_for("dashboard.index"))


@clients_bp.route("/<int:client_id>/regenerate-token", methods=["POST"])
@login_required
def regenerate_token(client_id):
    client = Client.query.filter_by(id=client_id, user_id=current_user.id).first_or_404()
    client.portal_token = Client.generate_token()
    db.session.commit()
    flash("Portal link has been regenerated. The old link will no longer work.", "warning")
    return redirect(url_for("dashboard.client_view", client_id=client.id))


@clients_bp.route("/<int:client_id>/portal-url")
@login_required
def get_portal_url(client_id):
    """JSON endpoint — returns the portal URL for clipboard copy."""
    client = Client.query.filter_by(id=client_id, user_id=current_user.id).first_or_404()
    base_url = current_app.config.get("BASE_URL", request.host_url.rstrip("/"))
    portal_url = f"{base_url}/upload/{client.portal_token}"
    return jsonify({"url": portal_url})
