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
    
    # Llamar a la función iaDeitu
    try:
        result = iaDeitu(prompt, simplified_game_state)
        current_app.logger.info(f"IA response: {result}")
        
        # Eliminar comillas al principio y al final si existen
        if isinstance(result, str):
            if result.startswith('"') and result.endswith('"'):
                result = result[1:-1]
            
            # Intentar parsear el resultado como JSON
            try:
                # Parsear el string a un objeto Python
                parsed_result = json.loads(result)
                return jsonify(parsed_result)
            except json.JSONDecodeError as e:
                current_app.logger.error(f"Error parsing AI response: {e}")
                # Si falla el parseo, devolver el resultado como texto
                return jsonify({"result": result})
        
        # Si no es un string, devolver directamente
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"AI processing error: {str(e)}"}), 500
