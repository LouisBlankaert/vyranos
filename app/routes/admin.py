import os
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
    total_reservations = Reservation.query.count()
    return render_template('admin/index.html', users=users, total_reservations=total_reservations)


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
