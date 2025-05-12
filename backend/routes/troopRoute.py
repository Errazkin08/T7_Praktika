from flask import Blueprint, request, jsonify, session
import logging
from database import (get_troop_types, get_troop_type, add_troop_to_player, 
                     get_player_troops, update_troop_position, update_troop_status, 
                     reset_troops_status)

# Set up logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint for troop routes
troop_blueprint = Blueprint('troop', __name__)

@troop_blueprint.route('/api/troops/types', methods=['GET'])
def get_troop_types_endpoint():
    """Get all available troop types"""
    troop_types = get_troop_types()
    return jsonify(troop_types), 200

@troop_blueprint.route('/api/troops/types/<type_id>', methods=['GET'])
def get_troop_type_endpoint(type_id):
    """Get a specific troop type by its ID"""
    logger.info(f"Received request for troop type with ID: {type_id}")
    
    # Extract position from query parameters if provided
    position_param = request.args.get('position')
    position = None
    
    if position_param:
        try:
            logger.info(f"Position parameter received: {position_param}")
            import json
            position = json.loads(position_param)
            logger.info(f"Parsed position: {position}")
        except Exception as e:
            logger.error(f"Error parsing position parameter: {str(e)}")
            position = [0, 0]  # Default position
    else:
        logger.info("No position parameter provided, using default [0, 0]")
        position = [0, 0]  # Default position
    
    try:
        logger.info(f"Calling database function get_troop_type with ID: {type_id} and position: {position}")
        troop_type = get_troop_type(type_id, position)
        
        logger.info(f"Database returned troop_type: {troop_type}")
        
        if not troop_type:
            logger.warning(f"Troop type with ID {type_id} not found in database")
            return jsonify({"error": "Troop type not found"}), 404
        
        logger.info(f"Successfully returning troop type: {troop_type}")
        return jsonify(troop_type), 200
    
    except Exception as e:
        logger.error(f"Error retrieving troop type {type_id}: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@troop_blueprint.route('/api/troops', methods=['POST'])
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

@troop_blueprint.route('/api/troops', methods=['GET'])
def get_troops_endpoint():
    """Get all troops for the current player"""
    username = session.get('username')
    if not username:
        return jsonify({"error": "User not logged in"}), 401
    
    troops = get_player_troops(username)
    return jsonify(troops), 200

@troop_blueprint.route('/api/troops/<troop_id>/move', methods=['PUT'])
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

@troop_blueprint.route('/api/troops/<troop_id>/status', methods=['PUT'])
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

@troop_blueprint.route('/api/troops/reset', methods=['POST'])
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
