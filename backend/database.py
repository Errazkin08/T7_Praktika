from pymongo import MongoClient
from flask import g
import os
import datetime

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

def add_map(width, height, startPoint, difficulty):
    """
    Add a new map to the database
    """
    db = get_db()
    
    # Create a grid (vector of vectors) initialized with zeros
    grid = [[0 for _ in range(width)] for _ in range(height)]
    
    # Set the start point to 1
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
        "startPoint": startPoint
    }
    
    return db.maps.insert_one(map)

def add_game(username, map):
    """
    Add a new game to the database
    """
    db = get_db()
    game = {
        "username": username,
        "map":map
    }
    return db.games.insert_one(game)

