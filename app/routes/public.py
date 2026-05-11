from datetime import date, datetime, timedelta, time as dtime
from flask import Blueprint, render_template, redirect, url_for, request, flash
from ..models import User, Business, Service, Reservation, Blocage
from .. import db

public_bp = Blueprint('public', __name__)

def parse_time(s):
    h, m = map(int, s.split(':'))
    return h * 60 + m


def generate_creneaux(business, service, day):
    horaires = business.horaires or {}
    day_name = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche'][day.weekday()]
    jour = horaires.get(day_name, {})
    if not jour.get('ouvert', False):
        return []

    try:
        ouverture = parse_time(jour.get('debut', '09:00'))
        fermeture = parse_time(jour.get('fin', '18:00'))
    except ValueError:
        return []

    duree = service.duree_minutes

    reservations = Reservation.query.filter_by(
        business_id=business.id, date=day, statut='confirmé'
    ).all()

    blocages = Blocage.query.filter_by(business_id=business.id, date=day).all()

    def is_blocked(slot_start_min):
        slot_end_min = slot_start_min + duree
        for r in reservations:
            r_start = parse_time(r.creneau)
            r_end = r_start + r.service.duree_minutes
            if slot_start_min < r_end and slot_end_min > r_start:
                return True
        for b in blocages:
            b_start = parse_time(b.debut)
            b_end = parse_time(b.fin)
            if b_start <= slot_start_min < b_end:
                return True
        return False

    step = getattr(business, 'creneau_step', None) or 30

    creneaux = []
    current = ouverture
    while current + duree <= fermeture:
        h, m = divmod(current, 60)
        heure = f'{h:02d}:{m:02d}'
        creneaux.append({'heure': heure, 'disponible': not is_blocked(current)})
        current += step

    return creneaux


@public_bp.route('/<slug>')
def landing(slug):
    user = User.query.filter_by(slug=slug).first_or_404()
    business = user.business
    if not business:
        return render_template('public/404.html'), 404
    services = Service.query.filter_by(business_id=business.id, actif=True).all()
    return render_template(
        'public/landing.html',
        business=business,
        services=services,
        user=user,
    )


@public_bp.route('/<slug>/booking', methods=['GET', 'POST'])
def booking(slug):
    user = User.query.filter_by(slug=slug).first_or_404()
    business = user.business
    services = Service.query.filter_by(business_id=business.id, actif=True).all()

    selected_service_id = request.args.get('service_id', type=int)
    selected_date_str = request.args.get('date', '')
    selected_service = next((s for s in services if s.id == selected_service_id), None) or (services[0] if services else None)

    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = date.today()

    creneaux = []
    if selected_service:
        creneaux = generate_creneaux(business, selected_service, selected_date)

    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        prenom = request.form.get('prenom', '').strip()
        email = request.form.get('email', '').strip()
        telephone = request.form.get('telephone', '').strip()
        service_id = request.form.get('service_id', type=int)
        date_str = request.form.get('date', '')
        creneau = request.form.get('creneau', '')

        if not all([prenom, telephone, service_id, date_str, creneau]):
            flash('Tous les champs obligatoires doivent être remplis.', 'error')
        else:
            try:
                resa_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                service = Service.query.filter_by(id=service_id, business_id=business.id, actif=True).first()
                if not service:
                    flash('Service introuvable.', 'error')
                else:
                    existing = Reservation.query.filter_by(
                        business_id=business.id, service_id=service_id,
                        date=resa_date, creneau=creneau, statut='confirmé'
                    ).first()
                    if existing:
                        flash('Ce créneau vient d\'être pris. Veuillez en choisir un autre.', 'error')
                    else:
                        resa = Reservation(
                            business_id=business.id,
                            service_id=service_id,
                            nom=nom, prenom=prenom, email=email, telephone=telephone,
                            date=resa_date, creneau=creneau,
                        )
                        db.session.add(resa)
                        db.session.commit()
                        return redirect(url_for('public.confirmation', slug=slug, rid=resa.id))
            except ValueError:
                flash('Date invalide.', 'error')

    return render_template(
        'public/booking.html',
        business=business, services=services,
        selected_service=selected_service,
        selected_date=selected_date,
        creneaux=creneaux,
        slug=slug,
    )


@public_bp.route('/<slug>/confirmation/<int:rid>')
def confirmation(slug, rid):
    user = User.query.filter_by(slug=slug).first_or_404()
    resa = Reservation.query.filter_by(id=rid, business_id=user.business.id).first_or_404()
    return render_template('public/confirmation.html', resa=resa, business=user.business, slug=slug)
