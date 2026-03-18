from flask import (
    Blueprint, render_template, request, flash,
    redirect, url_for, jsonify, current_app
)
from models import db
from models.client import Client
from models.document import Document
from services.storage import save_file, allowed_file

portal_bp = Blueprint("portal", __name__)

DOCUMENT_TYPES = [
    ("bank_statement", "Bank Statement"),
    ("receipt", "Receipt"),
    ("invoice", "Invoice"),
    ("tax_form", "Tax Form"),
    ("payroll", "Payroll Record"),
    ("other", "Other"),
]


@portal_bp.route("/upload/<token>", methods=["GET"])
def upload_page(token):
    client = Client.query.filter_by(portal_token=token).first_or_404()
    return render_template(
        "portal/upload.html",
        client=client,
        business_name=client.owner.business_name or "Your Bookkeeper",
        document_types=DOCUMENT_TYPES,
        token=token,
    )


@portal_bp.route("/upload/<token>", methods=["POST"])
def upload_files(token):
    client = Client.query.filter_by(portal_token=token).first_or_404()

    files = request.files.getlist("files")
    doc_type = request.form.get("document_type", "other")

    if not files or all(f.filename == "" for f in files):
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "error": "No files selected."}), 400
        flash("Please select at least one file.", "danger")
        return redirect(url_for("portal.upload_page", token=token))

    max_mb = current_app.config.get("MAX_UPLOAD_MB", 25)
    max_bytes = max_mb * 1024 * 1024
    uploaded = []
    errors = []

    for file in files:
        if file.filename == "":
            continue

        if not allowed_file(file.filename):
            errors.append(f"{file.filename}: file type not allowed.")
            continue

        # Check size by reading content-length or seek
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)

        if size > max_bytes:
            errors.append(f"{file.filename}: exceeds {max_mb}MB limit.")
            continue

        try:
            meta = save_file(file, client.id)
            doc = Document(
                client_id=client.id,
                filename=meta["filename"],
                original_filename=meta["original_filename"],
                file_size=meta["file_size"],
                mime_type=meta["mime_type"],
                document_type=doc_type,
            )
            db.session.add(doc)
            uploaded.append(meta["original_filename"])
        except Exception as e:
            current_app.logger.error(f"Upload error for {file.filename}: {e}")
            errors.append(f"{file.filename}: upload failed.")

    if uploaded:
        db.session.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({
            "success": bool(uploaded),
            "uploaded": uploaded,
            "errors": errors,
        })

    if uploaded:
        flash(f"✓ {len(uploaded)} file(s) uploaded successfully. Thank you!", "success")
    if errors:
        for err in errors:
            flash(err, "danger")

    if uploaded and not errors:
        return render_template(
            "portal/upload.html",
            client=client,
            business_name=client.owner.business_name or "Your Bookkeeper",
            document_types=DOCUMENT_TYPES,
            token=token,
            success=True,
            uploaded_count=len(uploaded),
        )

    return redirect(url_for("portal.upload_page", token=token))
