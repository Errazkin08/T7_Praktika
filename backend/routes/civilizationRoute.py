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
    """Create a new game with specified civilizations for player and AI"""
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
        ai_civ_id = data.get('ai_civ_id')
        game_name = data.get('name', "New Game")  # Optional with default
        
        # Validate required fields
        if not map_id or not difficulty or not civ_id:
            return jsonify({
                "error": "Required fields missing", 
                "required": ["map_id", "difficulty", "civ_id"]
            }), 400
        
        # Validate civilizations exist
        player_civ = get_civilization_by_id(civ_id)
        if not player_civ:
            return jsonify({"error": f"Invalid player civilization ID: {civ_id}"}), 400
            
        # Validate AI civilization if provided
        ai_civ = None
        if ai_civ_id:
            ai_civ = get_civilization_by_id(ai_civ_id)
            if not ai_civ:
                return jsonify({"error": f"Invalid AI civilization ID: {ai_civ_id}"}), 400
        
        # Create the game with civilizations
        result = add_game_with_civilization(username, map_id, difficulty, civ_id, game_name, ai_civ_id)
        
        if result:
            # Get the game ID for the response
            game_id = session.get('game', {}).get('game_id', 'unknown')
            
            response_data = {
                "success": True,
                "message": "Game created successfully with civilization",
                "game_id": game_id,
                "player_civilization": player_civ["name"]
            }
            
            if ai_civ:
                response_data["ai_civilization"] = ai_civ["name"]
                
            return jsonify(response_data), 201
        else:
            return jsonify({
                "success": False,
                "message": "Failed to create game"
            }), 500
            
    except Exception as e:
        print(f"Error creating game with civilization: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500
