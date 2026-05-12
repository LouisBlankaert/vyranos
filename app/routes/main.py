from flask import Blueprint, render_template, request, flash, redirect, url_for
from ..models import Lead
from .. import db

main_bp = Blueprint('main', __name__)

TYPES_COMMERCE = [
    'Coiffeur / Barbier',
    'Esthéticienne / Nail art',
    'Restaurant / Café',
    'Boulangerie / Pâtisserie',
    'Coach / Personal trainer',
    'Photographe',
    'Médecin / Kiné / Ostéo',
    'Tatoueur / Piercing',
    'Auto / Moto',
    'Autre',
]


@main_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        prenom = request.form.get('prenom', '').strip()
        nom = request.form.get('nom', '').strip()
        email = request.form.get('email', '').strip()
        telephone = request.form.get('telephone', '').strip()
        nom_commerce = request.form.get('nom_commerce', '').strip()
        type_commerce = request.form.get('type_commerce', '').strip()
        message = request.form.get('message', '').strip()

        if not all([prenom, nom, email, telephone, nom_commerce, type_commerce]):
            flash('Merci de remplir tous les champs obligatoires.', 'error')
            return redirect(url_for('main.index') + '#contact')

        lead = Lead(
            prenom=prenom,
            nom=nom,
            email=email,
            telephone=telephone,
            nom_commerce=nom_commerce,
            type_commerce=type_commerce,
            message=message or None,
        )
        db.session.add(lead)
        db.session.commit()
        flash('Votre demande a bien été envoyée ! Je vous recontacte très vite.', 'success')
        return redirect(url_for('main.index') + '#contact')

    return render_template('index.html', types_commerce=TYPES_COMMERCE)
