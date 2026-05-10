import os
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, abort
from ..models import User, Reservation
from .. import db

admin_bp = Blueprint('admin', __name__)

ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', '')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if email == ADMIN_EMAIL.lower() and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session.permanent = True
            return redirect(url_for('admin.index'))
        flash('Identifiants incorrects.', 'error')

    return render_template('admin/login.html')


@admin_bp.route('/admin/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.login'))


@admin_bp.route('/admin')
@admin_required
def index():
    users = User.query.order_by(User.created_at.desc()).all()
    now = datetime.now(timezone.utc)

    total_reservations = Reservation.query.count()
    actifs = [u for u in users if u.subscription and u.subscription.statut == 'active']
    en_trial = [u for u in users if u.trial_ends_at and u.trial_ends_at.replace(tzinfo=timezone.utc) > now and not (u.subscription and u.subscription.statut == 'active')]
    inactifs = [u for u in users if not u.is_active]
    mrr_base = len(actifs) * 69
    nb_domaines = sum(1 for u in users if u.business and u.business.custom_domain)
    mrr = mrr_base + nb_domaines * 10

    return render_template('admin/index.html',
        users=users,
        total_reservations=total_reservations,
        nb_actifs=len(actifs),
        nb_trial=len(en_trial),
        nb_domaines=nb_domaines,
        mrr=mrr,
    )


@admin_bp.route('/admin/client/<int:user_id>')
@admin_required
def client(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    reservations = (
        Reservation.query
        .filter_by(business_id=user.business.id)
        .order_by(Reservation.date.desc(), Reservation.creneau.desc())
        .all()
    ) if user.business else []
    return render_template('admin/client.html', client=user, reservations=reservations)


@admin_bp.route('/admin/client/<int:user_id>/domaine', methods=['POST'])
@admin_required
def set_domaine(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    if not user.business:
        flash('Ce client n\'a pas encore de commerce configuré.', 'error')
        return redirect(url_for('admin.client', user_id=user_id))
    raw = request.form.get('custom_domain', '').strip().lower()
    domain = raw.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
    if domain:
        from ..models import Business
        existing = Business.query.filter(Business.custom_domain == domain, Business.id != user.business.id).first()
        if existing:
            flash('Ce domaine est déjà utilisé par un autre client.', 'error')
        else:
            user.business.custom_domain = domain
            db.session.commit()
            flash(f'Domaine {domain} activé pour {user.business.nom}.', 'success')
    else:
        user.business.custom_domain = None
        db.session.commit()
        flash('Domaine retiré.', 'success')
    return redirect(url_for('admin.client', user_id=user_id))


@admin_bp.route('/admin/client/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_client(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    user.is_active = not user.is_active
    db.session.commit()
    status = 'réactivé' if user.is_active else 'suspendu'
    flash(f'Compte {status} avec succès.', 'success')
    return redirect(url_for('admin.client', user_id=user_id))
