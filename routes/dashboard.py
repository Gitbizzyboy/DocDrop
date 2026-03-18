import io
import os
import zipfile
from flask import (
    Blueprint, render_template, redirect, url_for,
    request, flash, send_file, abort, current_app
)
from flask_login import login_required, current_user
from models import db
from models.client import Client
from models.document import Document
from services.storage import get_file_path

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    clients = (
        Client.query
        .filter_by(user_id=current_user.id)
        .order_by(Client.created_at.desc())
        .all()
    )
    # Attach new doc counts
    for c in clients:
        c._new_docs = sum(1 for d in c.documents if not d.downloaded_by_bookkeeper)

    recent_docs = (
        Document.query
        .join(Client)
        .filter(Client.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .limit(10)
        .all()
    )

    upgraded = request.args.get("upgraded")
    cancelled = request.args.get("cancelled")

    return render_template(
        "dashboard/index.html",
        clients=clients,
        recent_docs=recent_docs,
        upgraded=upgraded,
        cancelled=cancelled,
    )


@dashboard_bp.route("/client/<int:client_id>")
@login_required
def client_view(client_id):
    client = Client.query.filter_by(id=client_id, user_id=current_user.id).first_or_404()
    documents = (
        Document.query
        .filter_by(client_id=client_id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    base_url = current_app.config.get("BASE_URL", request.host_url.rstrip("/"))
    portal_url = f"{base_url}/upload/{client.portal_token}"

    return render_template(
        "dashboard/client.html",
        client=client,
        documents=documents,
        portal_url=portal_url,
    )


@dashboard_bp.route("/document/<int:doc_id>/download")
@login_required
def download_document(doc_id):
    doc = (
        Document.query
        .join(Client)
        .filter(Document.id == doc_id, Client.user_id == current_user.id)
        .first_or_404()
    )

    filepath = get_file_path(doc.filename)
    if not os.path.exists(filepath):
        abort(404)

    # Mark as downloaded
    doc.downloaded_by_bookkeeper = True
    db.session.commit()

    return send_file(
        filepath,
        as_attachment=True,
        download_name=doc.original_filename,
        mimetype=doc.mime_type or "application/octet-stream",
    )


@dashboard_bp.route("/client/<int:client_id>/download-all")
@login_required
def download_all(client_id):
    client = Client.query.filter_by(id=client_id, user_id=current_user.id).first_or_404()
    documents = Document.query.filter_by(client_id=client_id).all()

    if not documents:
        flash("No documents to download.", "warning")
        return redirect(url_for("dashboard.client_view", client_id=client_id))

    # Build in-memory ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for doc in documents:
            filepath = get_file_path(doc.filename)
            if os.path.exists(filepath):
                zf.write(filepath, doc.original_filename)
                doc.downloaded_by_bookkeeper = True

    db.session.commit()
    zip_buffer.seek(0)

    safe_name = client.name.replace(" ", "_").lower()
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name=f"{safe_name}_documents.zip",
        mimetype="application/zip",
    )


@dashboard_bp.route("/document/<int:doc_id>/mark-reviewed", methods=["POST"])
@login_required
def mark_reviewed(doc_id):
    doc = (
        Document.query
        .join(Client)
        .filter(Document.id == doc_id, Client.user_id == current_user.id)
        .first_or_404()
    )
    doc.downloaded_by_bookkeeper = True
    db.session.commit()
    return redirect(request.referrer or url_for("dashboard.index"))


@dashboard_bp.route("/document/<int:doc_id>/delete", methods=["POST"])
@login_required
def delete_document(doc_id):
    doc = (
        Document.query
        .join(Client)
        .filter(Document.id == doc_id, Client.user_id == current_user.id)
        .first_or_404()
    )
    from services.storage import delete_file
    delete_file(doc.filename)
    db.session.delete(doc)
    db.session.commit()
    flash("Document deleted.", "success")
    return redirect(request.referrer or url_for("dashboard.index"))
