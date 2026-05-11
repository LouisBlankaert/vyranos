import os
from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..models import Business, Service, Reservation, Blocage
from .. import db

dashboard_bp = Blueprint('dashboard', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
ALLOWED = {'png', 'jpg', 'jpeg', 'webp'}


def save_upload(file, prefix):
    if not file or file.filename == '':
        return None
    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED:
        return None
    filename = f'{prefix}_{current_user.id}.{ext}'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    return f'/static/uploads/{filename}'


@dashboard_bp.route('/')
@login_required
def index():
    business = current_user.business
    today = date.today()
    upcoming = (
        Reservation.query
        .filter_by(business_id=business.id, statut='confirmé')
        .filter(Reservation.date >= today)
        .order_by(Reservation.date, Reservation.creneau)
        .limit(10)
        .all()
    ) if business else []
    return render_template('dashboard/index.html', business=business, upcoming=upcoming)


@dashboard_bp.route('/business', methods=['GET', 'POST'])
@login_required
def business():
    b = current_user.business
    if request.method == 'POST':
        b.nom = request.form.get('nom', '').strip() or b.nom
        b.description = request.form.get('description', '').strip()
        b.adresse = request.form.get('adresse', '').strip()
        b.ville = request.form.get('ville', '').strip()
        b.telephone = request.form.get('telephone', '').strip()
        b.email_contact = request.form.get('email_contact', '').strip()
        b.instagram = request.form.get('instagram', '').strip()
        b.tiktok = request.form.get('tiktok', '').strip()
        b.couleur_primaire = request.form.get('couleur_primaire', '#1a1a1a')

        if request.form.get('supprimer_logo'):
            b.logo_url = None
        if request.form.get('supprimer_cover'):
            b.cover_url = None

        logo = request.files.get('logo')
        cover = request.files.get('cover')
        logo_url = save_upload(logo, 'logo')
        cover_url = save_upload(cover, 'cover')
        if logo_url:
            b.logo_url = logo_url
        if cover_url:
            b.cover_url = cover_url

        db.session.commit()
        flash('Informations mises à jour.', 'success')
    return render_template('dashboard/business.html', business=b)


@dashboard_bp.route('/services', methods=['GET', 'POST'])
@login_required
def services():
    business = current_user.business
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            nom = request.form.get('nom', '').strip()
            if nom:
                s = Service(
                    business_id=business.id,
                    nom=nom,
                    description=request.form.get('description', '').strip(),
                    duree_minutes=int(request.form.get('duree_minutes', 60)),
                    prix=float(request.form.get('prix', 0)),
                )
                db.session.add(s)
                db.session.commit()
                flash('Service ajouté.', 'success')

        elif action == 'delete':
            service_id = request.form.get('service_id')
            s = Service.query.filter_by(id=service_id, business_id=business.id).first()
            if s:
                db.session.delete(s)
                db.session.commit()
                flash('Service supprimé.', 'success')

        elif action == 'toggle':
            service_id = request.form.get('service_id')
            s = Service.query.filter_by(id=service_id, business_id=business.id).first()
            if s:
                s.actif = not s.actif
                db.session.commit()

    all_services = Service.query.filter_by(business_id=business.id).all()
    return render_template('dashboard/services.html', business=business, services=all_services)


@dashboard_bp.route('/reservations')
@login_required
def reservations():
    business = current_user.business
    statut = request.args.get('statut', '')
    q = Reservation.query.filter_by(business_id=business.id)
    if statut:
        q = q.filter_by(statut=statut)
    all_reservations = q.order_by(Reservation.date.asc(), Reservation.creneau.asc()).all()
    services = Service.query.filter_by(business_id=business.id, actif=True).all()
    blocages = Blocage.query.filter_by(business_id=business.id).order_by(Blocage.date, Blocage.debut).all()
    return render_template('dashboard/reservations.html',
        business=business, reservations=all_reservations,
        services=services, blocages=blocages)


@dashboard_bp.route('/reservations/<int:rid>/edit', methods=['POST'])
@login_required
def edit_reservation(rid):
    r = Reservation.query.filter_by(id=rid, business_id=current_user.business.id).first_or_404()
    r.prenom = request.form.get('prenom', r.prenom).strip()
    r.nom = request.form.get('nom', r.nom).strip()
    r.email = request.form.get('email', r.email).strip()
    r.telephone = request.form.get('telephone', r.telephone or '').strip()
    r.statut = request.form.get('statut', r.statut)
    try:
        r.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
    except (ValueError, TypeError):
        pass
    r.creneau = request.form.get('creneau', r.creneau)
    service_id = request.form.get('service_id', type=int)
    if service_id:
        r.service_id = service_id
    db.session.commit()
    flash('Réservation mise à jour.', 'success')
    return redirect(url_for('dashboard.reservations'))


@dashboard_bp.route('/reservations/<int:rid>/delete', methods=['POST'])
@login_required
def delete_reservation(rid):
    r = Reservation.query.filter_by(id=rid, business_id=current_user.business.id).first_or_404()
    db.session.delete(r)
    db.session.commit()
    flash('Réservation supprimée.', 'success')
    return redirect(url_for('dashboard.reservations'))


@dashboard_bp.route('/reservations/<int:rid>/statut', methods=['POST'])
@login_required
def update_statut(rid):
    r = Reservation.query.filter_by(id=rid, business_id=current_user.business.id).first_or_404()
    r.statut = request.form.get('statut', r.statut)
    db.session.commit()
    return redirect(url_for('dashboard.reservations'))


@dashboard_bp.route('/blocages', methods=['POST'])
@login_required
def add_blocage():
    business = current_user.business
    try:
        d = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
    except (ValueError, TypeError):
        flash('Date invalide.', 'error')
        return redirect(url_for('dashboard.reservations'))
    b = Blocage(
        business_id=business.id,
        date=d,
        debut=request.form.get('debut', '12:00'),
        fin=request.form.get('fin', '14:00'),
        motif=request.form.get('motif', 'Indisponible').strip() or 'Indisponible',
    )
    db.session.add(b)
    db.session.commit()
    flash('Pause ajoutée.', 'success')
    return redirect(url_for('dashboard.reservations'))


@dashboard_bp.route('/blocages/<int:bid>/delete', methods=['POST'])
@login_required
def delete_blocage(bid):
    b = Blocage.query.filter_by(id=bid, business_id=current_user.business.id).first_or_404()
    db.session.delete(b)
    db.session.commit()
    flash('Pause supprimée.', 'success')
    return redirect(url_for('dashboard.reservations'))


@dashboard_bp.route('/domaine', methods=['GET', 'POST'])
@login_required
def domaine():
    b = current_user.business
    if request.method == 'POST':
        raw = request.form.get('custom_domain', '').strip().lower()
        domain = raw.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
        if domain:
            existing = Business.query.filter(Business.custom_domain == domain, Business.id != b.id).first()
            if existing:
                flash('Ce domaine est déjà utilisé par un autre compte.', 'error')
            else:
                b.custom_domain = domain
                db.session.commit()
                flash('Domaine enregistré. Pensez à configurer votre CNAME.', 'success')
        else:
            b.custom_domain = None
            db.session.commit()
            flash('Domaine personnalisé retiré.', 'success')
    return render_template('dashboard/domaine.html', business=b)


@dashboard_bp.route('/horaires', methods=['GET', 'POST'])
@login_required
def horaires():
    business = current_user.business
    jours = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']

    if request.method == 'POST':
        h = {}
        for jour in jours:
            ouvert = request.form.get(f'{jour}_ouvert') == 'on'
            h[jour] = {
                'ouvert': ouvert,
                'debut': request.form.get(f'{jour}_debut', '09:00'),
                'fin': request.form.get(f'{jour}_fin', '18:00'),
            }
        business.horaires = h
        step = request.form.get('creneau_step', 30, type=int)
        if step in [15, 30, 45, 60, 90]:
            business.creneau_step = step
        db.session.commit()
        flash('Horaires mis à jour.', 'success')

    return render_template('dashboard/horaires.html', business=business, jours=jours)
