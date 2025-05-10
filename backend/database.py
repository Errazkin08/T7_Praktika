from pymongo import MongoClient
from flask import g, session
import os
import datetime
import random
import uuid
import json
from bson import ObjectId

# MongoDB connection string - using environment variable for security
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://mongodb:27017/')

# Add this utility function for JSON serialization
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super(JSONEncoder, self).default(obj)

def sanitize_for_json(obj):
    """
    Convert any MongoDB ObjectId or datetime objects to strings for JSON serialization
    """
    return json.loads(JSONEncoder().encode(obj))

def get_db():
    """
    Configure the MongoDB connection
    """
    if 'db' not in g:
        client = MongoClient(MONGO_URI)
        g.db = client.game_database
    return g.db

def close_db(e=None):
    """
    Close the MongoDB connection
    """
    db = g.pop('db', None)
    if db is not None:
        db.client.close()

def init_db():
    """
    Initialize database collections if they don't exist
    """
    db = get_db()
    
    # Create users collection if it doesn't exist
    collections = db.list_collection_names()
    if 'users' not in collections:
        db.create_collection('users')
        print("Users collection created")
    if 'maps' not in collections:
        db.create_collection('maps')
        print("Maps collection created")
    if 'games' not in collections:
        db.create_collection('games')
        print("Games collection created")
    
    # Check if any map exists, if not create a test map
    create_test_map_if_not_exists()

def create_test_map_if_not_exists():
    """
    Create a test map if there are no maps in the database
    """
    db = get_db()
    
    # Check if any maps exist
    maps_count = db.maps.count_documents({})
    
    if maps_count == 0:
        # Create a test map
        width = 30
        height = 15
        startPoint = [15, 7]  # Center of the map
        
        # Use the add_map function to create the test map
        result = add_map(width, height, startPoint, "easy")
        print("Test map created")

def add_user(username, password_hash):
    """
    Add a new user to the database
    """
    db = get_db()
    user = {
        "username": username,
        "password": password_hash,
        "created_at": datetime.datetime.now(),
        "last_login": datetime.datetime.now()
    }
    return db.users.insert_one(user)

def find_user(username):
    """
    Find a user by username
    """
    db = get_db()
    return db.users.find_one({"username": username})

def update_user_login(username):
    """
    Update the last login time of a user
    """
    db = get_db()
    return db.users.update_one(
        {"username": username},
        {"$set": {"last_login": datetime.datetime.now()}}
    )

def update_user_score(username, score):
    """
    Update a user's score
    """
    db = get_db()
    return db.users.update_one(
        {"username": username},
        {"$set": {"score": score}}
    )

def get_all_users():
    """
    Get all users from the database
    """
    db = get_db()
    return list(db.users.find({}, {'_id': 0, 'password': 0}))

def add_map(width, height, startPoint, difficulty="easy", name=None):
    """
    Add a new map to the database with terrain types:
    0 - Normal terrain
    1 - Water
    2 - Mineralized terrain (rare)
    """
    db = get_db()
    
    # Create a grid (vector of vectors) initialized with zeros
    grid = [[0 for _ in range(width)] for _ in range(height)]
    
    # Create a terrain grid (0=normal, 1=water, 2=mineralized)
    terrain = generate_terrain(width, height, difficulty)
    
    # Remove water tiles within a 4-tile perimeter around the start point
    x_start, y_start = startPoint
    for y in range(max(0, y_start - 4), min(height, y_start + 5)):
        for x in range(max(0, x_start - 4), min(width, x_start + 5)):
            # Calculate Manhattan distance from start point
            distance = abs(x - x_start) + abs(y - y_start)
            if distance <= 4 and terrain[y][x] == 1:  # If it's water and within perimeter
                terrain[y][x] = 0  # Change to normal terrain
    
    # Set visibility for a 3x3 area around the start point
    x, y = startPoint
    
    # Loop through a 3x3 grid centered at the start point
    for dy in range(-1, 2):  # -1, 0, 1
        for dx in range(-1, 2):  # -1, 0, 1
            nx, ny = x + dx, y + dy
            # Check if position is within map boundaries
            if 0 <= nx < width and 0 <= ny < height:
                grid[ny][nx] = 1  # Set to visible (1) in fog of war grid
    
    # Generate a default name if none provided
    if not name:
        name = f"Mapa {width}x{height} ({difficulty})"
    
    # Create the map document
    map = {
        "width": width,
        "height": height,
        "grid": grid,
        "terrain": terrain,
        "startPoint": startPoint,
        "visibleObjects": [],  # Initialize with an empty list
        "difficulty": difficulty,  # Add difficulty to the map document
        "name": name  # Add name to the map document
    }
    
    return db.maps.insert_one(map)

def generate_terrain(width, height, difficulty):
    """
    Generate terrain with patterns:
    - 0: Normal terrain (most common)
    - 1: Water (forms lakes and rivers)
    - 2: Mineralized terrain (rare, forms in small clusters)
    """
    # Initialize terrain with normal terrain
    terrain = [[0 for _ in range(width)] for _ in range(height)]
    
    # Water generation parameters
    water_percent = 15  # 15% of map is water
    water_seeds = int((width * height * water_percent) / 100 / 10)
    water_seeds = max(3, min(15, water_seeds))  # Minimum 3, maximum 15 seeds
    
    # Mineralized terrain parameters
    mineral_percent = 5  # 5% of map is mineralized (rare resource)
    mineral_seeds = int((width * height * mineral_percent) / 100 / 4)
    mineral_seeds = max(2, min(8, mineral_seeds))  # Minimum 2, maximum 8 seeds
    
    # Adjust difficulty
    if difficulty == "medium":
        water_percent += 5
        mineral_percent -= 1
    elif difficulty == "hard":
        water_percent += 10
        mineral_percent -= 2
    
    # Generate water bodies (lakes/rivers)
    for _ in range(water_seeds):
        # Random starting point
        x = random.randint(2, width - 3)
        y = random.randint(2, height - 3)
        
        # Size of the water body
        size = random.randint(5, 15)
        
        # Generate water in a natural-looking pattern
        generate_water_pattern(terrain, x, y, size, width, height)
    
    # Generate mineralized terrain (small clusters)
    for _ in range(mineral_seeds):
        # Random starting point
        x = random.randint(1, width - 2)
        y = random.randint(1, height - 2)
        
        # Size of the mineral deposit
        size = random.randint(1, 3)
        
        # Generate minerals in small clusters
        generate_mineral_pattern(terrain, x, y, size, width, height)
    
    return terrain

def generate_water_pattern(terrain, x, y, size, width, height):
    """Generate a natural-looking water body"""
    # Mark the center as water
    terrain[y][x] = 1
    
    # Generate water in a randomized pattern around the center
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    queue = [(x, y, size)]
    
    while queue:
        cx, cy, remaining_size = queue.pop(0)
        if remaining_size <= 0:
            continue
        
        # Choose random directions to expand
        random.shuffle(directions)
        for dx, dy in directions[:random.randint(1, 4)]:  # Expand in 1-4 directions
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height and terrain[ny][nx] == 0:
                terrain[ny][nx] = 1
                # Continue expanding with reduced size
                if random.random() < 0.7:  # 70% chance to continue
                    queue.append((nx, ny, remaining_size - 1))

def generate_mineral_pattern(terrain, x, y, size, width, height):
    """Generate a small cluster of mineralized terrain"""
    # Mark the center as mineralized
    if terrain[y][x] == 0:  # Only place minerals on normal terrain
        terrain[y][x] = 2
    
    # Generate minerals in a small cluster
    if size > 1:
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for _ in range(size):
            dx, dy = random.choice(directions)
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and terrain[ny][nx] == 0:
                terrain[ny][nx] = 2

def get_first_map():
    """
    Get the first map from the database
    """
    db = get_db()
    return db.maps.find_one({})

def get_map(map_id):
    """
    Get a map by its ID
    """
    db = get_db()
    try:
        # Convert map_id to ObjectId if necessary
        if isinstance(map_id, str) and len(map_id) == 24:
            obj_id = ObjectId(map_id)
            map_doc = db.maps.find_one({"_id": obj_id})
        else:
            map_doc = db.maps.find_one({"map_id": map_id})
        
        # Convert ObjectId to string for JSON serialization
        if map_doc and '_id' in map_doc:
            map_doc['_id'] = str(map_doc['_id'])
        
        return map_doc
    except Exception as e:
        print(f"Error in get_map(): {str(e)}")
        return None

def get_all_maps():
    """
    Get all maps from the database
    """
    db = get_db()
    maps = []
    try:
        # Encuentra todos los mapas y procesa cada uno para asegurar serialización JSON segura
        for map_doc in db.maps.find():
            # Convertir ObjectId a string para evitar problemas de serialización JSON
            if '_id' in map_doc:
                map_doc['map_id'] = str(map_doc['_id'])
                map_doc['_id'] = str(map_doc['_id'])
            maps.append(map_doc)
        print(f"Found {len(maps)} maps in database")
        return maps
    except Exception as e:
        print(f"Error in get_all_maps(): {str(e)}")
        # En caso de error, devuelve una lista vacía en lugar de lanzar excepción
        return []

def delete_map(map_id):
    """
    Delete a map from the database by its ID
    """
    db = get_db()
    try:
        # Intentar diferentes formas de encontrar el mapa
        deleted = False
        
        # Intento 1: Buscar por _id como ObjectId
        try:
            obj_id = ObjectId(map_id)
            result = db.maps.delete_one({"_id": obj_id})
            if result.deleted_count > 0:
                return True
        except Exception as e:
            print(f"Could not delete by ObjectId: {e}")
        
        # Intento 2: Buscar por map_id como string
        result = db.maps.delete_one({"map_id": map_id})
        if result.deleted_count > 0:
            return True
            
        # Intento 3: Para IDs generados por el frontend (map-timestamp)
        if map_id.startswith('map-'):
            # Obtener el primer mapa (para desarrollo)
            # Esto es solo una solución temporal
            result = db.maps.delete_one({})
            if result.deleted_count > 0:
                return True
        
        return False
    except Exception as e:
        print(f"Error deleting map: {e}")
        return False

def add_game(username, map_id, difficulty, game_name="New Game"):
    """Add a new game for a user"""
    try:
        db = get_db()
        
        # Always convert map_id to string to avoid ObjectId serialization issues
        if isinstance(map_id, ObjectId):
            map_id_str = str(map_id)
        else:
            map_id_str = map_id
        
        # Obtener el mapa completo de la base de datos
        map_data = None
        try:
            # Intenta buscar por el ID original (podría ser ObjectId)
            map_data = db.maps.find_one({"_id": ObjectId(map_id_str)})
        except:
            # Si falla, intenta buscar por el ID como string
            map_data = db.maps.find_one({"_id": map_id_str})
            
        # Si no encontramos el mapa, creamos uno básico
        if not map_data:
            print(f"Warning: Map with ID {map_id_str} not found, creating basic map")
            # Crear grid y terreno básicos
            basic_grid = [[0 for _ in range(30)] for _ in range(15)]
            basic_terrain = [[0 for _ in range(30)] for _ in range(15)]
            
            # Añadir algunos elementos de terreno variados para mayor realismo
            for y in range(15):
                for x in range(30):
                    # Generar terreno simple pseudo-aleatorio basado en la posición
                    if (x + y) % 7 == 0:
                        basic_terrain[y][x] = 1  # Agua
                    elif (x * y) % 13 == 0:
                        basic_terrain[y][x] = 2  # Terreno mineralizado
            
            map_data = {
                "width": 30,
                "height": 15,
                "grid": basic_grid,
                "terrain": basic_terrain,  # Añadimos el terreno
                "startPoint": [15, 7],
                "difficulty": difficulty,
                "visibleObjects": []  # Igual que en add_map
            }
            
        # Extract map size properly
        map_size = {
            "width": map_data.get("width", 30),
            "height": map_data.get("height", 15)
        }
        
        # Create a copy of the start point for each unit to avoid shared references
        settler = get_troop_type("settler", map_data["startPoint"][:])  # Create a copy of the list

        # Create a separate copy for the warrior
        warrior = get_troop_type("warrior", map_data["startPoint"][:])  # Create another copy
        
        # Adjust warrior position to be adjacent to start point
        if map_data["startPoint"][0] + 1 < map_size["width"]:
            warrior["position"][0] += 1
        elif map_data["startPoint"][1] + 1 < map_size["height"]:
            warrior["position"][1] += 1
        elif map_data["startPoint"][0] - 1 >= 0:
            warrior["position"][0] -= 1
        elif map_data["startPoint"][1] - 1 >= 0:
            warrior["position"][1] -= 1
            
        # Create a timestamp-based game ID
        game_id = str(int(datetime.datetime.now().timestamp() * 1000) + 1)
        
        # Crear el documento del juego con el mapa completo
        game = {
            "game_id": game_id,
            "username": username,
            "name": game_name,  # Store the user-provided name
            "difficulty": difficulty,
            "turn": 1,
            "current_player": "player",
            "cheats_used": [],

            "map_id": map_id_str,
            "map_size": map_size,  # Explicitly store map size
            "map_data": map_data,  # Guardar el mapa completo
            "player": {
                "units": [settler, warrior],
                "cities": [],
                "resources": {
                    "food": 100,
                    "gold": 50,
                    "wood": 20
                },
            },
            "ia": {
                "units": [],
                "cities": []
            },
            "created_at": datetime.datetime.now(),
            "last_saved": datetime.datetime.now()
        }
        
        # Convert the game object to be JSON serializable before storing in session
        session['game'] = sanitize_for_json(game)
        
        # Return the original game object for storing in MongoDB
        return db.games.insert_one(game)
    except Exception as e:
        print(f"Error adding game: {e}")
        return None

def save_game():
    """
    Save the current game in the session to the database
    """
    db = get_db()
    game = session.get('game')
    
    if not game:
        print("No game found in session to save")
        return False
        
    try:
        # Make sure game_id exists
        if 'game_id' not in game or not game['game_id']:
            game_id = str(int(datetime.datetime.now().timestamp() * 1000))
            game['game_id'] = game_id
        
        # Update the last_saved timestamp
        game['last_saved'] = datetime.datetime.now().isoformat()
        
        # Create a direct copy of the game data to save
        # This avoids any accidental references to the session object
        game_to_save = dict(game)
        
        # Find and remove the existing game first
        db.games.delete_one({"game_id": game_to_save['game_id']})
        
        # Insert as a new document
        result = db.games.insert_one(game_to_save)
        
        print(f"Game saved successfully with ID: {game_to_save['game_id']}")
        return True
    except Exception as e:
        print(f"Error saving game: {e}")
        return False

def delete_game(game_id):
    """
    Delete a game from the database
    """
    try:
        db = get_db()
        
        # Try different formats of game_id
        deleted = False
        
        # Try as is
        result = db.games.delete_one({"game_id": game_id})
        if result.deleted_count > 0:
            deleted = True
        
        # Try as integer if it's not already
        if not deleted and isinstance(game_id, str):
            try:
                numeric_id = int(game_id)
                result = db.games.delete_one({"game_id": numeric_id})
                if result.deleted_count > 0:
                    deleted = True
            except ValueError:
                pass
        
        # Try by _id if it could be an ObjectId
        if not deleted and isinstance(game_id, str) and len(game_id) == 24:
            try:
                obj_id = ObjectId(game_id)
                result = db.games.delete_one({"_id": obj_id})
                if result.deleted_count > 0:
                    deleted = True
            except Exception:
                pass
        
        # If the game was in the session, remove it
        if 'game' in session and session.get('game', {}).get('game_id') == game_id:
            session.pop('game', None)
        
        return deleted
    except Exception as e:
        print(f"Error in delete_game: {e}")
        raise

def get_user_games(username):
    """
    Get all games for a specific user
    """
    db = get_db()
    games = []
    try:
        # Get all games for the user
        games_cursor = db.games.find({"username": username})
        
        # Process each game to ensure JSON serialization works
        for game in games_cursor:
            # Use the sanitize_for_json helper to handle ObjectId and datetime objects
            sanitized_game = sanitize_for_json(game)
            games.append(sanitized_game)
            
        return games
    except Exception as e:
        print(f"Error in get_user_games: {str(e)}")
        return []

def get_game_by_id_from_db(game_id, username=None):
    """
    Get a game by its ID. If username is provided, verify that the game belongs to this user.
    """
    db = get_db()
    try:
        # First try by game_id as is
        game = db.games.find_one({"game_id": game_id})
        
        if not game and isinstance(game_id, str):
            try:
                # Try as integer
                numeric_id = int(game_id)
                game = db.games.find_one({"game_id": numeric_id})
            except ValueError:
                pass
            
            # Try as ObjectId
            if not game and len(game_id) == 24:
                try:
                    obj_id = ObjectId(game_id)
                    game = db.games.find_one({"_id": obj_id})
                except Exception:
                    pass
        
        # If game found and username provided, check ownership
        if game and username and game.get('username') != username:
            print(f"Game {game_id} belongs to {game.get('username')}, not to {username}")
            return None
        
        # Ensure the game is properly cleaned for session storage
        if game:
            # Make sure ObjectIds are converted to strings
            if '_id' in game:
                game['_id'] = str(game['_id'])
            
            # Make sure the game_id is a string
            if 'game_id' in game and not isinstance(game['game_id'], str):
                game['game_id'] = str(game['game_id'])
                
            # Store the exact game document in the session
            session['game'] = game
        
        return game
    except Exception as e:
        print(f"Error getting game by ID: {e}")
        return None

# Troop related functions
def get_troop_types():
    """
    Get all available troop types
    """
    # Define the base troop types
    troop_types = [
        {
            "type_id": "warrior",
            "name": "Warrior",
            "category": "infantry",
            "health": 100,
            "attack": 10,
            "defense": 10,
            "position": [0, 0],
            "movement": 2,
            "cost": {
                "food": 50,
                "gold": 10
            },
            "abilities": ["basic_attack"],
            "description": "Basic infantry unit"
        },
        {
            "type_id": "archer",
            "name": "Archer",
            "category": "ranged",
            "health": 80,
            "attack": 15,
            "defense": 5,
            "position": [0, 0],
            "movement": 2,
            "range": 2,
            "cost": {
                "food": 40,
                "gold": 15,
                "wood": 10
            },
            "abilities": ["ranged_attack"],
            "description": "Basic ranged unit"
        },
        {
            "type_id": "cavalry",
            "name": "Cavalry",
            "category": "mounted",
            "health": 120,
            "attack": 15,
            "defense": 8,
            "position": [0, 0],
            "movement": 4,
            "cost": {
                "food": 70,
                "gold": 20
            },
            "abilities": ["charge"],
            "description": "Fast moving mounted unit"
        },
        {
            "type_id": "settler",
            "name": "Settler",
            "category": "civilian",
            "health": 50,
            "attack": 0,
            "defense": 1,
            "position": [0, 0],
            "movement": 2,
            "cost": {
                "food": 100,
                "gold": 50
            },
            "abilities": ["found_city"],
            "description": "Can establish new settlements"
        },
        {
            "type_id": "builder",
            "name": "Builder",
            "category": "civilian",
            "health": 40,
            "attack": 0,
            "defense": 1,
            "position": [0, 0],
            "movement": 2,
            "cost": {
                "food": 50,
                "gold": 20
            },
            "abilities": ["build_improvement"],
            "description": "Constructs improvements on the map"
        }
    ]
    return troop_types

def get_troop_type(type_id, position):
    """
    Get a specific troop type by its ID
    """
    troop_types = get_troop_types()
    for troop_type in troop_types:
        if troop_type["type_id"] == type_id:
            troop_type["position"] = position
            return troop_type
    return None

def add_troop_to_player(username, type_id, position):
    """
    Add a new troop to a player's army
    """
    db = get_db()
    
    # Get the troop type
    troop_type = get_troop_type(type_id, position)
    if not troop_type:
        return False, "Invalid troop type"
    
    # Get the game to verify position is valid
    game = session.get('game')
    if not game:
        return False, "No active game"
    
    # Check if position is valid (on the map and not occupied)
    map_data = game.get('map', {})
    width = map_data.get('width', 0)
    height = map_data.get('height', 0)
    
    x, y = position
    if x < 0 or x >= width or y < 0 or y >= height:
        return False, "Position is out of map bounds"
    
    # Create a unique ID for the troop
    troop_id = str(uuid.uuid4())
    
    # Create the troop based on the type
    troop = {
        "id": troop_id,
        "type_id": type_id,
        "name": troop_type["name"],
        "health": troop_type["health"],
        "attack": troop_type["attack"],
        "defense": troop_type["defense"],
        "movement": troop_type["movement"],
        "position": position,
        "status": "ready",
        "created_at": datetime.datetime.now()
    }
    
    # Add specific properties based on troop type
    if "range" in troop_type:
        troop["range"] = troop_type["range"]
    if "abilities" in troop_type:
        troop["abilities"] = troop_type["abilities"]
    
    # Add the troop to the player's army in the current game
    if "troops" not in game:
        game["troops"] = {}
    if username not in game["troops"]:
        game["troops"][username] = []
    
    game["troops"][username].append(troop)
    session['game'] = game
    
    return True, troop

def get_player_troops(username):
    """
    Get all troops for a specific player
    """
    game = session.get('game')
    if not game or "troops" not in game or username not in game["troops"]:
        return []
    return game["troops"][username]

def update_troop_position(username, troop_id, new_position):
    """
    Update a troop's position
    """
    game = session.get('game')
    if not game or "troops" not in game or username not in game["troops"]:
        return False, "No troops found for player"
    
    # Find the troop
    for i, troop in enumerate(game["troops"][username]):
        if troop["id"] == troop_id:
            # Validate the new position
            map_data = game.get('map', {})
            width = map_data.get('width', 0)
            height = map_data.get('height', 0)
            
            x, y = new_position
            if x < 0 or x >= width or y < 0 or y >= height:
                return False, "Position is out of map bounds"
            
            # Update the troop's position
            game["troops"][username][i]["position"] = new_position
            game["troops"][username][i]["status"] = "moved"
            session['game'] = game
            return True, "Troop position updated"
    
    return False, "Troop not found"

def update_troop_status(username, troop_id, status):
    """
    Update a troop's status
    """
    game = session.get('game')
    if not game or "troops" not in game or username not in game["troops"]:
        return False, "No troops found for player"
    
    valid_statuses = ["ready", "moved", "attacked", "exhausted"]
    if status not in valid_statuses:
        return False, "Invalid status"
    
    # Find the troop
    for i, troop in enumerate(game["troops"][username]):
        if troop["id"] == troop_id:
            # Update the troop's status
            game["troops"][username][i]["status"] = status
            session['game'] = game
            return True, "Troop status updated"
    
    return False, "Troop not found"

def reset_troops_status(username):
    """
    Reset all troops status to ready at the start of a new turn
    """
    game = session.get('game')
    if not game or "troops" not in game or username not in game["troops"]:
        return False, "No troops found for player"
    
    for i, troop in enumerate(game["troops"][username]):
        game["troops"][username][i]["status"] = "ready"
    
    session['game'] = game
    return True, "All troops reset to ready status"