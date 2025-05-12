"""
Routes package for the application.
This package contains all the blueprints for the API routes.
"""
# Import all blueprints here to make them available when importing from routes
from .userRoute import user_blueprint
from .gameRoute import game_blueprint
from .mapRoute import map_blueprint
from .iaRoute import ia_blueprint
from .troopRoute import troop_blueprint
from .buildingRoute import building_blueprint
from .civilizationRoute import civilization_blueprint

# Make the blueprints available when importing from the package
__all__ = [
    'user_blueprint',
    'game_blueprint',
    'map_blueprint', 
    'ia_blueprint',
    'troop_blueprint',
    'building_blueprint',
    'civilization_blueprint'
]
