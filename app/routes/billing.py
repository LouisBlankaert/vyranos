import os
import stripe
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from ..models import Subscription
from .. import db

billing_bp = Blueprint('billing', __name__)

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')


@billing_bp.route('/')
@login_required
def index():
    return render_template('billing/index.html')


@billing_bp.route('/checkout')
@login_required
def checkout():
    if current_user.is_subscribed():
        return redirect(url_for('dashboard.index'))

    price_id = os.environ.get('STRIPE_PRICE_ID')
    if not price_id or 'your_price_id' in price_id:
        flash('Abonnement non configuré (clés Stripe manquantes). Accès accordé en mode test.', 'warning')
        return redirect(url_for('dashboard.index'))

    try:
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(email=current_user.email)
            current_user.stripe_customer_id = customer.id
            db.session.commit()

        session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            mode='subscription',
            line_items=[{'price': price_id, 'quantity': 1}],
            success_url=url_for('billing.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('billing.index', _external=True),
            metadata={'user_id': current_user.id},
        )
        return redirect(session.url)
    except stripe.error.StripeError as e:
        flash(f'Erreur Stripe : {e.user_message}', 'error')
        return redirect(url_for('billing.index'))


@billing_bp.route('/success')
@login_required
def success():
    flash('Abonnement activé ! Bienvenue sur Vyranos.', 'success')
    return redirect(url_for('dashboard.index'))


@billing_bp.route('/portal')
@login_required
def portal():
    if not current_user.stripe_customer_id:
        flash('Aucun abonnement trouvé.', 'error')
        return redirect(url_for('billing.index'))

    try:
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=url_for('billing.index', _external=True),
        )
        return redirect(session.url)
    except stripe.error.StripeError as e:
        flash(f'Erreur : {e.user_message}', 'error')
        return redirect(url_for('billing.index'))


@billing_bp.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data()
    sig = request.headers.get('Stripe-Signature')
    secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

    try:
        event = stripe.Webhook.construct_event(payload, sig, secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return '', 400

    data = event['data']['object']

    if event['type'] == 'customer.subscription.created':
        _upsert_subscription(data, 'active')
    elif event['type'] == 'customer.subscription.updated':
        _upsert_subscription(data, data['status'])
    elif event['type'] == 'customer.subscription.deleted':
        _upsert_subscription(data, 'canceled')

    return '', 200


def _upsert_subscription(data, statut):
    from ..models import User
    user = User.query.filter_by(stripe_customer_id=data['customer']).first()
    if not user:
        return
    sub = user.subscription or Subscription(user_id=user.id)
    sub.stripe_subscription_id = data['id']
    sub.statut = statut
    end = data.get('current_period_end')
    if end:
        sub.current_period_end = datetime.fromtimestamp(end, tz=timezone.utc)
    if not user.subscription:
        db.session.add(sub)
    db.session.commit()
