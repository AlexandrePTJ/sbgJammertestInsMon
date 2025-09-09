from typing import List

from flask import Flask

from app.blueprints.api import api_bp
from app.blueprints.main import main_bp
from app.models.config import INSConfig


def create_app(ins_configs: List[INSConfig] = None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['INS_CONFIGS'] = ins_configs

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
