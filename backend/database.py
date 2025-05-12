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
    - 2: Gold mineral (rare, 7% of minerals)
    - 3: Iron mineral (uncommon, 13% of minerals)
    - 4: Wood resource (common, 60% of minerals)
    - 5: Stone resource (semi-common, 20% of minerals)
    """
    # Initialize terrain with normal terrain
    terrain = [[0 for _ in range(width)] for _ in range(height)]
    
    # Calculate total tiles
    total_tiles = width * height
    
    # Fixed water percentage regardless of difficulty
    water_percent = 15  # Always 15% of map is water
    
    # Set mineral percentage based on difficulty
    if difficulty == "easy":
        mineral_percent = 20  # 20% minerals on easy difficulty
    elif difficulty == "medium":
        mineral_percent = 15  # 15% minerals on medium difficulty
    elif difficulty == "hard":
        mineral_percent = 10  # 10% minerals on hard difficulty
    else:
        # Default to easy if unknown difficulty
        mineral_percent = 20
    
    # Calculate exact number of tiles for each type
    water_tiles = int(total_tiles * water_percent / 100)
    mineral_tiles = int(total_tiles * mineral_percent / 100)
    
    # Subdivide minerals by type with new percentages
    gold_tiles = int(mineral_tiles * 0.07)    # 7% of minerals are gold
    iron_tiles = int(mineral_tiles * 0.13)    # 13% of minerals are iron
    stone_tiles = int(mineral_tiles * 0.20)   # 20% of minerals are stone
    wood_tiles = mineral_tiles - gold_tiles - iron_tiles - stone_tiles  # Remaining ~60% are wood
    
    print(f"Map size: {width}x{height} = {total_tiles} tiles")
    print(f"Difficulty: {difficulty}")
    print(f"Water: {water_percent}% = {water_tiles} tiles")
    print(f"Minerals: {mineral_percent}% = {mineral_tiles} tiles")
    print(f"  - Gold: 7% of minerals = {gold_tiles} tiles")
    print(f"  - Iron: 13% of minerals = {iron_tiles} tiles")
    print(f"  - Stone: 20% of minerals = {stone_tiles} tiles")
    print(f"  - Wood: 60% of minerals = {wood_tiles} tiles")
    
    # First place water features with clustering
    placed_water = 0
    water_seeds = min(water_tiles // 10, 15)  # Use at most 15 seed points
    water_seeds = max(water_seeds, 3)  # At least 3 seed points
    
    water_per_seed = water_tiles // water_seeds
    
    for _ in range(water_seeds):
        if placed_water >= water_tiles:
            break
            
        # Place a water seed
        x = random.randint(2, width - 3)
        y = random.randint(2, height - 3)
        
        # Skip if already water
        if terrain[y][x] != 0:
            continue
            
        # Define size of this water body (avoid one large body consuming everything)
        size = min(random.randint(5, 15), water_per_seed)
        
        # Generate water cluster
        placed_water += generate_water_pattern(terrain, x, y, size, width, height)
    
    # If we still have water to place, add random individual water tiles
    remaining_water = water_tiles - placed_water
    attempts = 0
    
    while remaining_water > 0 and attempts < remaining_water * 3:
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        
        if terrain[y][x] == 0:  # Only place on normal terrain
            terrain[y][x] = 1  # Water
            remaining_water -= 1
        
        attempts += 1
    
    # Now place minerals - first distribute them individually
    mineral_placement_order = []
    
    # Add gold tiles
    for _ in range(gold_tiles):
        mineral_placement_order.append(2)  # Gold
    
    # Add iron tiles
    for _ in range(iron_tiles):
        mineral_placement_order.append(3)  # Iron
    
    # Add stone tiles
    for _ in range(stone_tiles):
        mineral_placement_order.append(5)  # Stone (code 5)
    
    # Add wood tiles
    for _ in range(wood_tiles):
        mineral_placement_order.append(4)  # Wood
    
    # Shuffle the placement order
    random.shuffle(mineral_placement_order)
    
    # Attempt to place each mineral (with some clustering)
    to_place = len(mineral_placement_order)
    placed = 0
    cluster_chance = 0.3  # 30% chance to try to form a small cluster
    
    for mineral_type in mineral_placement_order:
        # Try to place the mineral
        attempts = 0
        max_attempts = 10  # Try up to 10 times to find a suitable spot
        
        while attempts < max_attempts:
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            
            if terrain[y][x] == 0:  # Only place on normal terrain
                terrain[y][x] = mineral_type
                placed += 1
                
                # Try to form a small cluster (occasionally)
                if random.random() < cluster_chance:
                    # Try to add one adjacent mineral of the same type
                    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                    random.shuffle(directions)
                    
                    for dx, dy in directions:
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < width and 0 <= ny < height and 
                            terrain[ny][nx] == 0):
                            terrain[ny][nx] = mineral_type
                            placed += 1
                            break  # Only add one adjacent tile
                
                break  # Successfully placed
            
            attempts += 1
    
    print(f"Placed {placed} out of {to_place} minerals")
    
    return terrain

def generate_water_pattern(terrain, x, y, size, width, height):
    """Generate a natural-looking water body. Returns the number of water tiles placed."""
    # Mark the center as water
    if terrain[y][x] != 0:  # Already something else
        return 0
        
    terrain[y][x] = 1
    placed = 1
    
    # Generate water in a randomized pattern around the center
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    queue = [(x, y, size)]
    
    while queue and placed < size:
        cx, cy, remaining_size = queue.pop(0)
        if remaining_size <= 0:
            continue
        
        # Choose random directions to expand
        random.shuffle(directions)
        for dx, dy in directions[:random.randint(1, min(4, remaining_size))]:
            nx, ny = cx + dx, cy + dy
            if (0 <= nx < width and 0 <= ny < height and 
                terrain[ny][nx] == 0 and placed < size):
                terrain[ny][nx] = 1
                placed += 1
                # Continue expanding with reduced size
                if random.random() < 0.7:  # 70% chance to continue
                    queue.append((nx, ny, remaining_size - 1))
    
    return placed

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

def find_distant_valid_position(map_data):
    """
    Find the furthest position from the player's start point where we can place 2 units without water
    """
    width = map_data.get("width", 30)
    height = map_data.get("height", 15)
    terrain = map_data.get("terrain", [])
    player_x, player_y = map_data.get("startPoint", [15, 7])
    
    # Create a list to store all valid positions with their distances
    valid_positions = []
    
    # Check all positions on the map
    for y in range(height):
        for x in range(width):
            # Skip water tiles
            if terrain and len(terrain) > y and len(terrain[y]) > x and terrain[y][x] != 1:
                # Calculate squared distance from player start (no need for square root yet)
                squared_distance = (x - player_x)**2 + (y - player_y)**2
                
                # Check if this position has at least one adjacent non-water position
                has_valid_adjacent = False
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
                
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < width and 0 <= ny < height and 
                        terrain and len(terrain) > ny and len(terrain[ny]) > nx and terrain[ny][nx] != 1):
                        has_valid_adjacent = True
                        break
                
                if has_valid_adjacent:
                    # Store position and its squared distance
                    valid_positions.append(([x, y], squared_distance))
    
    # Sort positions by distance (furthest first)
    valid_positions.sort(key=lambda item: item[1], reverse=True)
    
    # Return the furthest valid position if we found any
    if valid_positions:
        return valid_positions[0][0]  # Return just the position coordinates
    
    # Fallback to a position that's at least not close to the player
    attempts = 100
    while attempts > 0:
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        # Ensure position is somewhat far from player start
        min_distance = (width**2 + height**2)**0.5 / 4
        distance = ((x - player_x)**2 + (y - player_y)**2)**0.5
        
        # Check if the position is valid and has a valid adjacent position
        if distance >= min_distance and terrain and terrain[y][x] != 1:
            # Check for adjacent valid positions
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                nx, ny = x + dx, y + dy
                if (0 <= nx < width and 0 <= ny < height and terrain[ny][nx] != 1):
                    return [x, y]  # Found a position with a valid adjacent space
        
        attempts -= 1
    
    # Last resort: Return a position in the first quadrant of the map
    # We'll still check for adjacency to ensure two units can be placed
    for y in range(height // 2):
        for x in range(width // 2):
            if terrain and terrain[y][x] != 1:
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < width and 0 <= ny < height and terrain[ny][nx] != 1):
                        return [x, y]
    
    # Ultimate fallback: Just return corner position and hope for the best
    return [1, 1]

def find_adjacent_valid_position(map_data, position):
    """
    Find a valid (non-water) position adjacent to the given position
    """
    width = map_data.get("width", 30)
    height = map_data.get("height", 15)
    terrain = map_data.get("terrain", [])
    x, y = position
    
    # Check all adjacent positions (including diagonals)
    directions = [
        (1, 0), (-1, 0), (0, 1), (0, -1),  # Cardinal directions first
        (1, 1), (1, -1), (-1, 1), (-1, -1)  # Then diagonals
    ]
    
    for dx, dy in directions:
        new_x = x + dx
        new_y = y + dy
        
        # Check if position is within map bounds
        if 0 <= new_x < width and 0 <= new_y < height:
            # Check if position is not water
            if terrain and len(terrain) > new_y and len(terrain[new_y]) > new_x and terrain[new_y][new_x] != 1:
                return [new_x, new_y]
    
    # If no valid adjacent position found, return original position
    return position

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
            
        # Find a distant valid position for AI settler
        ai_start_position = find_distant_valid_position(map_data)
        
        # Create AI settler
        ai_settler = get_troop_type("settler", ai_start_position[:])  # Create a copy of the position list
        
        # Find adjacent valid position for AI warrior
        ai_warrior_position = find_adjacent_valid_position(map_data, ai_start_position)
        
        # Create AI warrior
        ai_warrior = get_troop_type("warrior", ai_warrior_position[:])  # Create a copy of the position list
            
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
                    "wood": 20,
                    "stone": 20,
                    "iron": 10
                },
            },
            "ia": {
                "units": [ai_settler, ai_warrior],
                "cities": [],
                "resources": {
                    "food": 100,
                    "gold": 50,
                    "wood": 20,
                    "stone": 20,
                    "iron": 10
                },
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
        games_cursor = db.games.find({"username": username}).sort("last_saved", -1)
        
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
            "turns": 3,
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
            "turns": 5,
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
            "turns": 8,
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
            "turns": 6,
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
            "turns": 7,
            "position": [0, 0],
            "movement": 2,
            "cost": {
                "food": 50,
                "gold": 20
            },
            "abilities": ["build_improvement"],
            "description": "Constructs improvements on the city"
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


def get_building_types():
    #Define different building types like sawmill, quarry, farm, etc.
    building_types = [
        {
            "type_id": "Sawmill",
            "name": "Sawmill",
            "category": "production",
            "turns": 3,
            "cost": {
                "wood": 20,
                "stone": 20
            },
            "description": "Produces wood over time"
        },
        { 
            "type_id": "Quarry",
            "name": "Quarry",
            "category": "production",
            "turns": 5,
            "cost": {
                "wood": 30, 
                "stone": 20
            },
            "description": "Produces stone over time"
        },
        {
            "type_id": "Farm",
            "name": "Farm",
            "category": "production",
            "turns": 3,
            "cost": {
                "wood": 40
            },
            "description": "Produces food over time"
        },
        {
            "type_id": "Iron mine",
            "name": "Iron mine",
            "category": "production",
            "turns": 5,
            "cost": {
                "wood": 50,
                "stone": 50
            },
            "description": "Produces iron over time"
        }, 
        {
            "type_id": "Gold mine",
            "name": "Gold mine",
            "category": "production",
            "turns": 7,
            "cost": {
                "wood": 50,
                "stone": 70
            },
            "description": "Produces gold over time"
        }

    ]

    return building_types

def get_building_type(type_id):
    """
    Get a specific building type by its ID
    """
    building_types = get_building_types()
    for building_type in building_types:
        if building_type["type_id"] == type_id:
            return building_type
    return None

def add_building_to_city(city_id, type_id):
    """
    Add a new building to a city
    """
    game = session.get('game')
    if not game or "cities" not in game:
        return False, "No cities found"

    city = next((c for c in game["cities"] if c["id"] == city_id), None)
    if not city:
        return False, "City not found"

    building_type = get_building_type(type_id)
    if not building_type:
        return False, "Invalid building type"

    # Check if the city has a buildings list, if not, create one
    if "buildings" not in city:
        city["buildings"] = []

    # Create the new building
    new_building = {
        "id": f"building-{datetime.now()}",
        "type_id": type_id,
        "name": building_type["name"],
        "category": building_type["category"],
        "cost": building_type["cost"],
        "output": building_type["output"],
        "description": building_type["description"]
    }

    city["buildings"].append(new_building)
    session['game'] = game
    return True, "Building added to city"

def get_civilization_types():
    """
    Get all available civilization types with their unique bonuses and starting resources
    """
    civilizations = [
        {
            "civ_id": "egypt",
            "name": "Egypt",
            "description": "Masters of agriculture and construction",
            "bonuses": [
                "Farms produce 20% more food",
                "Stone buildings cost 15% less"
            ],
            "starting_resources": {
                "food": 120,  # +20% food
                "gold": 50,
                "wood": 15,   # -25% wood (desert)
                "stone": 30,  # +50% stone (pyramids)
                "iron": 10
            },
            "starting_units": {
                "settler": 2,
                "warrior": 1
            }
        },
        {
            "civ_id": "greece",
            "name": "Greece",
            "description": "Masters of philosophy and naval warfare",
            "bonuses": [
                "Naval units have +1 movement",
                "Science buildings produce 15% more research"
            ],
            "starting_resources": {
                "food": 100,
                "gold": 60,   # +20% gold (trade)
                "wood": 25,   # +25% wood (shipbuilding)
                "stone": 25,   # +25% stone (architecture)
                "iron": 5     # -50% iron
            },
            "starting_units": {
                "settler": 1,
                "warrior": 1,
                "archer": 1  # Greece gets an extra archer
            }
        },
        {
            "civ_id": "rome",
            "name": "Rome",
            "description": "Masters of warfare and organization",
            "bonuses": [
                "All units gain +1 experience per combat",
                "Cities grow 10% faster"
            ],
            "starting_resources": {
                "food": 110,   # +10% food 
                "gold": 70,    # +40% gold (empire)
                "wood": 20,
                "stone": 20,
                "iron": 15     # +50% iron (weapons)
            },
            "starting_units": {
                "settler": 1,
                "warrior": 2  # Rome gets an extra warrior
            }
        },
        {
            "civ_id": "mongolia",
            "name": "Mongolia",
            "description": "Masters of cavalry and conquest",
            "bonuses": [
                "Mounted units have +1 movement",
                "Conquered cities produce no unhappiness"
            ],
            "starting_resources": {
                "food": 90,    # -10% food (nomadic)
                "gold": 40,    # -20% gold (less trade) 
                "wood": 15,    # -25% wood
                "stone": 15,   # -25% stone
                "iron": 25     # +150% iron (weapons)
            },
            "starting_units": {
                "settler": 1,
                "warrior": 1,
                "cavalry": 1  # Mongolia gets a cavalry unit
            }
        }
    ]
    return civilizations

def get_civilization_by_id(civ_id):
    """
    Get a specific civilization by its ID
    
    Args:
        civ_id: The ID of the civilization to retrieve
        
    Returns:
        The civilization data dictionary or None if not found
    """
    civilizations = get_civilization_types()
    for civ in civilizations:
        if civ["civ_id"] == civ_id:
            return civ
    return None

def apply_civilization_bonuses(game, civ_id):
    """
    Apply civilization-specific bonuses to a game
    
    Args:
        game: The game dictionary to modify
        civ_id: The ID of the civilization to apply
        
    Returns:
        The modified game dictionary
    """
    civilization = get_civilization_by_id(civ_id)
    if not civilization:
        # If no valid civilization, return the game unchanged
        return game
    
    # Apply resource bonuses
    if "starting_resources" in civilization:
        game["player"]["resources"] = civilization["starting_resources"]
    
    # Adjust starting units based on civilization
    if "starting_units" in civilization:
        # Clear existing units - we'll replace them completely
        game["player"]["units"] = []
        
        # Find starting position from the map data
        start_position = game["map_data"]["startPoint"] if "map_data" in game and "startPoint" in game["map_data"] else [15, 7]
        
        # Add the specified starting units
        for unit_type, count in civilization["starting_units"].items():
            for i in range(count):
                # Find a valid position for this unit
                # First unit at start position, others adjacent
                if len(game["player"]["units"]) == 0:
                    position = start_position[:]  # Copy to avoid reference issues
                else:
                    # Find an adjacent position
                    map_data = game["map_data"]
                    position = find_adjacent_valid_position(map_data, start_position)
                
                # Create the unit and add to player's units
                unit = get_troop_type(unit_type, position)
                if unit:
                    game["player"]["units"].append(unit)
        
    # Add the civilization info to the game
    game["player"]["civilization"] = {
        "id": civilization["civ_id"],
        "name": civilization["name"],
        "bonuses": civilization["bonuses"]
    }
    
    return game

def add_game_with_civilization(username, map_id, difficulty, civ_id=None, game_name="New Game"):
    """Add a new game for a user with optional civilization selection"""
    try:
        # First create a base game
        result = add_game(username, map_id, difficulty, game_name)
        
        # If no game was created or no civilization was specified, return
        if not result or not civ_id:
            return result
            
        # Get the created game
        game = session.get('game')
        if not game:
            return result
            
        # Apply civilization bonuses
        modified_game = apply_civilization_bonuses(game, civ_id)
        
        # Update the game in the session
        session['game'] = modified_game
        
        # Update the game in the database
        db = get_db()
        db.games.update_one(
            {"game_id": modified_game["game_id"]},
            {"$set": modified_game}
        )
        
        return result
    except Exception as e:
        print(f"Error adding game with civilization: {e}")
        return None
