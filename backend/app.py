from flask import Flask, request, jsonify, session
from flask_cors import CORS
import os
import json
from bson import ObjectId
import pymongo
import requests
from datetime import datetime

# MongoDB connection from environment variable
mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = pymongo.MongoClient(mongo_uri)
db = client["civilizationGame"]
users_collection = db["users"]
games_collection = db["games"]
scenarios_collection = db["scenarios"]

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24))

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({"message": "Hello from Flask!"})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})

# Helper function to convert ObjectId to string
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)

# Authentication routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # Basic validation
    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400
    
    # Check if user already exists
    if users_collection.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 400
    
    # Create new user
    user = {
        "username": username,
        "email": email,
        "password_hash": password,  # In a real app, you'd hash this
        "created_at": datetime.now(),
        "last_login": datetime.now()
    }
    
    result = users_collection.insert_one(user)
    return jsonify({"success": True, "user_id": str(result.inserted_id)}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = users_collection.find_one({"username": username})
    
    if not user or user["password_hash"] != password:  # Again, you'd verify the hash
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Update last login
    users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.now()}}
    )
    
    # Set session
    session['user_id'] = str(user["_id"])
    
    return jsonify({
        "success": True,
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"]
        }
    })

@app.route('/api/auth/profile', methods=['GET'])
def get_profile():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = users_collection.find_one({"_id": ObjectId(session['user_id'])})
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "created_at": user["created_at"],
        "last_login": user["last_login"]
    })

# Game routes
@app.route('/api/games', methods=['GET'])
def list_games():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    games = list(games_collection.find({"user_id": ObjectId(session['user_id'])}))
    return JSONEncoder().encode(games), 200, {'Content-Type': 'application/json'}

@app.route('/api/games', methods=['POST'])
def create_game():
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    data = request.get_json()
    scenario_id = data.get('scenario_id')
    name = data.get('name', 'New Game')
    
    # Validate scenario exists
    scenario = scenarios_collection.find_one({"_id": ObjectId(scenario_id)})
    if not scenario:
        return jsonify({"error": "Scenario not found"}), 404
    
    # Create new game
    game = {
        "user_id": ObjectId(session['user_id']),
        "name": name,
        "scenario_id": scenario_id,
        "created_at": datetime.now(),
        "last_saved": datetime.now(),
        "is_autosave": False,
        "cheats_used": [],
        "turn": 1,
        "current_player": "player",
        "game_state": scenario["initial_state"]
    }
    
    result = games_collection.insert_one(game)
    
    return jsonify({
        "success": True,
        "game_id": str(result.inserted_id),
        "game": JSONEncoder().default(game)
    }), 201

@app.route('/api/games/<game_id>', methods=['GET'])
def get_game(game_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    game = games_collection.find_one({
        "_id": ObjectId(game_id),
        "user_id": ObjectId(session['user_id'])
    })
    
    if not game:
        return jsonify({"error": "Game not found"}), 404
    
    return JSONEncoder().encode(game), 200, {'Content-Type': 'application/json'}

@app.route('/api/games/<game_id>/action', methods=['POST'])
def perform_action(game_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    game = games_collection.find_one({
        "_id": ObjectId(game_id),
        "user_id": ObjectId(session['user_id'])
    })
    
    if not game:
        return jsonify({"error": "Game not found"}), 404
    
    data = request.get_json()
    action_type = data.get('type')
    
    # Here we would implement the different action types (move, build, etc.)
    # For now, just a stub
    
    return jsonify({"success": True, "message": f"Action {action_type} processed"}), 200

@app.route('/api/games/<game_id>/endTurn', methods=['POST'])
def end_turn(game_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    game = games_collection.find_one({
        "_id": ObjectId(game_id),
        "user_id": ObjectId(session['user_id'])
    })
    
    if not game:
        return jsonify({"error": "Game not found"}), 404
    
    # Process end of turn (resource calculation, etc.)
    
    # Start AI turn
    ai_actions = process_ai_turn(game)
    
    # Update game state and turn number
    games_collection.update_one(
        {"_id": ObjectId(game_id)},
        {"$set": {
            "current_player": "player",
            "turn": game["turn"] + 1,
            "last_saved": datetime.now(),
        }}
    )
    
    return jsonify({
        "success": True,
        "ai_actions": ai_actions
    }), 200

@app.route('/api/games/<game_id>/cheat', methods=['POST'])
def apply_cheat(game_id):
    if 'user_id' not in session:
        return jsonify({"error": "Not authenticated"}), 401
    
    game = games_collection.find_one({
        "_id": ObjectId(game_id),
        "user_id": ObjectId(session['user_id'])
    })
    
    if not game:
        return jsonify({"error": "Game not found"}), 404
    
    data = request.get_json()
    cheat_code = data.get('cheat_code')
    target = data.get('target')
    
    # Process the cheat code
    result = process_cheat(game, cheat_code, target)
    
    # Add cheat to used cheats if successful
    if result["success"] and cheat_code not in game["cheats_used"]:
        games_collection.update_one(
            {"_id": ObjectId(game_id)},
            {"$push": {"cheats_used": cheat_code}}
        )
    
    return jsonify(result), 200

# AI functions
def process_ai_turn(game):
    # This would call the GroQ API and process AI decisions
    # For now, return a simple mock response
    
    actions = [
        {
            "action_id": 1,
            "type": "moveUnit",
            "unitId": "ai_unit1",
            "path": [
                {"x": 42, "y": 35},
                {"x": 43, "y": 35}
            ],
            "state_before": {},
            "state_after": {},
            "timestamp": datetime.now().isoformat()
        },
        {
            "action_id": 2,
            "type": "endTurn",
            "state_before": {},
            "state_after": {},
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    return actions

def process_cheat(game, cheat_code, target):
    # Process different cheat codes
    if cheat_code == "maila_igo" and target["type"] == "city":
        # Find the city in player's cities
        city_found = False
        for city in game["game_state"]["player"]["cities"]:
            if city["id"] == target["id"]:
                city_found = True
                old_population = city["population"]
                city["population"] += 1
                
                # Update in database
                games_collection.update_one(
                    {"_id": game["_id"]},
                    {"$set": {
                        f"game_state.player.cities.$[city].population": city["population"]
                    }},
                    array_filters=[{"city.id": target["id"]}]
                )
                
                return {
                    "success": True,
                    "message": "Hiria maila bat igo da",
                    "affected_entity": {
                        "type": "city",
                        "id": target["id"],
                        "changes": {
                            "population": {"before": old_population, "after": city["population"]}
                        }
                    },
                    "game_state": game["game_state"]
                }
        
        if not city_found:
            return {
                "success": False,
                "message": "City not found",
                "game_state": game["game_state"]
            }
    
    return {
        "success": False,
        "message": "Unknown cheat code or invalid target",
        "game_state": game["game_state"]
    }

# Scenarios
@app.route('/api/scenarios', methods=['GET'])
def list_scenarios():
    scenarios = list(scenarios_collection.find())
    return JSONEncoder().encode(scenarios), 200, {'Content-Type': 'application/json'}

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)