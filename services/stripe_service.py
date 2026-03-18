import stripe
from flask import current_app


def get_stripe():
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]
    return stripe


def create_checkout_session(user_email: str, user_id: int) -> str:
    """
    Create a Stripe Checkout session for the $39/mo subscription.
    Returns the checkout URL.
    """
    s = get_stripe()
    base_url = current_app.config["BASE_URL"]

    session = s.checkout.Session.create(
        payment_method_types=["card"],
        mode="subscription",
        line_items=[
            {
                "price": current_app.config["STRIPE_MONTHLY_PRICE_ID"],
                "quantity": 1,
            }
        ],
        customer_email=user_email,
        metadata={"user_id": str(user_id)},
        success_url=f"{base_url}/dashboard?upgraded=1",
        cancel_url=f"{base_url}/dashboard?cancelled=1",
    )
    return session.url


def create_customer_portal_session(stripe_customer_id: str) -> str:
    """Return URL to Stripe billing portal for subscription management."""
    s = get_stripe()
    base_url = current_app.config["BASE_URL"]

    session = s.billing_portal.Session.create(
        customer=stripe_customer_id,
        return_url=f"{base_url}/dashboard",
    )
    return session.url


def handle_webhook(payload: bytes, sig_header: str) -> dict | None:
    """
    Validate and parse a Stripe webhook event.
    Returns the event dict or None if validation fails.
    """
    s = get_stripe()
    webhook_secret = current_app.config["STRIPE_WEBHOOK_SECRET"]

    try:
        event = s.Webhook.construct_event(payload, sig_header, webhook_secret)
        return event
    except (ValueError, stripe.error.SignatureVerificationError):
        return None
