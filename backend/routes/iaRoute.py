from flask import Blueprint, request, jsonify, session, current_app
import json
from IAProba import iaDeitu


# Create blueprint for IA routes
ia_blueprint = Blueprint('ia', __name__)

@ia_blueprint.route('/api/ai/action', methods=['POST'])
def ai_action():
    """
    Endpoint para obtener acciones de la IA basadas en el estado del juego
    """
    # Verificar si el usuario está autenticado
    user = session.get('user')
    if not user:
        return jsonify({"error": "User not logged in"}), 401
    
    # Obtener datos de la solicitud
    data = request.json
    
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    # Extraer los parámetros para la función iaDeitu
    prompt = data.get('prompt', '')
    game_state = data.get('game_state')
    
    # Extraer solo los campos necesarios para la IA
    simplified_game_state = {
        "ia": game_state.get("ia", {}),
        "difficulty": game_state.get("difficulty", ""),
        "map_data": game_state.get("map_data", {})
    }
    
    # Opcional: añadir identificador de juego para manejar múltiples conversaciones
    game_id = game_state.get("id", "default_game")
    
    # Llamar a la función iaDeitu
    try:
        # El contexto de la conversación se maneja dentro de iaDeitu ahora
        result = iaDeitu(prompt, simplified_game_state)
        current_app.logger.info(f"IA response raw: {result}")
        
        if isinstance(result, str):
            # Extract JSON content by finding the first { and last }
            first_brace_index = result.find('{')
            last_brace_index = result.rfind('}')
            
            if first_brace_index != -1 and last_brace_index != -1 and first_brace_index < last_brace_index:
                # Extract only the JSON part
                cleaned_result = result[first_brace_index:last_brace_index + 1]
                current_app.logger.info(f"Extracted JSON: {cleaned_result[:100]}...")
                
                try:
                    # Parse the extracted JSON
                    parsed_result = json.loads(cleaned_result)
                    return jsonify(parsed_result)
                except json.JSONDecodeError as e:
                    current_app.logger.error(f"Error parsing extracted JSON: {e}")
                    return jsonify({"error": "Invalid JSON format", "extracted_content": cleaned_result})
            else:
                # If no JSON structure found, try original response
                current_app.logger.warning("No JSON structure found in response, trying original")
                try:
                    parsed_result = json.loads(result)
                    return jsonify(parsed_result)
                except json.JSONDecodeError:
                    current_app.logger.error("Could not parse response as JSON")
                    return jsonify({"result": result})
        
        # If result is not a string, return directly
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"AI processing error: {str(e)}")
        return jsonify({"error": f"AI processing error: {str(e)}"}), 500
