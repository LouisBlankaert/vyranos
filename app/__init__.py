import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
    db_url = os.environ.get('DATABASE_URL', 'sqlite:///vyranos.db')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Connectez-vous pour accéder à cette page.'

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.public import public_bp
    from .routes.onboarding import onboarding_bp
    from .routes.billing import billing_bp
    from .routes.main import main_bp
    from .routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(onboarding_bp, url_prefix='/onboarding')
    app.register_blueprint(billing_bp, url_prefix='/billing')
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp)

    with app.app_context():
        db.create_all()

    return app
