from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config_class="app.config.DevConfig"):
    app = Flask(__name__)

    app.config.from_object(config_class)

    db.init_app(app)

    from app.models import Expense
    from app.main.routes import main_bp
    from app.api.routes import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()

    return app