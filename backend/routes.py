from flask import Blueprint, request, jsonify, session
from database import add_user, find_user, update_user_score, get_all_users
import hashlib

routes_blueprint = Blueprint('routes', __name__)

@routes_blueprint.route('/proba', methods=['GET'])
def proba():
    return "Kaixoooo"

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
    
    return jsonify({
        "message": "Login successful",
        "user": {
            "username": user['username'],
            "score": user['score'],
            "level": user['level']
        }
    }), 200

@routes_blueprint.route('/api/logout', methods=['POST'])
def logout():
    # Clear the session
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

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

@routes_blueprint.route('/api/users/<username>/score', methods=['PUT'])
def update_score(username):
    data = request.get_json()
    score = data.get('score')
    
    if score is None:
        return jsonify({"error": "Score is required"}), 400
    
    # Check if user exists
    user = find_user(username)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Update user's score
    update_user_score(username, score)
    return jsonify({"message": "Score updated successfully"}), 200

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
