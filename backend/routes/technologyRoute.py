from flask import Blueprint, request, jsonify, session
from database import (get_technology_types, get_technology_type)

# Create blueprint for technology routes
technology_blueprint = Blueprint('technology', __name__)

@technology_blueprint.route('/api/technology/types', methods=['GET'])
def get_technology_types_endpoint():
    """Get all available technology types"""
    technology_types = get_technology_types()
    return jsonify(technology_types), 200

@technology_blueprint.route('/api/technologies/types/<type_id>', methods=['GET'])
def get_technology_type_endpoint(type_id):
    """Get a specific technology type by its ID"""
    technology_type = get_technology_type(type_id)
    if not technology_type:
        return jsonify({"error": "technology type not found"}), 404
    return jsonify(technology_type), 200

