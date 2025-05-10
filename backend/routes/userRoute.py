from flask import Blueprint, request, jsonify, session
from database import (add_user, find_user, get_all_users, update_user_login, get_user_games, get_db)
import hashlib
from bson import ObjectId
import datetime

# Create blueprint for user routes
user_blueprint = Blueprint('user', __name__)

# Helper functions
def convert_bson_types(obj):
    if isinstance(obj, list):
        return [convert_bson_types(x) for x in obj]
    if isinstance(obj, dict):
        return {k: convert_bson_types(v) for k, v in obj.items()}
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return obj

#Register a new user
@user_blueprint.route('/api/users', methods=['POST'])
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
@user_blueprint.route('/api/login', methods=['POST'])
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
@user_blueprint.route('/api/logout', methods=['POST'])
def logout():
    # Clear the session
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

# Check if user is logged in
@user_blueprint.route('/api/session', methods=['GET'])
def check_session():
    if 'username' in session:
        user = find_user(session['username'])
        if user:
            return jsonify({
                "authenticated": True,
                "user": {
                    "username": user['username'],
                    "score": user.get('score', 0),
                    "level": user.get('level', 1)
                }
            }), 200
    return jsonify({"authenticated": False}), 401

# Get user information from its username
@user_blueprint.route('/api/users/<username>', methods=['GET'])
def get_user(username):
    # Fetch user from database
    user = find_user(username)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "username": user['username'],
        "score": user.get('score', 0),
        "level": user.get('level', 1)
    }), 200

#Get all users from the database
@user_blueprint.route('/api/users/', methods=['GET'])
def get_all_users_endpoint():
    try:
        # Query all users from the database
        users = get_all_users()
        if not users or len(users) == 0:
            return jsonify({"message": "No users found"}), 404
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@user_blueprint.route('/api/user/games', methods=['GET'])
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

@user_blueprint.route('/api/user/games/<game_id>', methods=['DELETE'])
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
