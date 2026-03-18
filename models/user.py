from flask_login import UserMixin
from models import db
from datetime import datetime, timezone


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    business_name = db.Column(db.String(255))
    stripe_customer_id = db.Column(db.String(255))
    plan = db.Column(db.String(20), default="free")
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    clients = db.relationship("Client", backref="owner", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"
