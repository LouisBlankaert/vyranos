import os
import re
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from ..models import User, Business, Reservation, Lead
from .. import db


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

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
    nb_actifs = sum(1 for u in users if u.is_active)
    nb_domaines = sum(1 for u in users if u.business and u.business.custom_domain)
    leads = Lead.query.order_by(Lead.created_at.desc()).all()
    nb_leads_nouveaux = sum(1 for l in leads if not l.lu)

    return render_template('admin/index.html',
        users=users,
        total_reservations=total_reservations,
        nb_actifs=nb_actifs,
        nb_domaines=nb_domaines,
        leads=leads,
        nb_leads_nouveaux=nb_leads_nouveaux,
    )


@admin_bp.route('/admin/lead/<int:lead_id>/lu', methods=['POST'])
@admin_required
def mark_lead_lu(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    lead.lu = True
    db.session.commit()
    return redirect(url_for('admin.index') + '#leads')


@admin_bp.route('/admin/lead/<int:lead_id>/convertir', methods=['POST'])
@admin_required
def convertir_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')

    if not email or not password:
        flash('Email et mot de passe requis.', 'error')
        return redirect(url_for('admin.index') + '#leads')

    if len(password) < 8:
        flash('Le mot de passe doit faire au moins 8 caractères.', 'error')
        return redirect(url_for('admin.index') + '#leads')

    if User.query.filter_by(email=email).first():
        flash('Cet email est déjà utilisé par un autre compte.', 'error')
        return redirect(url_for('admin.index') + '#leads')

    slug = slugify(lead.nom_commerce)
    base_slug = slug
    counter = 1
    while User.query.filter_by(slug=slug).first():
        slug = f'{base_slug}-{counter}'
        counter += 1

    user = User(email=email, slug=slug)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    business = Business(user_id=user.id, nom=lead.nom_commerce)
    db.session.add(business)

    lead.converti = True
    lead.lu = True
    db.session.commit()

    flash(f'Compte créé pour {lead.prenom} {lead.nom} — {lead.nom_commerce}. Slug : /{slug}', 'success')
    return redirect(url_for('admin.index') + '#leads')


@admin_bp.route('/admin/lead/<int:lead_id>/supprimer', methods=['POST'])
@admin_required
def delete_lead(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    db.session.delete(lead)
    db.session.commit()
    flash('Lead supprimé.', 'success')
    return redirect(url_for('admin.index') + '#leads')


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
