from flask import Blueprint, render_template, current_app

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    ins_configs = current_app.config.get('INS_CONFIGS', {})
    return render_template('index.html', ins_configs=ins_configs)
