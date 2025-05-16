from flask import Blueprint, request, jsonify, session
from database import (get_building_types, get_building_type, add_building_to_city)

# Create blueprint for building routes
building_blueprint = Blueprint('building', __name__)

@building_blueprint.route('/api/buildings/types', methods=['GET'])
def get_building_types_endpoint():
    """Get all available building types"""
    building_types = get_building_types()
    return jsonify(building_types), 200

@building_blueprint.route('/api/buildings/types/<type_id>', methods=['GET'])
def get_building_type_endpoint(type_id):
    """Get a specific building type by its ID"""
    building_type = get_building_type(type_id)
    if not building_type:
        return jsonify({"error": "Building type not found"}), 404
    return jsonify(building_type), 200

@building_blueprint.route('/api/buildings', methods=['POST'])
def add_building_endpoint():
    """Add a new building to a city"""
    username = session.get('username')
    if not username:
        return jsonify({"error": "User not logged in"}), 401
    
    data = request.get_json()
    city_id = data.get('city_id')
    type_id = data.get('type_id')
    
    if not city_id or not type_id:
        return jsonify({"error": "City ID and building type ID are required"}), 400
    
    success, result = add_building_to_city(city_id, type_id)
    if not success:
        return jsonify({"error": result}), 400
    
    return jsonify({
        "message": "Building added successfully",
        "building": result
    }), 201

@building_blueprint.route('/api/cities/<city_id>/buildings', methods=['GET'])
def get_city_buildings_endpoint(city_id):
    """Get all buildings for a specific city"""
    game = session.get('game')
    if not game:
        return jsonify({"error": "No active game"}), 404
    
    # Find the city
    cities = []
    if game.get("player") and game["player"].get("cities"):
        cities.extend(game["player"]["cities"])
    if game.get("ia") and game["ia"].get("cities"):
        cities.extend(game["ia"]["cities"])
    
    city = next((c for c in cities if c.get("id") == city_id), None)
    
    if not city:
        return jsonify({"error": "City not found"}), 404
    
    buildings = city.get("buildings", [])
    return jsonify(buildings), 200

@building_blueprint.route('/api/cities/<city_id>/buildings/<building_id>', methods=['DELETE'])
def remove_building_endpoint(city_id, building_id):
    """Remove a building from a city"""
    game = session.get('game')
    if not game:
        return jsonify({"error": "No active game"}), 404
    
    # Find the city
    cities = []
    if game.get("player") and game["player"].get("cities"):
        cities.extend(game["player"]["cities"])
    if game.get("ia") and game["ia"].get("cities"):
        cities.extend(game["ia"]["cities"])
    
    city = next((c for c in cities if c.get("id") == city_id), None)
    
    if not city:
        return jsonify({"error": "City not found"}), 404
    
    buildings = city.get("buildings", [])
    building_index = next((i for i, b in enumerate(buildings) if b.get("id") == building_id), None)
    
    if building_index is None:
        return jsonify({"error": "Building not found in city"}), 404
    
    # Remove the building
    removed_building = buildings.pop(building_index)
    session.modified = True
    
    return jsonify({
        "message": "Building removed successfully",
        "building": removed_building
    }), 200

@building_blueprint.route('/api/buildings/costs', methods=['GET'])
def get_building_costs():
    """Get costs of all available building types"""
    try:
        building_types = get_building_types()
        
        # Extract only the cost information from each building type
        building_costs = {}
        for building in building_types:
            building_costs[building["type_id"]] = {
                "name": building["name"],
                "cost": building["cost"],
                "turns": building.get("turns", 0)
            }
            
        return jsonify(building_costs), 200
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@building_blueprint.route('/api/buildings/costs/<type_id>', methods=['GET'])
def get_building_cost(type_id):
    """Get the cost of a specific building type by ID"""
    try:
        # Get the building type from the database
        building_type = get_building_type(type_id)
        
        if not building_type:
            return jsonify({"error": "Building type not found"}), 404
        
        # Extract only the cost information
        cost_data = {
            "name": building_type["name"],
            "cost": building_type["cost"],
            "turns": building_type.get("turns", 0)
        }
        
        return jsonify(cost_data), 200
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500
