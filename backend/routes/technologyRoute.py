from flask import Blueprint, request, jsonify, session
from database import (get_technology_types)

# Create blueprint for technology routes
technology_blueprint = Blueprint('technology', __name__)

@technology_blueprint.route('/api/technology/types', methods=['GET'])
def get_technology_types_endpoint():
    """Get all available technology types"""
    technology_types = get_technology_types()
    return jsonify(technology_types), 200

