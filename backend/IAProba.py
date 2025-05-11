#!/usr/bin/env python3
import requests
import time
import json
import os
from typing import Dict, Optional, Any
from dotenv import load_dotenv

class GroqAPIClient:
    """Cliente para realizar llamadas a la API de Groq con manejo de errores y cambio de modelos."""
    
    BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    # Lista de modelos disponibles en Groq (agrega o quita según necesidad)
    MODELS = [
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "meta-llama/llama-4-scout-17b-16e-instruct"
        "llama-3.3-70b-versatile",
        "deepseek-r1-distill-llama-70b",
        "meta-llama/Llama-Guard-4-12B"
        "qwen-qwq-32b",
        
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
    
    def call_api(self, prompt: str, temperature: float = 0.3) -> Dict[str, Any]:
        """
        Realiza una llamada a la API de Groq con manejo de errores.
        
        Args:
            prompt: El texto del prompt a enviar.
            max_tokens: Número máximo de tokens en la respuesta.
            temperature: Temperatura para la generación (0.0 - 1.0).
            retry_delay: Tiempo en segundos entre reintentos.
            max_retries: Número máximo de reintentos antes de cambiar de modelo.
            
        Returns:
            Respuesta de la API en formato diccionario.
        """
        payload = {
            "model": self.current_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature
        }
        
        retries = 0
        while retries < len(self.MODELS):  # Intentar con todos los modelos si es necesario
            try:
                print(f"Enviando solicitud a {self.current_model}")
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
    
    def run_call(self, prompt: str) -> str:
        """        
        Args:
            prompt: El texto del prompt fijo a enviar.
        """
        try:
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

def iaDeitu(prompt: str, game_state: dict = None) -> str:
    """
    Función para interactuar con la IA de juego.
    
    Args:
        prompt: El prompt principal para la IA.
        game_state: Estado actual del juego en formato JSON.
        rules: Las reglas del juego.
    
    Returns:
        Respuesta de la IA, generalmente en formato JSON.
    """
    try:
        # Inicializar el cliente
        client = GroqAPIClient()
        
        # Siempre incluimos las instrucciones del sistema en cada llamada
        system_instructions = f"""
        Eres una IA que controla un jugador en un juego de estrategia por turnos tipo Civilization. 
        Tu objetivo es tomar decisiones estratégicas según el estado del juego que recibirás.
        Debes responder EXCLUSIVAMENTE en formato JSON según el esquema proporcionado, aparte del JSON no añadas nada más.
        No debes incluir comentarios, explicaciones o cualquier otro texto fuera del JSON.
        Estas son las reglas del juego:
        -Cada unidad puede movrse dos veces por turno.
        -Cada unidad puede atacar una vez por turno.
        -Cada unidad puede construir una vez por turno.
        """
        game_prompt = f"""
        {system_instructions}
        
        Basado en el estado actual del juego y tus objetivos, genera tu siguiente turno de acciones.
        
        IMPORTANTE: NO puedes usar directamente los elementos map_data.startPoint, grid y visibleObjects del JSON 
        del estado del juego. Estos son datos internos del motor de juego.
        
        Información sobre el terreno:
        - 0: Tierra (terreno normal)
        - 1: Agua (no transitable)
        - 2: Terreno con minerales (recursos)
        - 3: Terreno con hierro (recursos)
        - 4: Terreno con madera (bosque)
        - 5: Terreno con piedra (recursos)
        - 6: Terreno con oro (recursos)
        
        Estado actual del juego:
        {json.dumps(game_state) if game_state else 'No hay estado de juego disponible.'}
        
        {prompt}
        
        Responde ÚNICAMENTE con un JSON válido siguiendo esta estructura:
        {{
          "ai_turn_id": "[ID único para este turno]",
          "game_id": "[ID del juego actual]",
          "turn_number": [número del turno actual],
          "actions": [
            {{
              "action_id": [número secuencial de acción],
              "type": "[tipo de acción/ movimiento/ataque/construcción]",
                "unit_id": "[ID de la unidad que realiza la acción]",
                "position":[
                  [coordenada_x, coordenada_y]
                ],
              // otros campos según el tipo de acción
              "state_before": {{ /* estado resumido antes de la acción */ }},
              "state_after": {{ /* estado resumido después de la acción */ }}
            }},
            // más acciones...
          ],
          "reasoning": "[Explicación breve de tu estrategia en este turno]"
        }}

        Aqui tienes un ejemplo de respuesta:
        {{
  "ai_turn_id": "ai_turn_1684159782",
  "game_id": "game_12345",
  "turn_number": 5,
  "actions": [
    {{
      "action_id": 1,
      "type": "movement",
      "unit_id": "warrior_01",
      "position": [15, 8],
      "target_position": [16, 9],
      "state_before": {{
        "position": [15, 8],
        "remainingMovement": 2,
        "status": "ready"
      }},
      "state_after": {{
        "position": [16, 9],
        "remainingMovement": 1,
        "status": "moved"
      }}
        }},
    {{
      "action_id": 2,
      "type": "attack",
      "unit_id": "warrior_01",
      "position": [16, 9],
      "target_unit_id": "player_settler_03",
      "target_position": [17, 9],
      "state_before": {{
        "position": [16, 9],
        "remainingMovement": 1,
        "status": "moved",
        "health": 100
      }},
      "state_after": {{
        "position": [16, 9],
        "remainingMovement": 0,
        "status": "exhausted",
        "health": 85
      }}
    }},
    {{
      "action_id": 3,
      "type": "construction",
      "unit_id": "settler_02",
      "position": [12, 5],
      "building": "city",
      "city_name": "New Atlantis",
      "state_before": {{
        "position": [12, 5],
        "remainingMovement": 2,
        "status": "ready"
      }},
      "state_after": {{
        "position": [12, 5],
        "remainingMovement": 0,
        "status": "exhausted"
      }}
    }}
  ],
  "reasoning": "Advancing warrior units toward player territory to apply pressure while establishing a new city near resources to secure economic advantage."
}}

        Recuerda que el JSON debe ser válido y no debe contener comillas al principio o al final.
        Si no puedes realizar ninguna acción, responde con un JSON vacío.
        """
        
        # Ejecutar la llamada a la API y devolver directamente el resultado
        return client.run_call(prompt=game_prompt)
        
    except Exception as e:
        print(f"Error en la ejecución: {str(e)}")
        return json.dumps({"error": str(e)})
