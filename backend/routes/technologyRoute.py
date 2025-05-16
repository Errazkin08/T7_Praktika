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

@technology_blueprint.route('/api/technology/costs', methods=['GET'])
def get_technology_costs():
    """Get costs of all available technology types"""
    try:
        technology_types = get_technology_types()
        
        # Extract only the cost information from each technology type
        technology_costs = {}
        for tech in technology_types:
            # Check if the technology has cost information
            if "cost" in tech:
                technology_costs[tech["id"]] = {
                    "name": tech["name"],
                    "cost": tech["cost"],
                    "turns": tech.get("turns", 0)
                }
            else:
                # Default cost structure if none specified
                technology_costs[tech["id"]] = {
                    "name": tech["name"],
                    "cost": {
                        "gold": tech.get("turns", 10) * 5,  # Default formula
                        "science": tech.get("turns", 10) * 2
                    },
                    "turns": tech.get("turns", 0)
                }
            
        return jsonify(technology_costs), 200
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@technology_blueprint.route('/api/technology/costs/<type_id>', methods=['GET'])
def get_technology_cost(type_id):
    """Get the cost of a specific technology type by ID"""
    try:
        # Get the technology type from the database
        technology_type = get_technology_type(type_id)
        
        if not technology_type:
            return jsonify({"error": "Technology type not found"}), 404
        
        # Extract only the cost information
        if "cost" in technology_type:
            cost_data = {
                "name": technology_type["name"],
                "cost": technology_type["cost"],
                "turns": technology_type.get("turns", 0)
            }
        else:
            # Default cost structure if none specified
            cost_data = {
                "name": technology_type["name"],
                "cost": {
                    "gold": technology_type.get("turns", 10) * 5,  # Default formula
                    "science": technology_type.get("turns", 10) * 2
                },
                "turns": technology_type.get("turns", 0)
            }
        
        return jsonify(cost_data), 200
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

