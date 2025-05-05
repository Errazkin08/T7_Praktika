from pymongo import MongoClient
from flask import g, session
import os
import datetime
import random
import uuid

# MongoDB connection string - using environment variable for security
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://mongodb:27017/')

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

def add_map(width, height, startPoint, difficulty="easy"):
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
    
    # Set the start point to 1 in grid
    x, y = startPoint
    grid[y][x] = 1
    
    # For easy difficulty, set 2 more points around start point to 1
    if difficulty == "easy":
        # Define possible adjacent positions (up, down, left, right)
        adjacent = [(x, y-1), (x, y+1), (x-1, y), (x+1, y)]
        # Filter valid positions within grid boundaries
        valid_positions = [(nx, ny) for nx, ny in adjacent if 0 <= nx < width and 0 <= ny < height]
        # Choose up to 2 positions
        for i, (nx, ny) in enumerate(valid_positions):
            if i < 2:  # Only set up to 2 additional points
                grid[ny][nx] = 1
    
    # Create the map document
    map = {
        "width": width,
        "height": height,
        "grid": grid,
        "terrain": terrain,
        "startPoint": startPoint,
        "visibleObjects": []  # Initialize with an empty list
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
    return db.maps.find_one({}, {'_id': 0})

def add_game(username, difficulty, map):
    """
    Add a new game to the database
    """
    db = get_db()
    game = {
        "game_id": str(int(datetime.datetime.now().timestamp() * 1000) + 1),
        "username": username,
        "difficulty": difficulty,
        "map": map
    }
    #insert in session the actual game
    session['game'] = game
    return db.games.insert_one(game)

def save_game():
    """
    Save the current game in the session to the database
    """
    db = get_db()
    game = session.get('game')
    
    if game:
        # Save the game to the database
        db.games.delete_one({"game_id": game['game_id']})  # Remove old game if exists
        db.games.insert_one(game)
        return True
    return False

def delete_game(game_id):
    """
    Delete a game from the database
    """
    db = get_db()
    result = db.games.delete_one({"game_id": game_id})
    session.pop('game', None)  # Remove game from session
    return result.deleted_count > 0

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

def get_troop_type(type_id):
    """
    Get a specific troop type by its ID
    """
    troop_types = get_troop_types()
    for troop_type in troop_types:
        if troop_type["type_id"] == type_id:
            return troop_type
    return None

def add_troop_to_player(username, type_id, position):
    """
    Add a new troop to a player's army
    """
    db = get_db()
    
    # Get the troop type
    troop_type = get_troop_type(type_id)
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