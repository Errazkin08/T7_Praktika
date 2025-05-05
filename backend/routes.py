from flask import Blueprint, request, jsonify, session
from database import (add_user, find_user, save_game, get_all_users, update_user_login, add_map, get_first_map, add_game, delete_game,
                     get_troop_types, get_troop_type, add_troop_to_player, get_player_troops, update_troop_position,
                     update_troop_status, reset_troops_status)
import hashlib

routes_blueprint = Blueprint('routes', __name__)

#just a proba endpoint
@routes_blueprint.route('/proba', methods=['GET'])
def proba():
    return "Kaixoooo"

#Register a new user
@routes_blueprint.route('/api/users', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    # Check if user already exists
    existing_user = find_user(username)
    if existing_user:
        return jsonify({"error": "Username already exists"}), 409
    
    # Hash the password before storing
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Add user to database
    add_user(username, password_hash)
    return jsonify({"message": "User created successfully"}), 201


#Login a user
@routes_blueprint.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    
    # Fetch user from database
    user = find_user(username)
    if not user:
        return jsonify({"error": "Invalid username or password"}), 401
    
    # Verify password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash != user['password']:
        return jsonify({"error": "Invalid username or password"}), 401
    
    # Store user in session
    session['username'] = user['username']
    session['user_id'] = str(user.get('_id', ''))
    update_user_login(user['username'])
    
    return jsonify({
        "message": "Login successful",
        "user": {
            "username": user['username'],
            "score": user['score'],
            "level": user['level']
        }
    }), 200

# Logout a user
@routes_blueprint.route('/api/logout', methods=['POST'])
def logout():
    # Clear the session
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

# Check if user is logged in
@routes_blueprint.route('/api/session', methods=['GET'])
def check_session():
    if 'username' in session:
        user = find_user(session['username'])
        if user:
            return jsonify({
                "authenticated": True,
                "user": {
                    "username": user['username'],
                    "score": user['score'],
                    "level": user['level']
                }
            }), 200
    return jsonify({"authenticated": False}), 401

# Get user information from its username
@routes_blueprint.route('/api/users/<username>', methods=['GET'])
def get_user(username):
    # Fetch user from database
    user = find_user(username)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "username": user['username'],
        "score": user['score'],
        "level": user['level']
    }), 200

#Get all users from the database
@routes_blueprint.route('/api/users/', methods=['GET'])
def get_all_users():
    try:
        # Query all users from the database
        users = get_all_users()
        if not users or len(users) == 0:
            return jsonify({"message": "No users found"}), 404
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

# Create a new map
@routes_blueprint.route('/api/maps', methods=['POST'])
def create_map():
    data = request.get_json()
    width = data.get('width')
    height = data.get('height')
    startPoint = data.get('startPoint')
    difficulty = data.get('difficulty')
    
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
    result = add_map(width, height, startPoint, difficulty)
    
    return jsonify({
        "message": "Map created successfully",
        "map_id": str(result.inserted_id)
    }), 201

# Get the first map from the database
@routes_blueprint.route('/api/maps/first', methods=['GET'])
def get_first_map_endpoint():
    try:
        # Get the first map
        map_data = get_first_map()
        if not map_data:
            return jsonify({"error": "No maps found"}), 404
        return jsonify(map_data), 200
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
    
@routes_blueprint.route('/api/game', methods=['POST'])
def create_game():
    data = request.get_json()
    username= session.get('username')
    if not username:
        return jsonify({"error": "User not logged in"}), 401
    map = data.get('map')
    difficulty = data.get('difficulty')
    add_game(username, map, difficulty)
    return jsonify({"message": "Game added successfully"}), 201

@routes_blueprint.route('/api/game', methods=['GET'])
def get_game():
    game = session.get('game')
    if not game:
        return jsonify({"error": "No game found"}), 404
    return jsonify(game), 200

@routes_blueprint.route('/api/game/save', methods=['POST'])
def save_game_endpoint():
    if save_game():
        return jsonify({"message": "Game saved successfully"}), 200
    return jsonify({"error": "Failed to save game"}), 500

@routes_blueprint.route('/api/game/delete', methods=['DELETE'])
def delete_game_endpoint():
    if session.get('game'):
        delete_game(session['game'].get('game_id'))
        return jsonify({"message": "Game deleted successfully"}), 200
    return jsonify({"error": "No game found"}), 404

# Troop Management Endpoints

@routes_blueprint.route('/api/troops/types', methods=['GET'])
def get_troop_types_endpoint():
    """Get all available troop types"""
    troop_types = get_troop_types()
    return jsonify(troop_types), 200

@routes_blueprint.route('/api/troops/types/<type_id>', methods=['GET'])
def get_troop_type_endpoint(type_id):
    """Get a specific troop type by its ID"""
    troop_type = get_troop_type(type_id)
    if not troop_type:
        return jsonify({"error": "Troop type not found"}), 404
    return jsonify(troop_type), 200

@routes_blueprint.route('/api/troops', methods=['POST'])
def add_troop_endpoint():
    """Add a new troop to the player's army"""
    username = session.get('username')
    if not username:
        return jsonify({"error": "User not logged in"}), 401
    
    data = request.get_json()
    type_id = data.get('type_id')
    position = data.get('position')
    
    if not type_id or not position:
        return jsonify({"error": "Type ID and position are required"}), 400
    
    success, result = add_troop_to_player(username, type_id, position)
    if not success:
        return jsonify({"error": result}), 400
    
    return jsonify({
        "message": "Troop added successfully",
        "troop": result
    }), 201

@routes_blueprint.route('/api/troops', methods=['GET'])
def get_troops_endpoint():
    """Get all troops for the current player"""
    username = session.get('username')
    if not username:
        return jsonify({"error": "User not logged in"}), 401
    
    troops = get_player_troops(username)
    return jsonify(troops), 200

@routes_blueprint.route('/api/troops/<troop_id>/move', methods=['PUT'])
def move_troop_endpoint(troop_id):
    """Move a troop to a new position"""
    username = session.get('username')
    if not username:
        return jsonify({"error": "User not logged in"}), 401
    
    data = request.get_json()
    position = data.get('position')
    
    if not position:
        return jsonify({"error": "Position is required"}), 400
    
    success, message = update_troop_position(username, troop_id, position)
    if not success:
        return jsonify({"error": message}), 400
    
    return jsonify({
        "message": message
    }), 200

@routes_blueprint.route('/api/troops/<troop_id>/status', methods=['PUT'])
def update_troop_status_endpoint(troop_id):
    """Update a troop's status"""
    username = session.get('username')
    if not username:
        return jsonify({"error": "User not logged in"}), 401
    
    data = request.get_json()
    status = data.get('status')
    
    if not status:
        return jsonify({"error": "Status is required"}), 400
    
    success, message = update_troop_status(username, troop_id, status)
    if not success:
        return jsonify({"error": message}), 400
    
    return jsonify({
        "message": message
    }), 200

@routes_blueprint.route('/api/troops/reset', methods=['POST'])
def reset_troops_endpoint():
    """Reset all troops status to ready (start of turn)"""
    username = session.get('username')
    if not username:
        return jsonify({"error": "User not logged in"}), 401
    
    success, message = reset_troops_status(username)
    if not success:
        return jsonify({"error": message}), 400
    
    return jsonify({
        "message": message
    }), 200