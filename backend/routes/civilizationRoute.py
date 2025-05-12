from flask import Blueprint, request, jsonify, session
from database import (get_civilization_types, get_civilization_by_id, add_game_with_civilization)

# Create blueprint for civilization routes
civilization_blueprint = Blueprint('civilization', __name__)

@civilization_blueprint.route('/api/civilizations', methods=['GET'])
def get_all_civilizations():
    """Get all available civilization types"""
    try:
        civilizations = get_civilization_types()
        return jsonify(civilizations), 200
    except Exception as e:
        print(f"Error getting civilizations: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@civilization_blueprint.route('/api/civilizations/<civ_id>', methods=['GET'])
def get_civilization(civ_id):
    """Get a specific civilization by its ID"""
    try:
        civilization = get_civilization_by_id(civ_id)
        if not civilization:
            return jsonify({"error": "Civilization not found"}), 404
        return jsonify(civilization), 200
    except Exception as e:
        print(f"Error getting civilization: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@civilization_blueprint.route('/api/games/civilization', methods=['POST'])
def create_game_with_civilization():
    """Create a new game with a specified civilization"""
    try:
        # Check if user is logged in
        username = session.get('username')
        if not username:
            return jsonify({"error": "User not logged in"}), 401
        
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract required fields
        map_id = data.get('map_id')
        difficulty = data.get('difficulty')
        civ_id = data.get('civ_id')
        game_name = data.get('name', "New Game")  # Optional with default
        
        # Validate required fields
        if not map_id or not difficulty or not civ_id:
            return jsonify({
                "error": "Required fields missing", 
                "required": ["map_id", "difficulty", "civ_id"]
            }), 400
        
        # Validate civilization exists
        civilization = get_civilization_by_id(civ_id)
        if not civilization:
            return jsonify({"error": f"Invalid civilization ID: {civ_id}"}), 400
        
        # Create the game with civilization
        result = add_game_with_civilization(username, map_id, difficulty, civ_id, game_name)
        
        if result:
            # Get the game ID for the response
            game_id = session.get('game', {}).get('game_id', 'unknown')
            
            return jsonify({
                "success": True,
                "message": "Game created successfully with civilization",
                "game_id": game_id,
                "civilization": civilization["name"]
            }), 201
        else:
            return jsonify({
                "success": False,
                "message": "Failed to create game"
            }), 500
            
    except Exception as e:
        print(f"Error creating game with civilization: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
