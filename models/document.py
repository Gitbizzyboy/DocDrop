from models import db
from datetime import datetime, timezone


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)       # stored filename (UUID-based)
    original_filename = db.Column(db.String(255), nullable=False)  # what the client named it
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))
    document_type = db.Column(db.String(100))  # bank statement, receipt, invoice, etc.
    uploaded_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    downloaded_by_bookkeeper = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Document {self.original_filename}>"
