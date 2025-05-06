from flask import Blueprint, request, jsonify, session
from database import (add_user, find_user, save_game, get_all_users, update_user_login, add_map, get_first_map, add_game, delete_game,
                     get_troop_types, get_troop_type, add_troop_to_player, get_player_troops, update_troop_position,
                     update_troop_status, reset_troops_status, get_all_maps, delete_map, get_map, get_user_games, get_db)
import hashlib
from bson import ObjectId
import json

routes_blueprint = Blueprint('routes', __name__)

# Helper function to convert ObjectId to string
def serialize_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

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
    try:
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
        
        # Store user in session - use only simple data types
        session['username'] = user['username']
        
        if '_id' in user:
            user_id = str(user['_id'])  # Convert ObjectId to string
        else:
            user_id = username  # Fallback to username if no _id
            
        session['user_id'] = user_id
        
        # Create a safe user object for session
        session['user'] = {
            "username": user['username']
        }
        
        # Update last login time
        update_user_login(user['username'])
        
        # Return safe user information
        return jsonify({
            "message": "Login successful",
            "user": {
                "username": user['username'],
                "score": user.get('score', 0),
                "level": user.get('level', 1)
            }
        }), 200
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({"error": "An error occurred during login"}), 500

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
    
@routes_blueprint.route('/api/maps', methods=['GET'])
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

@routes_blueprint.route('/api/maps/<map_id>', methods=['DELETE'])
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

@routes_blueprint.route('/api/maps/<map_id>', methods=['GET'])
def get_map_edpoint(map_id):
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
    
@routes_blueprint.route('/api/game', methods=['POST'])
def create_game():
    try:
        data = request.get_json()
        username = session.get('username')
        if not username:
            return jsonify({"error": "User not logged in"}), 401
        
        map_id = data.get('map')
        difficulty = data.get('difficulty')
        
        # Make sure to convert map_id to string if it's an ObjectId
        if map_id and isinstance(map_id, ObjectId):
            map_id = str(map_id)
            
        # Create the game
        result = add_game(username, map_id, difficulty)
        
        if result:
            return jsonify({"message": "Game added successfully"}), 201
        else:
            return jsonify({"error": "Failed to create game"}), 500
    except Exception as e:
        print(f"Error creating game: {e}")
        return jsonify({"error": str(e)}), 500

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

@routes_blueprint.route('/api/user/games', methods=['GET'])
def get_user_games_endpoint():
    """Get all games for the current user"""
    try:
        # Check if user is logged in
        if 'username' not in session:
            return jsonify({"error": "User not logged in"}), 401
        
        username = session['username']
        games = get_user_games(username)
        
        # Convert ObjectId to string for JSON serialization
        for game in games:
            if '_id' in game:
                game['_id'] = str(game['_id'])
        
        return jsonify(games), 200
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@routes_blueprint.route('/api/user/games/<game_id>', methods=['DELETE'])
def delete_user_game_endpoint(game_id):
    """Delete a specific game for the current user"""
    try:
        # Check if user is logged in
        if 'username' not in session:
            return jsonify({"error": "User not logged in"}), 401
        
        username = session['username']
        print(f"Attempting to delete game {game_id} for user {username}")
        
        # Get the database connection
        db = get_db()
        
        # Get the game to verify ownership
        game = db.games.find_one({"game_id": game_id})
        print(f"Found game: {game is not None}")
        
        if not game:
            # Try to find with different ID formats
            try:
                # Try as string first
                print(f"Trying to find game with string ID: {game_id}")
                game = db.games.find_one({"game_id": str(game_id)})
                
                # Then try as integer
                if not game:
                    print(f"Trying to find game with numeric ID")
                    numeric_id = int(game_id)
                    game = db.games.find_one({"game_id": numeric_id})
                    if game:
                        game_id = numeric_id  # Update game_id for deletion
                        print(f"Found game with numeric ID: {numeric_id}")
            except (ValueError, TypeError) as e:
                print(f"Error converting game_id: {str(e)}")
                
            # If still not found, return 404
            if not game:
                print("Game not found after all attempts")
                return jsonify({"error": "Game not found"}), 404
        
        # Print game details for debugging
        print(f"Game details: ID={game.get('game_id')}, Owner={game.get('username')}")
        
        # Verify that the game belongs to the current user
        if game.get("username") != username:
            return jsonify({"error": "Not authorized to delete this game"}), 403
        
        # Delete the game directly from database to avoid any issues
        try:
            print(f"Attempting direct deletion of game_id: {game_id}")
            result = db.games.delete_one({"game_id": game_id})
            if result.deleted_count > 0:
                print(f"Game successfully deleted with direct DB call")
                return jsonify({"message": "Game deleted successfully"}), 200
            
            # Try different format just in case
            print(f"Trying deletion with alternate formats")
            if isinstance(game_id, str):
                try:
                    numeric_id = int(game_id)
                    result = db.games.delete_one({"game_id": numeric_id})
                    if result.deleted_count > 0:
                        print(f"Game deleted with numeric ID")
                        return jsonify({"message": "Game deleted successfully (numeric ID)"}), 200
                except ValueError:
                    pass
            
            # If we get here, deletion failed
            print("Failed to delete game after multiple attempts")
            return jsonify({"error": "Failed to delete game"}), 500
            
        except Exception as delete_error:
            print(f"Exception during direct deletion: {str(delete_error)}")
            return jsonify({"error": f"Database error: {str(delete_error)}"}), 500
    except Exception as e:
        print(f"Exception in delete_user_game_endpoint: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

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