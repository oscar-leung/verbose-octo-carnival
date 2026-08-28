"""Stripe integration — subscription checkout + webhook handling.

Disabled when STRIPE_SECRET_KEY is unset (paywall off; free tier is unlimited).
Tie billing events to unlock keys in store.py via checkout.session.completed
and customer.subscription.deleted.
"""

from __future__ import annotations

import os
import secrets
from typing import Optional

import stripe

import store


def _key() -> Optional[str]:
    return os.environ.get("STRIPE_SECRET_KEY")


def is_enabled() -> bool:
    return bool(_key() and os.environ.get("STRIPE_PRICE_ID"))


def _init() -> None:
    key = _key()
    if not key:
        raise RuntimeError("Stripe is not configured (STRIPE_SECRET_KEY missing).")
    stripe.api_key = key


def create_checkout_session(success_url: str, cancel_url: str) -> str:
    """Returns the Checkout URL to redirect the user to."""
    _init()
    price_id = os.environ["STRIPE_PRICE_ID"]
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
        cancel_url=cancel_url,
        allow_promotion_codes=True,
    )
    return session.url


def verify_and_get_session(session_id: str) -> Optional[dict]:
    """Called after Stripe redirects back — verifies the session is paid."""
    _init()
    session = stripe.checkout.Session.retrieve(session_id)
    if session.payment_status != "paid":
        return None
    return {
        "id": session.id,
        "customer_id": session.customer,
        "subscription_id": session.subscription,
        "email": (session.customer_details or {}).get("email") or "",
    }


def handle_webhook(payload: bytes, sig_header: str) -> None:
    """Verify signature, dispatch event. Raises on invalid signature."""
    _init()
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET not set.")

    event = stripe.Webhook.construct_event(payload, sig_header, secret)
    event_type = event["type"]
    obj = event["data"]["object"]

    if event_type == "checkout.session.completed":
        if obj.get("payment_status") != "paid" or obj.get("mode") != "subscription":
            return
        key = secrets.token_urlsafe(32)
        store.upsert_key(
            key=key,
            email=(obj.get("customer_details") or {}).get("email") or "",
            customer_id=obj.get("customer"),
            subscription_id=obj.get("subscription"),
            checkout_session_id=obj.get("id"),
        )
    elif event_type == "customer.subscription.deleted":
        subscription_id = obj.get("id")
        if subscription_id:
            store.deactivate_by_subscription(subscription_id)


def issue_key_for_session(session_id: str) -> Optional[str]:
    """Used by the /unlocked redirect page when the webhook may not have fired yet.

    Idempotent: if the webhook already created a key for this session, returns it.
    Otherwise verifies the checkout session with Stripe and creates one.
    """
    existing = store.find_by_checkout_session(session_id)
    if existing:
        return existing["key"]

    session = verify_and_get_session(session_id)
    if not session:
        return None

    key = secrets.token_urlsafe(32)
    store.upsert_key(
        key=key,
        email=session["email"],
        customer_id=session["customer_id"],
        subscription_id=session["subscription_id"],
        checkout_session_id=session["id"],
    )
    # Re-fetch in case of a race with the webhook
    row = store.find_by_checkout_session(session_id)
    return row["key"] if row else key
