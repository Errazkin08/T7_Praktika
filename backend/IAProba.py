#!/usr/bin/env python3
import requests
import time
import json
import os
from typing import Dict, Optional, Any, List
from dotenv import load_dotenv

class GroqAPIClient:
    """Cliente para realizar llamadas a la API de Groq con manejo de errores y cambio de modelos."""
    
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    # Lista de modelos disponibles en Groq (agrega o quita según necesidad)
    MODELS = [
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "compound-beta-mini",
        "compound-beta",
        ""
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el cliente de Groq API.
        
        Args:
            api_key: Clave de API de Groq. Si no se proporciona, se intentará
                     obtener de la variable de entorno GROQ_API_KEY.
        """
        # Cargar variables de entorno desde el archivo .env
        load_dotenv()
        
        # Usar la API key proporcionada o buscarla en las variables de entorno
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("API key debe ser proporcionada o configurada en la variable de entorno GROQ_API_KEY")
                
        self.current_model_index = 0
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        # Inicializar el historial de conversación
        self.conversation_history = []
        print(f"Cliente inicializado. Modelo inicial: {self.current_model}")
    
    @property
    def current_model(self) -> str:
        """Obtiene el modelo actual que se está utilizando."""
        return self.MODELS[self.current_model_index]
    
    def rotate_model(self) -> str:
        """Cambia al siguiente modelo disponible y devuelve su nombre."""
        self.current_model_index = (self.current_model_index + 1) % len(self.MODELS)
        print(f"Cambiando al modelo: {self.current_model}")
        return self.current_model
    
    def set_system_instructions(self, instructions: str) -> None:
        """Establece las instrucciones del sistema como primer mensaje en el historial de conversación."""
        # Limpiar el historial actual y establecer el mensaje del sistema
        self.conversation_history = [
            {"role": "system", "content": instructions}
        ]
        print("Instrucciones del sistema establecidas en el historial de conversación")
    
    def call_api(self, prompt: str = None, temperature: float = 0.4) -> Dict[str, Any]:
        """
        Realiza una llamada a la API de Groq con manejo de errores.
        
        Args:
            prompt: El texto del prompt a enviar (opcional si ya hay historial).
            temperature: Temperatura para la generación (0.0 - 1.0).
            
        Returns:
            Respuesta de la API en formato diccionario.
        """
        # Si se proporciona un nuevo prompt, agregarlo al historial
        if prompt:
            self.conversation_history.append({"role": "user", "content": prompt})
        
        # Asegurar que hay mensajes para enviar
        if not self.conversation_history:
            raise ValueError("No hay mensajes en el historial de conversación para enviar")
        
        payload = {
            "model": self.current_model,
            "messages": self.conversation_history,
            "temperature": temperature
        }
        
        retries = 0
        while retries < len(self.MODELS):  # Intentar con todos los modelos si es necesario
            try:
                print(f"Enviando solicitud a {self.current_model} con {len(self.conversation_history)} mensajes")
                response = requests.post(
                    self.BASE_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=30
                )
                
                # Si la respuesta es exitosa, devolver los datos
                if response.status_code == 200:
                    data = response.json()
                    print(f"Respuesta exitosa recibida (tokens: {data.get('usage', {}).get('total_tokens', 'N/A')})")
                    
                    # Guardar la respuesta del asistente en el historial
                    if "choices" in data and len(data["choices"]) > 0:
                        self.conversation_history.append({
                            "role": "assistant", 
                            "content": data["choices"][0]["message"]["content"]
                        })
                        
                        # Limitar el historial si es necesario (mantener sistema + últimos 4 pares)
                        if len(self.conversation_history) > 9:  # sistema + 4 pares
                            # Mantener el mensaje del sistema
                            system_msg = self.conversation_history[0] if self.conversation_history[0]["role"] == "system" else None
                            # Mantener los últimos 8 mensajes (4 pares)
                            recent_msgs = self.conversation_history[-8:]
                            # Reconstruir el historial
                            self.conversation_history = ([system_msg] if system_msg else []) + recent_msgs
                    
                    retries = 0
                    return data
                
                # Manejar errores comunes
                error_info = response.json() if response.content else {"error": {"message": "Error desconocido"}}
                error_message = error_info.get("error", {}).get("message", "Error desconocido")
                
                if response.status_code == 429:  # Rate limit o límite de tokens
                    print(f"Error 429: {error_message}")
                    
                    # Si se alcanzó el límite, cambiar de modelo
                    if "rate limit" in error_message.lower() or "token limit" in error_message.lower():
                        self.rotate_model()
                        payload["model"] = self.current_model
                        retries += 1
                        continue
                    
                    retries += 1
                    
                elif response.status_code in (400, 401, 403):
                    print(f"Error {response.status_code}: {error_message}")
                    raise Exception(f"Error en la API: {error_message}")
                    
                else:
                    print(f"Error {response.status_code}: {error_message}. Cambiando de modelo.")
                    self.rotate_model()
                    payload["model"] = self.current_model
                    retries += 1
                    
            except (requests.RequestException, json.JSONDecodeError) as e:
                print(f"Error de conexión: {str(e)}")
                time.sleep(1)
                retries += 1
                self.rotate_model()
                payload["model"] = self.current_model
        
        # Si se agotaron todos los reintentos
        raise Exception("Se agotaron todos los reintentos con todos los modelos disponibles.")
    
    def run_call(self, prompt: str = None, system_instructions: str = None) -> str:
        """
        Ejecuta una llamada a la API con manejo del historial de conversación.
        
        Args:
            prompt: El texto del prompt a enviar (opcional si continuamos conversación).
            system_instructions: Instrucciones del sistema (solo necesario en la primera llamada).
            
        Returns:
            Contenido de la respuesta.
        """
        try:
            # Si se proporcionan instrucciones del sistema, establecer el contexto
            if system_instructions:
                self.set_system_instructions(system_instructions)
            
            # Hacer la llamada a la API
            response = self.call_api(prompt)
            
            # Extraer y mostrar la respuesta
            if response and "choices" in response and len(response["choices"]) > 0:
                message = response["choices"][0]["message"]
                content = message.get("content", "").strip()
                
                print(content)
                return content
                
        except Exception as e:
            print(f"Error en la llamada #{str(e)}") 
            return ""

def filter_game_state(game_state: dict) -> dict:
    """
    Filters the game state to include only essential data, significantly reducing tokens.
    
    Args:
        game_state: Complete game state.
        
    Returns:
        Minimized game state with only necessary fields.
    """
    if not game_state:
        return {}
    
    # Extract map dimensions for quick reference
    map_width = game_state.get("map_size", {}).get("width", 0)
    map_height = game_state.get("map_size", {}).get("height", 0)
    
    # Get AI fog of war grid
    ai_fog_grid = game_state.get("ia", {}).get("fog_grid", [])
    
    # Create optimized fog_of_war representation
    # Instead of sending full 2D array, we'll send only visible coordinates
    visible_tiles = []
    if ai_fog_grid:
        for y in range(min(len(ai_fog_grid), map_height)):
            for x in range(min(len(ai_fog_grid[y]), map_width)):
                if ai_fog_grid[y][x] == 1:  # If tile is visible to AI
                    visible_tiles.append([x, y])
    
    # Only keep essential terrain data for visible tiles
    terrain_visible = {}
    if "terrain" in game_state.get("map_data", {}):
        terrain = game_state["map_data"]["terrain"]
        
        # Process terrain only for visible tiles
        for [x, y] in visible_tiles:
            if y < len(terrain) and x < len(terrain[y]):
                # Only store non-zero terrains to save tokens
                if terrain[y][x] != 0:
                    # Store as "x,y": terrain_type
                    terrain_visible[f"{x},{y}"] = terrain[y][x]
    
    # Extract essential IA info (units and cities with minimal properties)
    ia_units = []
    if "units" in game_state.get("ia", {}):
        for unit in game_state["ia"]["units"]:
            # Keep only essential unit properties
            ia_units.append({
                "id": unit.get("id"),
                "type_id": unit.get("type_id"),
                "position": unit.get("position"),
                "health": unit.get("health"),
                "attack": unit.get("attack"),
                "defense": unit.get("defense"),
                "movement": unit.get("movement"),
                "remainingMovement": unit.get("remainingMovement", unit.get("movement", 2)),
                "status": unit.get("status", "ready")
            })
    
    # Extract essential city information
    ia_cities = []
    if "cities" in game_state.get("ia", {}):
        for city in game_state["ia"]["cities"]:
            ia_cities.append({
                "id": city.get("id"),
                "name": city.get("name"),
                "position": city.get("position"),
                "population": city.get("population", 0)
            })
    
    # Extract visible player units (those within AI's fog of war)
    visible_player_units = []
    player_unit_positions = [] # For easy checking
    
    if "units" in game_state.get("player", {}):
        for unit in game_state["player"]["units"]:
            unit_pos = unit.get("position", [])
            if len(unit_pos) >= 2:
                x, y = unit_pos[0], unit_pos[1]
                # Check if unit position is within AI's visibility
                if any(pos[0] == x and pos[1] == y for pos in visible_tiles):
                    player_unit_positions.append((x, y))
                    visible_player_units.append({
                        "id": unit.get("id"),
                        "type_id": unit.get("type_id"),
                        "position": unit_pos
                    })
    
    # Create minimal filtered state
    filtered_state = {
        "difficulty": game_state.get("difficulty"),
        "turn": game_state.get("turn"),
        "map_size": {"width": map_width, "height": map_height},
        "visible_tiles": visible_tiles,
        "terrain_visible": terrain_visible,
        "player_units_visible": visible_player_units,
        "player_unit_positions": player_unit_positions,  # Add positions array for easier AI logic
        "ia": {
            "units": ia_units,
            "cities": ia_cities,
            "resources": game_state.get("ia", {}).get("resources", {})
        },
        "ceasefire_turns": game_state.get("ceasefire_turns", 0)
    }
    
    return filtered_state

def iaDeitu(prompt: str = None, game_state: dict = None) -> str:
    """
    Function to interact with the game AI.
    If a prompt is provided, send it directly to the LLM and return its response.
    If no prompt is provided, use the default behavior (filtered game state, system instructions, etc).
    Returns the LLM response (usually JSON).
    """
    try:
        # Initialize the client (keep a persistent instance)
        if not hasattr(iaDeitu, "_client"):
            iaDeitu._client = GroqAPIClient()
            # System instructions (only sent once)
            system_instructions = """
            You are an AI controlling a player in a turn-based strategy game similar to Civilization.
            Your role is to return ONLY a valid JSON response with your actions based on the game state.
            DO NOT include any text, explanations, or comments outside the JSON structure.
            
            YOUR PRIORITIES :
            1. CITY BUILDING: Found cities in resource-rich areas when you have settlers
            2. EXPLORATION: Expand visible map area by moving units to unexplored regions
            3. RESOURCE ACQUISITION: Secure tiles with resources (gold, iron, wood, stone)
            4. PRODUCTION: Train more units in your cities, especially settlers, warriors and archers
            5. MILITARY: Protect territory and attack when advantageous
            6. WINNING: Aim to win the game by defeating the oponent after attacking all their troops
            
            GAME RULES:
            1. TURNS AND ACTIONS:
               - You can perform MULTIPLE actions in each turn
               - Each unit can move and/or attack once per turn
               - Actions are executed in the order you specify them in the JSON response
               - At the beginning of each turn, all units have their status reset to "ready" and movement points fully restored
               - Each request you receive represents a fresh turn with all units ready to move
            2. MOVEMENT:
               - Most units can move up to 2 tiles per turn (tracked by remainingMovement)
               - CAVALRY units are faster and can move up to 4 tiles per turn
               - Each unit's movement is stored in the "movement" property (cavalry=4, others=2)
            3. INVALID MOVEMENTS:
               - Unit CANNOT move to other units or cities tale, including if they will move to other position in the next action
               - Units CANNOT move outside map boundaries (all x must be 0 to width-1, all y must be 0 to height-1)
               - Units CANNOT move onto water tiles (terrain type 1)
               - Units CANNOT occupy tiles with other units
               - Units CANNOT move to tiles outside visible_tiles list
            4. COMBAT RULES:
               - You can ONLY attack enemy units that are VISIBLE in your fog of war
               - You can ONLY attack enemy units that are within 3 tiles of one of your units
               - Your units can only attack once per turn
            5. FOUNDING CITIES:
               - Only settler units can found cities
               - Cities require resources: 20 wood and 15 stone
               - Cannot found cities on water or where another city exists
            6. CITY MANAGEMENT AND CONSTRUCTION:
            Before manage or produce in your cities check if you have any city, if you don't, you can't do anything. So, to create a city use these example:
            {
                "type": "construction",
                "building": "city",
                "city_id": "city-identifier",
                "action": "build",
                "item_id": "settler",
                "position": [5, 7]
            }

            To produce in your city use this example:
            {
                "type": "city_production",
                "city_id": "city-identifier",
                "action": "build|train|research",
                "item_id": "building_type|unit_type|technology_id"
            }
            - When you have cities, PRIORITIZE BUILDING construction in this order:
                a) Sawmill (produces wood: 10/turn, costs: 20 wood, 20 stone)
                b) Quarry (produces stone: 10/turn, costs: 30 wood, 20 stone)
                c) Farm (produces food: 15/turn, costs: 40 wood)
                d) Library (enables technology research, costs: 70 wood, 50 stone)
                e) Iron Mine (produces iron: 8/turn, costs: 50 wood, 50 stone, requires "medium" technology)
                f) Gold Mine (produces gold: 5/turn, costs: 50 wood, 70 stone, requires "medium" technology)
            
            - UNIT TRAINING priorities:
                a) Settler (for expansion, costs: 100 food, 50 gold)
                b) Warrior (for defense, costs: 50 food, 10 gold)
                c) Archer (for ranged combat, costs: 40 food, 15 gold, 10 wood)
                d) Cavalry (for fast exploration, costs: 70 food, 20 gold, requires "medium" technology)

            - TECHNOLOGY research sequence:
                a) Begin with "medium" technology (10 turns) when you have a library
                b) Later research "advanced" technology (20 turns) when population reaches 100
                
             IMPORTANT:
            7. CITY PRODUCTION ACTIONS:
            - Include in your response construction actions with format:
                {
                "type": "city_production",
                "city_id": "city-identifier",
                "action": "build|train|research",
                "item_id": "building_type|unit_type|technology_id"
                }
            8. FOG OF WAR:
               - You start with a 4x4 area of visibility around your starting position
               - When units move, they reveal a 4x4 area around their new position
               - You can only see tiles listed in "visible_tiles"
               - Terrain information is only available for visible tiles
               - Enemy units are only shown if they're within your visible tiles

            
            TERRAIN TYPES:
            - 0: Normal land (passable)
            - 1: Water (IMPASSABLE)
            - 2: Gold resource
            - 3: Iron resource
            - 4: Wood resource
            - 5: Stone resource
            
            UNIT TYPES:
            - warrior: Standard combat unit with 2 tiles movement
            - archer: Ranged unit with 2 tiles movement
            - cavalry: Fast combat unit with 4 tiles movement
            - settler: Can found cities, has 2 tiles movement
            
            RESPONSE FORMAT:
            {
              "actions": [
                {
                  "type": "movement|attack|construction",
                  "unit_id": "unit-identifier", // IMPORTANT: Always include a valid unit TYPE_ID(settler, warrior, archer, cavalry, tank) of the unit
                  "position": [x, y],           // Current unit position
                  "target_position": [x, y],    // For movement/attack: target position
                  "state_before": { "position": [x, y], "remainingMovement": n, "status": "ready|moved|exhausted" },
                  "state_after": { "position": [x, y], "remainingMovement": n, "status": "ready|moved|exhausted" }
                },
                {
                  // You can include multiple actions for different units or even the same unit
                  // if it has remaining movement points
                }
              ],
              "reasoning": "Brief explanation of your strategy (1-2 sentences)"
            }
            
            IMPORTANT NOTES:
            - PRIORITIZE EXPLORATION, FOUNDING CITIES and expanding your visible area of the map
            - Found cities near resource tiles when you have enough wood (20) and stone (15)
            - Produce more units in your cities, especially settlers for expansion
            - Each unit can move up to its movement value and/or attack once per turn
            - Cavalry units can move up to 4 tiles per turn - use this advantage for exploration
            - FOCUS ON EXPLORATION AND EXPANSION early, MILITARY later
            - All your units have full movement points available at the start of each turn
            - You can only attack enemy units that are visible and within 2 tiles of your units.
            - You can't move to water tiles (terrain type 1)
            - You can't move to the same tile as another unit or city
            - To win the game you must defeat the player by attacking all their troops
            - You can't attack while in a ceasefire
            - You can't move to a tile that is another troop or city
            """
            
            # Set system instructions
            iaDeitu._client.set_system_instructions(system_instructions)

        # --- NUEVO: Si se pasa un prompt explícito, mándalo tal cual al LLM ---

        if prompt is not None:
            # Si hay prompt, simplemente llama al LLM con ese prompt y devuelve la respuesta
            response = iaDeitu._client.run_call(prompt)
            return response

        # --- Si no hay prompt, sigue el flujo normal (acción de la IA en el juego) ---
        # Filter game state
        filtered_game_state = filter_game_state(game_state)

        # Build current message with minimal essential information
        game_prompt = f"""
        Generate actions based on this game state:
        {json.dumps(filtered_game_state)}
        
        Return ONLY a valid JSON with your actions. Your response must follow exactly the format from the instructions:
        1. Map boundaries are {filtered_game_state["map_size"]["width"]}x{filtered_game_state["map_size"]["height"]} (0-indexed). Never move outside these bounds.
        2. Only move to tiles that are visible in your fog of war (visible_tiles)
        3. Only attack enemy units that are VISIBLE and within 2 tiles of your units
        4. Calculate remaining movement and status correctly
        5. ALWAYS include a unit_id for all actions - if a unit has no ID, generate one using its position: "unit-x-y"
        6. You SHOULD perform multiple actions in a single turn - move all available units!
        7. Remember that cavalry units can move up to 4 tiles per turn (instead of 2)
        8. Your PRIMARY OBJECTIVE is to maximize exploration and visibility - prioritize movements that reveal new areas
        9. Your SECONDARY OBJECTIVE is to secure valuable resource tiles (gold, iron, wood, stone)
        10. IMPORTANT: This is a NEW TURN - all units shown in the game state have full movement points and status "ready"
        11. CITY MANAGEMENT: For each city without active production:
        a) Build Sawmills and Quarries first to secure resource production
        b) Build a Farm when food drops below 100
        c) Build a Library when you have at least 70 wood and 50 stone
        d) Start researching "medium" technology once you have a Library
        e) Train units when defenses are needed or for expansion

        IMPORTANT: Prioritize building cities in resource-rich areas when you have settlers
        CRITICAL: Always verify x coordinates are between 0 and {filtered_game_state["map_size"]["width"]-1} and y coordinates are between 0 and {filtered_game_state["map_size"]["height"]-1}.
        """

        # Call the API with the specific game prompt
        api_response = iaDeitu._client.run_call(prompt=game_prompt)

        # Post-process the response to ensure all actions have unit_ids
        try:
            # Parse the response
            response_data = json.loads(api_response)

            # Check if we have actions
            if "actions" in response_data and isinstance(response_data["actions"], list):
                for action in response_data["actions"]:
                    # If unit_id is missing or null, generate one from position
                    if "unit_id" not in action or action["unit_id"] is None:
                        if "position" in action and isinstance(action["position"], list) and len(action["position"]) >= 2:
                            x, y = action["position"][0], action["position"][1]
                            action["unit_id"] = f"unit-{x}-{y}"

            # Return the fixed response
            return json.dumps(response_data)
        except:
            # If any error in post-processing, return the original response
            return api_response

    except Exception as e:
        print(f"Error in execution: {str(e)}")
        return json.dumps({"error": str(e)})
