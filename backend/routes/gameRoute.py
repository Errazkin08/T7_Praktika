from flask import Blueprint, request, jsonify, session
from database import (add_game, delete_game, save_game, get_game_by_id_from_db)
from bson import ObjectId
import datetime
import traceback

# Create blueprint for game routes
game_blueprint = Blueprint('game', __name__)

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

def process_research(game):
    """Process technology research for both player and AI"""
    players = ['player', 'ia']
    
    for player_type in players:
        if player_type not in game:
            continue
            
        # Check each city for research in progress
        for city in game[player_type].get('cities', []):
            research_completed = False
            tech_id = None
            tech_name = None
            
            # Check city's research field (for backwards compatibility)
            if 'research' in city and city['research'].get('current_technology'):
                city['research']['turns_remaining'] -= 1
                
                # Check if research is complete
                if city['research']['turns_remaining'] <= 0:
                    tech_id = city['research']['current_technology']
                    research_completed = True
                    
                    # Reset the research
                    city['research']['current_technology'] = None
                    city['research']['turns_remaining'] = 0
            
            # Check library building for research
            if 'buildings' in city:
                for building in city['buildings']:
                    # Skip string-type buildings
                    if isinstance(building, str):
                        continue
                        
                    # Check if it's a library with research
                    if (building.get('type_id') == 'library' or building.get('name', '').lower() == 'library') and \
                       'production' in building and building['production'] and building['production'].get('current_technology'):
                        
                        # Decrease turns remaining
                        building['production']['turns_remaining'] -= 1
                        
                        # Check if research is complete
                        if building['production']['turns_remaining'] <= 0:
                            tech_id = building['production']['current_technology']
                            tech_name = building['production'].get('technology_name', tech_id)
                            research_completed = True
                            
                            # Reset the production
                            building['production'] = None
                            
                            # Also reset city research for backwards compatibility
                            if 'research' in city:
                                city['research']['current_technology'] = None
                                city['research']['turns_remaining'] = 0
            
            # If research was completed, add the technology to the player's technologies
            if research_completed and tech_id:
                # Initialize technologies array if it doesn't exist
                if 'technologies' not in game[player_type]:
                    game[player_type]['technologies'] = []
                
                # Check if the technology is already researched
                already_researched = False
                for tech in game[player_type]['technologies']:
                    if (isinstance(tech, str) and tech == tech_id) or \
                       (isinstance(tech, dict) and tech.get('id') == tech_id):
                        already_researched = True
                        break
                
                # Add the technology if not already researched
                if not already_researched:
                    # Get the full technology type from the database
                    from database import get_technology_type
                    tech_data = get_technology_type(tech_id)
                    
                    if tech_data:
                        game[player_type]['technologies'].append(tech_data)
                    else:
                        # Fallback to just the ID if tech data not found
                        game[player_type]['technologies'].append(tech_id)
    
    return game

def end_turn(game):
    # Process research progress
    game = process_research(game)
    
    return game

@game_blueprint.route('/api/game', methods=['POST'])
def create_game():
    try:
        data = request.get_json()
        username = session.get('username')
        if not username:
            return jsonify({"error": "User not logged in"}), 401
        
        map_id = data.get('map')
        difficulty = data.get('difficulty')
        game_name = data.get('name', "New Game")  # Get name from request, default if not provided
        
        # Make sure to convert map_id to string if it's an ObjectId
        if map_id and isinstance(map_id, ObjectId):
            map_id = str(map_id)
            
        # Create the game with the provided name
        result = add_game(username, map_id, difficulty, game_name)
        
        if result:
            return jsonify({"message": "Game added successfully"}), 201
        else:
            return jsonify({"error": "Failed to create game"}), 500
    except Exception as e:
        print(f"Error creating game: {e}")
        return jsonify({"error": str(e)}), 500

@game_blueprint.route('/api/game', methods=['GET'])
def get_game():
    game = session.get('game')
    if not game:
        return jsonify({"error": "No game found"}), 404
    return jsonify(game), 200

@game_blueprint.route('/api/current-game', methods=['GET'])
def get_current_game():
    """
    Get the current game from the session.
    """
    try:
        if 'username' not in session or not session['username']:
            return jsonify({"error": "User not logged in"}), 401
            
        if 'game' not in session or not session['game']:
            return jsonify({"error": "No active game in session"}), 404
            
        # Return the game from the session directly
        return jsonify(session['game'])
    except Exception as e:
        print(f"Error in get_current_game: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@game_blueprint.route('/api/game/save', methods=['POST'])
def save_game_endpoint():
    if save_game():
        return jsonify({"message": "Game saved successfully"}), 200
    return jsonify({"error": "Failed to save game"}), 500

@game_blueprint.route('/api/current-game/save', methods=['POST'])
def save_current_game_session():
    """Endpoint to save the current game session state to the database"""
    try:
        if 'username' not in session:
            return jsonify({"success": False, "message": "User not logged in"}), 401
            
        if 'game' not in session:
            return jsonify({"success": False, "message": "No active game in session"}), 400
        
        # Save the game from session to database
        from database import save_game
        result = save_game()
        
        if result:
            # Confirm the save was successful
            return jsonify({
                "success": True, 
                "message": "Game saved successfully", 
                "game_id": session['game'].get('game_id')
            })
        else:
            return jsonify({"success": False, "message": "Failed to save game"}), 500
    except Exception as e:
        print(f"Exception in save_current_game_session: {str(e)}")
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@game_blueprint.route('/api/update-game-session', methods=['POST'])
def update_game_session():
    """Update the game data in the session"""
    try:
        if 'user' not in session or session['user'] is None:
            return jsonify({"error": "User not logged in"}), 401
        
        # Get the updated game data from the request
        updated_game = request.get_json()
        if not updated_game:
            return jsonify({"error": "No game data provided"}), 400
        
        # Ensure the data stored in session is clean
        processed_game_data = convert_bson_types(updated_game)
        session['game'] = processed_game_data
        
        # Mark session as modified if necessary, Flask usually does this automatically
        session.modified = True 
        
        return jsonify({"message": "Game session updated successfully"}), 200
    except Exception as e:
        print(f"Error updating game session: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@game_blueprint.route('/api/game/delete', methods=['DELETE'])
def delete_game_endpoint():
    if session.get('game'):
        delete_game(session['game'].get('game_id'))
        return jsonify({"message": "Game deleted successfully"}), 200
    return jsonify({"error": "No game found"}), 404

@game_blueprint.route('/api/games/<game_id>', methods=['GET'])
def get_game_by_id(game_id):
    """Get a specific game by its ID"""
    try:
        if 'username' not in session: # Check for username in session
            return jsonify({"error": "Unauthorized - User not logged in"}), 401

        current_username = session['username']
        
        # Fetch the game document using the get_game_by_id_from_db function
        # This function should handle finding the game by its game_id
        # and optionally verify ownership if username is passed.
        game_doc = get_game_by_id_from_db(game_id, username=current_username)

        if game_doc:
            # Ensure the game document is fully processed for BSON types
            processed_game = convert_bson_types(game_doc)
            
            # Update the session with the loaded game
            session['game'] = processed_game 
            session.modified = True # Explicitly mark session as modified
            
            return jsonify(processed_game)
        else:
            # Game not found or does not belong to the user
            return jsonify({"error": "Game not found or access denied"}), 404
    except Exception as e:
        # Log the full error for debugging
        print(f"Error in get_game_by_id for game_id {game_id}: {e}")
        print(traceback.format_exc())
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
