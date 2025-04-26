from flask import Flask, session
from flask_cors import CORS
import os
from routes import routes_blueprint
import secrets
from database import init_db, close_db

# Initialize Flask app
app = Flask(__name__)

# Set a strong secret key for session encryption
app.secret_key = secrets.token_hex(16)
# Configure session to be secure and with appropriate timeout
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 7200  # 2 hours session timeout

# Enable CORS
CORS(app, supports_credentials=True)

# Register routes
app.register_blueprint(routes_blueprint)

# Register database teardown
app.teardown_appcontext(close_db)

# Initialize database
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
