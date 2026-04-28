import os
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from ..models import Business, Service
from .. import db

onboarding_bp = Blueprint('onboarding', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload(file, prefix):
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f'{prefix}_{current_user.id}.{ext}'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    return f'/static/uploads/{filename}'


@onboarding_bp.route('/step1', methods=['GET', 'POST'])
@login_required
def step1():
    business = current_user.business
    if request.method == 'POST':
        business.nom = request.form.get('nom', '').strip() or business.nom
        business.description = request.form.get('description', '').strip()
        business.adresse = request.form.get('adresse', '').strip()
        business.ville = request.form.get('ville', '').strip()
        business.telephone = request.form.get('telephone', '').strip()
        business.email_contact = request.form.get('email_contact', '').strip()
        current_user.onboarding_step = max(current_user.onboarding_step, 1)
        db.session.commit()
        return redirect(url_for('onboarding.step2'))
    return render_template('onboarding/step1.html', business=business, step=1)


@onboarding_bp.route('/step2', methods=['GET', 'POST'])
@login_required
def step2():
    business = current_user.business
    if request.method == 'POST':
        logo = request.files.get('logo')
        cover = request.files.get('cover')
        logo_url = save_upload(logo, 'logo')
        cover_url = save_upload(cover, 'cover')
        if logo_url:
            business.logo_url = logo_url
        if cover_url:
            business.cover_url = cover_url
        business.couleur_primaire = request.form.get('couleur_primaire', '#1a1a1a')
        business.instagram = request.form.get('instagram', '').strip()
        business.tiktok = request.form.get('tiktok', '').strip()
        current_user.onboarding_step = max(current_user.onboarding_step, 2)
        db.session.commit()
        return redirect(url_for('onboarding.step3'))
    return render_template('onboarding/step2.html', business=business, step=2)


@onboarding_bp.route('/step3', methods=['GET', 'POST'])
@login_required
def step3():
    business = current_user.business
    if request.method == 'POST':
        noms = request.form.getlist('service_nom')
        durees = request.form.getlist('service_duree')
        prix = request.form.getlist('service_prix')
        descriptions = request.form.getlist('service_description')

        Service.query.filter_by(business_id=business.id).delete()
        for nom, duree, p, desc in zip(noms, durees, prix, descriptions):
            if nom.strip():
                service = Service(
                    business_id=business.id,
                    nom=nom.strip(),
                    duree_minutes=int(duree) if duree.isdigit() else 60,
                    prix=float(p) if p else 0,
                    description=desc.strip(),
                )
                db.session.add(service)

        current_user.onboarding_step = max(current_user.onboarding_step, 3)
        db.session.commit()
        return redirect(url_for('onboarding.step4'))
    return render_template('onboarding/step3.html', business=business, step=3)


@onboarding_bp.route('/step4', methods=['GET', 'POST'])
@login_required
def step4():
    business = current_user.business
    jours = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche']

    if request.method == 'POST':
        horaires = {}
        for jour in jours:
            ouvert = request.form.get(f'{jour}_ouvert') == 'on'
            debut = request.form.get(f'{jour}_debut', '09:00')
            fin = request.form.get(f'{jour}_fin', '18:00')
            horaires[jour] = {'ouvert': ouvert, 'debut': debut, 'fin': fin}
        business.horaires = horaires
        current_user.onboarding_step = max(current_user.onboarding_step, 4)
        db.session.commit()
        return redirect(url_for('onboarding.step5'))

    return render_template('onboarding/step4.html', business=business, step=4, jours=jours)


@onboarding_bp.route('/step5', methods=['GET', 'POST'])
@login_required
def step5():
    business = current_user.business
    if request.method == 'POST':
        business.template = request.form.get('template', 'elegant')
        current_user.onboarding_step = max(current_user.onboarding_step, 5)
        db.session.commit()
        return redirect(url_for('billing.checkout'))
    return render_template('onboarding/step5.html', business=business, step=5)
