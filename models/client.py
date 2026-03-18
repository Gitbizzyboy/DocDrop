from models import db
from datetime import datetime, timezone
import secrets


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    company = db.Column(db.String(255))
    portal_token = db.Column(db.String(64), unique=True, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    documents = db.relationship("Document", backref="client", lazy=True, cascade="all, delete-orphan")

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(48)

    @property
    def new_doc_count(self):
        return sum(1 for d in self.documents if not d.downloaded_by_bookkeeper)

    def __repr__(self):
        return f"<Client {self.name}>"
