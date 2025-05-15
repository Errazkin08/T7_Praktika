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
    
    # Extraer los campos necesarios para la IA incluyendo fog of war
    simplified_game_state = {
        "ia": game_state.get("ia", {}),
        "player": {
            "units": game_state.get("player", {}).get("units", [])
        },
        "difficulty": game_state.get("difficulty", ""),
        "map_data": game_state.get("map_data", {}),
        "map_size": game_state.get("map_size", {}),
        "turn": game_state.get("turn", 1)
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

@ia_blueprint.route('/api/ai/negotiate', methods=['POST'])
def ai_negotiate():
    """
    Endpoint para negociar paz/intercambio de recursos con la IA.
    """
    user = session.get('user')
    if not user:
        return jsonify({"error": "User not logged in"}), 401

    data = request.json
    if not data or "offer" not in data or "game_state" not in data:
        return jsonify({"error": "Missing offer or game_state"}), 400

    offer = data["offer"]
    game_state = data["game_state"]

    # Construir prompt para negociación
    negotiation_prompt = f"""
Eres la IA de un juego de estrategia por turnos. El jugador te propone una negociación de paz/intercambio de recursos.
Oferta recibida (formato JSON):
{json.dumps(offer)}
Estado del juego relevante (recursos, ciudades, turno actual):
{json.dumps({
    "player_resources": game_state.get("player", {}).get("resources", {}),
    "ai_resources": game_state.get("ia", {}).get("resources", {}),
    "turn": game_state.get("turn", 1)
})}
Debes responder SOLO con un JSON con una de estas opciones:
- Si aceptas la oferta: {{ "accepted": true, "ceasefire_turns": N }}
- Si rechazas pero propones una contraoferta: {{ "accepted": false, "counter_offer": {{...misma estructura que la oferta...}} }}
- Si rechazas sin contraoferta: {{ "accepted": false }}
NO EXPLIQUES NADA, SOLO EL JSON.
"""

    try:
        from IAProba import iaDeitu
        result = iaDeitu(negotiation_prompt, game_state)
        # Extraer solo el JSON de la respuesta
        if isinstance(result, str):
            first_brace = result.find('{')
            last_brace = result.rfind('}')
            if first_brace != -1 and last_brace != -1 and first_brace < last_brace:
                cleaned = result[first_brace:last_brace+1]
                try:
                    parsed = json.loads(cleaned)
                    # --- NUEVO: Si la oferta es aceptada, actualiza los recursos y el estado de paz en la sesión ---
                    if parsed.get("accepted"):
                        # Actualiza recursos de ambos jugadores
                        player = game_state.get("player", {})
                        ia = game_state.get("ia", {})
                        offer_data = offer

                        # Sumar/restar recursos según la oferta aceptada
                        for res in ["food", "gold", "wood", "iron", "stone"]:
                            player_amt = offer_data.get("player", {}).get(res, 0) or 0
                            ia_amt = offer_data.get("ai", {}).get(res, 0) or 0
                            # El jugador da a la IA
                            player.setdefault("resources", {}).setdefault(res, 0)
                            ia.setdefault("resources", {}).setdefault(res, 0)
                            player["resources"][res] = max(0, player["resources"][res] - player_amt + ia_amt)
                            ia["resources"][res] = max(0, ia["resources"][res] - ia_amt + player_amt)

                        # Guardar los cambios en la sesión
                        if "game" in session and session["game"]:
                            session_game = session["game"]
                            # Actualiza recursos en la sesión
                            if "player" in session_game:
                                session_game["player"]["resources"] = player["resources"]
                            if "ia" in session_game:
                                session_game["ia"]["resources"] = ia["resources"]
                            # Añade el estado de paz
                            ceasefire_turns = parsed.get("ceasefire_turns") or offer.get("ceasefireTurns") or offer.get("ceasefire_turns") or 0
                            session_game["ceasefire_turns"] = int(ceasefire_turns)
                            session_game["ceasefire_active"] = True
                            session["game"] = session_game

                        parsed["resources_updated"] = True
                        parsed["ceasefire_turns"] = int(parsed.get("ceasefire_turns") or offer.get("ceasefireTurns") or 0)
                    return jsonify(parsed)
                except Exception:
                    return jsonify({"error": "Invalid JSON from LLM", "raw": cleaned})
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Negotiation AI error: {str(e)}"}), 500
