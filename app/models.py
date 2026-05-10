from datetime import datetime, timezone
from flask_login import UserMixin
import bcrypt
from . import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    stripe_customer_id = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    trial_ends_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    onboarding_step = db.Column(db.Integer, default=0)

    business = db.relationship('Business', backref='user', uselist=False, cascade='all, delete-orphan')
    subscription = db.relationship('Subscription', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def check_password(self, password):
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())

    def is_subscribed(self):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if self.trial_ends_at and self.trial_ends_at.replace(tzinfo=timezone.utc) > now:
            return True
        if self.subscription and self.subscription.statut == 'active':
            return True
        return False


class Business(db.Model):
    __tablename__ = 'businesses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    adresse = db.Column(db.String(200))
    ville = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    email_contact = db.Column(db.String(120))
    instagram = db.Column(db.String(100))
    tiktok = db.Column(db.String(100))
    logo_url = db.Column(db.String(300))
    cover_url = db.Column(db.String(300))
    couleur_primaire = db.Column(db.String(7), default='#1a1a1a')
    horaires = db.Column(db.JSON, default=dict)
    template = db.Column(db.String(20), default='elegant')
    creneau_step = db.Column(db.Integer, default=30)
    custom_domain = db.Column(db.String(100), unique=True, nullable=True)

    services = db.relationship('Service', backref='business', lazy=True, cascade='all, delete-orphan')
    reservations = db.relationship('Reservation', backref='business', lazy=True, cascade='all, delete-orphan')
    blocages = db.relationship('Blocage', backref='business', lazy=True, cascade='all, delete-orphan')


class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duree_minutes = db.Column(db.Integer, nullable=False, default=60)
    prix = db.Column(db.Float, nullable=False, default=0)
    actif = db.Column(db.Boolean, default=True)

    reservations = db.relationship('Reservation', backref='service', lazy=True)


class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    nom = db.Column(db.String(100), nullable=True)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    telephone = db.Column(db.String(20))
    date = db.Column(db.Date, nullable=False)
    creneau = db.Column(db.String(5), nullable=False)  # "09:00"
    statut = db.Column(db.String(20), default='confirmé')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class Blocage(db.Model):
    __tablename__ = 'blocages'
    id = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey('businesses.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    debut = db.Column(db.String(5), nullable=False)
    fin = db.Column(db.String(5), nullable=False)
    motif = db.Column(db.String(100), default='Indisponible')


class Subscription(db.Model):
    __tablename__ = 'subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_subscription_id = db.Column(db.String(100))
    statut = db.Column(db.String(20), default='inactive')
    current_period_end = db.Column(db.DateTime)
