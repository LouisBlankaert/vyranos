import re
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from ..models import User, Business
from .. import db

auth_bp = Blueprint('auth', __name__)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        nom_commerce = request.form.get('nom_commerce', '').strip()

        if not email or not password or not nom_commerce:
            flash('Tous les champs sont requis.', 'error')
            return render_template('auth/signup.html')

        if len(password) < 8:
            flash('Le mot de passe doit faire au moins 8 caractères.', 'error')
            return render_template('auth/signup.html')

        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'error')
            return render_template('auth/signup.html')

        slug = slugify(nom_commerce)
        base_slug = slug
        counter = 1
        while User.query.filter_by(slug=slug).first():
            slug = f'{base_slug}-{counter}'
            counter += 1

        user = User(email=email, slug=slug)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        business = Business(user_id=user.id, nom=nom_commerce)
        db.session.add(business)
        db.session.commit()

        login_user(user)
        return redirect(url_for('dashboard.index'))

    return render_template('auth/signup.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=request.form.get('remember'))
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))

        flash('Email ou mot de passe incorrect.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
