from flask import Blueprint, jsonify

from app.storage.cache_manager import get_or_create_cache

api_bp = Blueprint('api', __name__)

@api_bp.route('/data')
def get_all_data():
    memory_store = get_or_create_cache()
    data = memory_store.get_all_latest()
    return jsonify(data)

@api_bp.route('/data/<ins_id>')
def get_data(ins_id):
    memory_store = get_or_create_cache()
    return jsonify(memory_store.get_latest(ins_id))

@api_bp.route('/positions')
def get_positions():
    memory_store = get_or_create_cache()
    return jsonify(memory_store.get_positions(last_minutes=5))
