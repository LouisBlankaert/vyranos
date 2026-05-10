from datetime import date
from flask import Blueprint, render_template, abort

main_bp = Blueprint('main', __name__)


DEMO_DATA = {
    'elegant': {
        'business': {
            'nom': 'Salon Élise',
            'description': 'Salon de coiffure et beauté au cœur de Paris. Coupes, colorations, soins — une expérience sur-mesure dans un cadre chaleureux.',
            'adresse': '24 rue des Martyrs', 'ville': 'Paris',
            'telephone': '01 42 85 63 21', 'email_contact': 'contact@salon-elise.fr',
            'instagram': '@salon_elise', 'tiktok': None,
            'logo_url': None, 'cover_url': None, 'couleur_primaire': '#c9a84c',
            'horaires': {
                'lundi': {'ouvert': False},
                'mardi': {'ouvert': True, 'debut': '09:00', 'fin': '19:00'},
                'mercredi': {'ouvert': True, 'debut': '09:00', 'fin': '19:00'},
                'jeudi': {'ouvert': True, 'debut': '09:00', 'fin': '20:00'},
                'vendredi': {'ouvert': True, 'debut': '09:00', 'fin': '20:00'},
                'samedi': {'ouvert': True, 'debut': '09:00', 'fin': '18:00'},
                'dimanche': {'ouvert': False},
            },
        },
        'services': [
            {'nom': 'Coupe femme', 'description': 'Coupe + brushing', 'duree_minutes': 60, 'prix': 55},
            {'nom': 'Coupe homme', 'description': 'Coupe + finitions', 'duree_minutes': 30, 'prix': 28},
            {'nom': 'Coloration', 'description': 'Couleur complète + soin', 'duree_minutes': 90, 'prix': 85},
            {'nom': 'Mèches / balayage', 'description': 'Technique + brushing', 'duree_minutes': 120, 'prix': 110},
            {'nom': 'Soin kératine', 'description': 'Lissage et brillance', 'duree_minutes': 90, 'prix': 75},
            {'nom': 'Brushing', 'description': 'Mise en forme', 'duree_minutes': 30, 'prix': 30},
        ],
    },
    'moderne': {
        'business': {
            'nom': 'Brasserie Le Central',
            'description': 'Cuisine bistronomique, cocktails maison et ambiance conviviale. Ouvert tous les jours pour déjeuner et dîner.',
            'adresse': '8 place de la République', 'ville': 'Lyon',
            'telephone': '04 72 11 42 88', 'email_contact': 'hello@lecentral.fr',
            'instagram': '@lecentral_lyon', 'tiktok': '@lecentral',
            'logo_url': None, 'cover_url': None, 'couleur_primaire': '#8B4513',
            'horaires': {
                'lundi': {'ouvert': True, 'debut': '12:00', 'fin': '22:00'},
                'mardi': {'ouvert': True, 'debut': '12:00', 'fin': '22:00'},
                'mercredi': {'ouvert': True, 'debut': '12:00', 'fin': '22:00'},
                'jeudi': {'ouvert': True, 'debut': '12:00', 'fin': '23:00'},
                'vendredi': {'ouvert': True, 'debut': '12:00', 'fin': '23:30'},
                'samedi': {'ouvert': True, 'debut': '11:00', 'fin': '23:30'},
                'dimanche': {'ouvert': True, 'debut': '11:00', 'fin': '21:00'},
            },
        },
        'services': [
            {'nom': 'Table déjeuner', 'description': 'Formule entrée + plat + dessert', 'duree_minutes': 60, 'prix': 22},
            {'nom': 'Table dîner', 'description': 'Réservation pour le soir', 'duree_minutes': 90, 'prix': 0},
            {'nom': 'Brunch dominical', 'description': 'Buffet à volonté le dimanche', 'duree_minutes': 120, 'prix': 28},
            {'nom': 'Soirée privatisée', 'description': 'Espace privatisé (min. 20 pers.)', 'duree_minutes': 180, 'prix': 0},
        ],
    },
    'minimal': {
        'business': {
            'nom': 'Thomas Renaud',
            'description': 'Coach en performance et développement personnel. Accompagnement individuel pour atteindre vos objectifs professionnels et personnels.',
            'adresse': None, 'ville': 'Paris (visio ou présentiel)',
            'telephone': '06 87 22 41 09', 'email_contact': 'thomas@renaud-coaching.fr',
            'instagram': '@thomas.renaud.coach', 'tiktok': None,
            'logo_url': None, 'cover_url': None, 'couleur_primaire': '#111111',
            'horaires': {
                'lundi': {'ouvert': True, 'debut': '08:00', 'fin': '18:00'},
                'mardi': {'ouvert': True, 'debut': '08:00', 'fin': '18:00'},
                'mercredi': {'ouvert': True, 'debut': '08:00', 'fin': '18:00'},
                'jeudi': {'ouvert': True, 'debut': '08:00', 'fin': '18:00'},
                'vendredi': {'ouvert': True, 'debut': '08:00', 'fin': '16:00'},
                'samedi': {'ouvert': False},
                'dimanche': {'ouvert': False},
            },
        },
        'services': [
            {'nom': 'Séance découverte', 'description': '30 min — gratuit', 'duree_minutes': 30, 'prix': 0},
            {'nom': 'Coaching individuel', 'description': 'Séance d\'1h en visio ou présentiel', 'duree_minutes': 60, 'prix': 90},
            {'nom': 'Pack 5 séances', 'description': 'Suivi sur 5 semaines', 'duree_minutes': 60, 'prix': 400},
            {'nom': 'Bilan de carrière', 'description': 'Session approfondie 2h', 'duree_minutes': 120, 'prix': 180},
        ],
    },
    'nature': {
        'business': {
            'nom': 'Studio Racines',
            'description': 'Naturopathe & praticienne en bien-être. Retrouvez l\'équilibre grâce à des soins naturels adaptés à votre corps et votre rythme de vie.',
            'adresse': '12 chemin des Lilas', 'ville': 'Annecy',
            'telephone': '06 31 74 58 20', 'email_contact': 'contact@studio-racines.fr',
            'instagram': '@studio.racines', 'tiktok': None,
            'logo_url': None, 'cover_url': None, 'couleur_primaire': '#5c7a4e',
            'horaires': {
                'lundi': {'ouvert': False},
                'mardi': {'ouvert': True, 'debut': '09:00', 'fin': '18:00'},
                'mercredi': {'ouvert': True, 'debut': '09:00', 'fin': '18:00'},
                'jeudi': {'ouvert': True, 'debut': '09:00', 'fin': '18:00'},
                'vendredi': {'ouvert': True, 'debut': '09:00', 'fin': '17:00'},
                'samedi': {'ouvert': True, 'debut': '10:00', 'fin': '14:00'},
                'dimanche': {'ouvert': False},
            },
        },
        'services': [
            {'nom': 'Bilan naturopathique', 'description': 'Consultation initiale complète 1h30', 'duree_minutes': 90, 'prix': 75},
            {'nom': 'Soin réflexologie', 'description': 'Massage des pieds et rééquilibrage', 'duree_minutes': 60, 'prix': 55},
            {'nom': 'Accompagnement detox', 'description': 'Programme personnalisé sur 4 semaines', 'duree_minutes': 60, 'prix': 120},
            {'nom': 'Massage bien-être', 'description': 'Massage relaxant corps entier', 'duree_minutes': 60, 'prix': 65},
            {'nom': 'Séance yoga privée', 'description': 'Cours individuel adapté à votre niveau', 'duree_minutes': 60, 'prix': 50},
        ],
    },
    'premium': {
        'business': {
            'nom': 'Cabinet Morel & Associés',
            'description': 'Avocats en droit des affaires et droit social. Conseil stratégique, contentieux et accompagnement juridique sur mesure pour les entreprises.',
            'adresse': '47 avenue Hoche', 'ville': 'Paris 8e',
            'telephone': '01 55 62 88 00', 'email_contact': 'contact@morel-avocats.fr',
            'instagram': None, 'tiktok': None,
            'logo_url': None, 'cover_url': None, 'couleur_primaire': '#c41e3a',
            'horaires': {
                'lundi': {'ouvert': True, 'debut': '09:00', 'fin': '19:00'},
                'mardi': {'ouvert': True, 'debut': '09:00', 'fin': '19:00'},
                'mercredi': {'ouvert': True, 'debut': '09:00', 'fin': '19:00'},
                'jeudi': {'ouvert': True, 'debut': '09:00', 'fin': '19:00'},
                'vendredi': {'ouvert': True, 'debut': '09:00', 'fin': '18:00'},
                'samedi': {'ouvert': False},
                'dimanche': {'ouvert': False},
            },
        },
        'services': [
            {'nom': 'Consultation initiale', 'description': 'Analyse de votre situation juridique', 'duree_minutes': 60, 'prix': 250},
            {'nom': 'Rédaction de contrats', 'description': 'CGV, contrats commerciaux, NDA', 'duree_minutes': 90, 'prix': 450},
            {'nom': 'Accompagnement création', 'description': 'Structuration juridique de votre société', 'duree_minutes': 120, 'prix': 800},
            {'nom': 'Contentieux & médiation', 'description': 'Représentation et gestion de litiges', 'duree_minutes': 60, 'prix': 0},
        ],
    },
}


def make_obj(d):
    return type('Obj', (), d)()


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/demo')
def demo():
    return render_template('demo.html')


@main_bp.route('/demo/<template>')
def demo_template(template):
    if template not in DEMO_DATA:
        abort(404)
    data = DEMO_DATA[template]
    return render_template(
        f'public/templates/{template}.html',
        business=make_obj(data['business']),
        services=[make_obj(s) for s in data['services']],
        user=make_obj({'slug': 'demo'}),
        is_demo=True,
    )
