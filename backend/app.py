from flask import Flask, jsonify, request, session
from flask_cors import CORS
from routes import routes_blueprint
from database import init_db, close_db
import os
from bson import ObjectId
import datetime
import json

# Custom JSON encoder to handle MongoDB ObjectId and datetime
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)

app = Flask(__name__)
# Set a secret key for session security
app.secret_key = os.environ.get('SECRET_KEY', 'devkey_please_change_in_production')
# Configure the custom JSON encoder
app.json_encoder = MongoJSONEncoder

# Enable CORS with credentials
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Register database hooks
@app.before_request
def before_request():
    # Check if the session needs to be initialized
    if 'username' not in session and 'user' not in session:
        # Initialize session with empty values
        session['username'] = None
        session['user'] = None

# Convert ObjectID to string for all sessions
@app.after_request
def after_request(response):
    # Manually clean any ObjectId in session to avoid serialization issues
    if 'game' in session and session['game'] is not None:
        # Convert ObjectId to string in game
        session_game = session['game']
        if isinstance(session_game, dict):
            if 'map_id' in session_game and isinstance(session_game['map_id'], ObjectId):
                session_game['map_id'] = str(session_game['map_id'])
            # Recursively check for other ObjectIds in the game object
    return response

@app.route('/api/current-game', methods=['GET'])
def get_current_game():
    if 'game' in session:
        return jsonify(session['game'])
    return jsonify(None), 404

@app.route('/api/current-game/save', methods=['POST'])
def save_current_game_session():
    """Endpoint to save the current game session state without full game saving"""
    if 'game' in session:
        from database import save_game
        result = save_game()
        if result:
            return jsonify({"success": True, "message": "Game state saved"})
        return jsonify({"success": False, "message": "Failed to save game state"}), 500
    return jsonify({"success": False, "message": "No active game"}), 404

@app.teardown_appcontext
def teardown_db(exception):
    close_db(exception)

# Initialize the database
with app.app_context():
    init_db()

# Register blueprints
app.register_blueprint(routes_blueprint)

# Error handling
@app.errorhandler(500)
def handle_500_error(e):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def handle_404_error(e):
    return jsonify({"error": "Resource not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
