from flask import Blueprint, request, jsonify, session
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
    game_state = session.get('game')
    rules = data.get('rules', None)
    
    # Llamar a la función iaDeitu
    try:
        result = iaDeitu(prompt, game_state, rules)
        
        # Devolver el resultado como JSON
        return jsonify({
            "result": result
        })
    except Exception as e:
        return jsonify({"error": f"AI processing error: {str(e)}"}), 500
