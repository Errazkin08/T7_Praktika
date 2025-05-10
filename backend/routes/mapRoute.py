from flask import Blueprint, request, jsonify, session
from database import (add_map, get_first_map, get_all_maps, delete_map, get_map)
from bson import ObjectId

# Create blueprint for map routes
map_blueprint = Blueprint('map', __name__)

# Create a new map
@map_blueprint.route('/api/maps', methods=['POST'])
def create_map():
    data = request.get_json()
    width = data.get('width')
    height = data.get('height')
    startPoint = data.get('startPoint')
    difficulty = data.get('difficulty')
    name = data.get('name')  # Nuevo campo para el nombre del mapa
    
    # Validate required fields
    if not width or not height or not startPoint or not difficulty:
        return jsonify({"error": "Width, height, startPoint, and difficulty are required"}), 400
    
    # Validate data types
    if not isinstance(width, int) or not isinstance(height, int):
        return jsonify({"error": "Width and height must be integers"}), 400
    
    if not isinstance(startPoint, list) or len(startPoint) != 2:
        return jsonify({"error": "StartPoint must be a list of two integers"}), 400
    
    if difficulty not in ["easy", "medium", "hard"]:
        return jsonify({"error": "Difficulty must be 'easy', 'medium', or 'hard'"}), 400
    
    # Create map in database
    result = add_map(width, height, startPoint, difficulty, name)
    
    return jsonify({
        "message": "Map created successfully",
        "map_id": str(result.inserted_id)
    }), 201

# Get the first map from the database
@map_blueprint.route('/api/maps/first', methods=['GET'])
def get_first_map_endpoint():
    try:
        # Get the first map
        map_data = get_first_map()
        if not map_data:
            return jsonify({"error": "No maps found"}), 404
        return jsonify(map_data), 200
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
    
@map_blueprint.route('/api/maps', methods=['GET'])
def get_maps():
    """Get all maps from the database"""
    try:
        print("Getting all maps...")
        maps = get_all_maps()
        
        # Asegurar que los mapas sean serializables a JSON
        json_safe_maps = []
        for map_doc in maps:
            # Crear una copia segura para JSON
            safe_map = {}
            for key, value in map_doc.items():
                if key == '_id' or key == 'map_id':
                    safe_map[key] = str(value)
                elif isinstance(value, list) and not key in ['grid', 'terrain']:
                    # Para listas que no son la cuadrícula o el terreno (que son matrices)
                    safe_map[key] = [str(item) if isinstance(item, ObjectId) else item for item in value]
                else:
                    safe_map[key] = value
            json_safe_maps.append(safe_map)
            
        print(f"Returning {len(json_safe_maps)} maps")
        
        if not json_safe_maps or len(json_safe_maps) == 0:
            return jsonify({"message": "No maps found"}), 404
        
        return jsonify(json_safe_maps), 200
    except Exception as e:
        print(f"Error getting maps: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@map_blueprint.route('/api/maps/<map_id>', methods=['DELETE'])
def delete_map_endpoint(map_id):
    """Delete a map by its ID"""
    try:
        # Check if user is logged in
        if 'username' not in session:
            return jsonify({"error": "User not logged in"}), 401
        
        print(f"Attempting to delete map with ID: {map_id}")
        
        # Try to delete the map
        result = delete_map(map_id)
        
        if result:
            return jsonify({"message": "Map deleted successfully"}), 200
        else:
            return jsonify({"error": "Map not found or could not be deleted"}), 404
    except Exception as e:
        print(f"Error in delete_map_endpoint: {str(e)}")
        return jsonify({"error": f"Error deleting map: {str(e)}"}), 500

@map_blueprint.route('/api/maps/<map_id>', methods=['GET'])
def get_map_endpoint(map_id):
    """Get a specific map by its ID"""
    try:
        # Check if user is logged in
        if 'username' not in session:
            return jsonify({"error": "User not logged in"}), 401
        
        # Fetch the map from the database
        map_data = get_map(map_id)
        
        if not map_data:
            return jsonify({"error": "Map not found"}), 404
        
        # Convert ObjectId to string for JSON serialization
        map_data['_id'] = str(map_data['_id'])
        
        return jsonify(map_data), 200
    except Exception as e:
        print(f"Error getting map: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
