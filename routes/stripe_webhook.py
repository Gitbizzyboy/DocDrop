from flask import Blueprint, request, jsonify, current_app
from models import db
from models.user import User
from services.stripe_service import handle_webhook

stripe_bp = Blueprint("stripe", __name__)


@stripe_bp.route("/stripe/webhook", methods=["POST"])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")

    event = handle_webhook(payload, sig_header)
    if event is None:
        current_app.logger.warning("Invalid Stripe webhook signature")
        return jsonify({"error": "Invalid signature"}), 400

    event_type = event.get("type")
    current_app.logger.info(f"Stripe event: {event_type}")

    if event_type == "checkout.session.completed":
        session_obj = event["data"]["object"]
        user_id = session_obj.get("metadata", {}).get("user_id")
        stripe_customer_id = session_obj.get("customer")

        if user_id:
            user = User.query.get(int(user_id))
            if user:
                user.plan = "pro"
                user.stripe_customer_id = stripe_customer_id
                db.session.commit()
                current_app.logger.info(f"User {user.email} upgraded to pro")

    elif event_type in ("customer.subscription.deleted", "customer.subscription.paused"):
        sub = event["data"]["object"]
        stripe_customer_id = sub.get("customer")
        if stripe_customer_id:
            user = User.query.filter_by(stripe_customer_id=stripe_customer_id).first()
            if user:
                user.plan = "free"
                db.session.commit()
                current_app.logger.info(f"User {user.email} downgraded to free")

    elif event_type == "customer.subscription.updated":
        sub = event["data"]["object"]
        stripe_customer_id = sub.get("customer")
        status = sub.get("status")
        if stripe_customer_id:
            user = User.query.filter_by(stripe_customer_id=stripe_customer_id).first()
            if user:
                if status == "active":
                    user.plan = "pro"
                elif status in ("canceled", "unpaid", "past_due"):
                    user.plan = "free"
                db.session.commit()

    elif event_type == "invoice.payment_failed":
        invoice = event["data"]["object"]
        stripe_customer_id = invoice.get("customer")
        current_app.logger.warning(f"Payment failed for customer {stripe_customer_id}")

    return jsonify({"status": "ok"}), 200
