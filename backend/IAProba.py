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
    Filtra el estado del juego para incluir solo los campos necesarios,
    reduciendo así el número de tokens enviados a la API.
    
    Args:
        game_state: Estado completo del juego.
        
    Returns:
        Estado filtrado del juego con solo los campos necesarios.
    """
    if not game_state:
        return {}
        
    filtered_state = {
        "difficulty": game_state.get("difficulty"),
        "turn": game_state.get("turn"),
        "map_size": game_state.get("map_data", {}).get("map_size"),
        "terrain": game_state.get("map_data", {}).get("terrain"),
        "player_units": game_state.get("player", {}).get("units"),
        "ia_info": game_state.get("ia", {})
    }
    
    return filtered_state

def iaDeitu(prompt: str, game_state: dict = None) -> str:
    """
    Función para interactuar con la IA de juego.
    
    Args:
        prompt: El prompt principal para la IA.
        game_state: Estado actual del juego en formato JSON.
    
    Returns:
        Respuesta de la IA, generalmente en formato JSON.
    """
    try:
        # Inicializar el cliente (mantenemos una instancia persistente)
        if not hasattr(iaDeitu, "_client"):
            iaDeitu._client = GroqAPIClient()
            
            # Instrucciones del sistema que solo se envían una vez
            system_instructions = """
            Eres una IA que controla un jugador en un juego de estrategia por turnos tipo Civilization. 
            Tu objetivo es tomar decisiones estratégicas según el estado del juego que recibirás.
            Debes responder EXCLUSIVAMENTE en formato JSON según el esquema proporcionado, aparte del JSON no añadas nada más.
            No debes incluir comentarios, explicaciones o cualquier otro texto fuera del JSON.
            Estas son las reglas del juego:
            -Cada unidad puede movrse dos veces por turno.
            -Cada unidad puede atacar una vez por turno.
            -Cada unidad puede construir una vez por turno.
            -No puede haber dos unidades en la misma posición. (IMPORTANTE)
            -Las unidades no se pueden salir del mapa, es decir en un mapa 20x20 no pueden ir a las posiciones [20,0] o [0,20], ya que las coordenadas empiezan por el 0, para saber el tamaño del mapa fijate en el valor map_size del json del game que te paso.
            -Las unidades no pueden moverse a través de otras unidades.
            -Las unidades no pueden moverse a través de agua ni tampoco pueden estar en agua. (IMPORTANTE)
            
            Información sobre el terreno:
            - 0: Tierra (terreno normal)
            - 1: Agua (no transitable)
            - 2: Terreno con minerales (recursos)
            - 3: Terreno con hierro (recursos)
            - 4: Terreno con madera (bosque)
            - 5: Terreno con piedra (recursos)
            - 6: Terreno con oro (recursos)

            Los types de las acciones son:
            - movement
            - attack
            - construction
            
            Tu respuesta debe seguir este formato JSON:
            {
              "ai_turn_id": "ai_turn_ID",
              "game_id": "game_ID",
              "turn_number": NUMBER,
              "actions": [
                {
                  "action_id": NUMBER,
                  "type": "TYPE",
                  "unit_id": "ID",
                  "position": [X, Y],
                  "target_position": [X, Y],
                  "state_before": { "position": [X, Y], "remainingMovement": NUMBER, "status": "STATUS" },
                  "state_after": { "position": [X, Y], "remainingMovement": NUMBER, "status": "STATUS" }
                }
              ],
              "reasoning": "BRIEF_EXPLANATION"
            }
            """
            
            # Establecer las instrucciones del sistema en el cliente
            iaDeitu._client.set_system_instructions(system_instructions)
        
        # Filtrar el estado del juego para incluir solo los campos necesarios
        filtered_game_state = filter_game_state(game_state)
        
        # Construir el mensaje actual con el estado filtrado del juego y prompt específico
        game_prompt = f"""
        Genera tu siguiente turno de acciones basado en este estado de juego filtrado:
        
        {json.dumps(filtered_game_state)}
        
        {prompt}
        
        Responde SOLO con un JSON válido siguiendo el formato especificado en las instrucciones.
        """
        
        # Ejecutar la llamada a la API con el prompt específico del juego
        return iaDeitu._client.run_call(prompt=game_prompt)
        
    except Exception as e:
        print(f"Error en la ejecución: {str(e)}")
        return json.dumps({"error": str(e)})
