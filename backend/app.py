from flask import Flask
from flask_cors import CORS  # Import CORS
from routes import routes_blueprint
from database import init_db, close_db

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})

# Register routes
app.register_blueprint(routes_blueprint)

# Register database teardown
app.teardown_appcontext(close_db)

# Initialize database
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
