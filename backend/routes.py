from flask import Blueprint, request, jsonify, session
from database import add_user, find_user, update_user_score, get_all_users, update_user_login, add_map, get_first_map
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
