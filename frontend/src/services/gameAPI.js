/**
 * Game API service to interact with the backend
 */

const API_BASE_URL = '/api'; // Adjust this to match your backend URL

// Helper function for making authenticated API requests
async function fetchWithAuth(url, options = {}) {
  // Ensure credentials are included in all requests
  const fetchOptions = {
    ...options,
    credentials: 'include', // This ensures cookies are sent with the request
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    }
  };
  
  try {
    const response = await fetch(url, fetchOptions);
    
    if (response.status === 401) {
      console.error('Authentication error - user not logged in');
      // Optionally redirect to login page
      // window.location.href = '/login';
      throw new Error('User not logged in. Please log in to continue.');
    }
    
    return response;
  } catch (error) {
    console.error(`Error in fetchWithAuth for ${url}:`, error);
    throw error;
  }
}

// Temporary storage for sharing data between components
let temporaryDataStore = {};

// Store temporary data
export function storeTemporaryData(key, value) {
  temporaryDataStore[key] = value;
  // Also save in localStorage as backup
  try {
    localStorage.setItem(`temp_${key}`, JSON.stringify(value));
  } catch (e) {
    console.warn("Could not store temporary data in localStorage", e);
  }
  return value;
}

// Retrieve temporary data
export function getTemporaryData(key) {
  // First try in-memory storage
  if (temporaryDataStore[key] !== undefined) {
    return temporaryDataStore[key];
  }
  
  // Then try localStorage as backup
  try {
    const value = localStorage.getItem(`temp_${key}`);
    if (value) {
      const parsed = JSON.parse(value);
      temporaryDataStore[key] = parsed; // Update in-memory storage
      return parsed;
    }
  } catch (e) {
    console.warn("Could not retrieve temporary data from localStorage", e);
  }
  
  return null;
}

// Clear temporary data
export function clearTemporaryData(key) {
  if (key) {
    delete temporaryDataStore[key];
    try {
      localStorage.removeItem(`temp_${key}`);
    } catch (e) {
      console.warn("Could not remove temporary data from localStorage", e);
    }
  } else {
    temporaryDataStore = {};
    try {
      localStorage.clear();
    } catch (e) {
      console.warn("Could not clear localStorage", e);
    }
  }
}

// Add method to fetch troop types
async function getTroopTypes() {
  try {
    const response = await fetch(`${API_BASE_URL}/troops/types`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch troop types');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error fetching troop types:', error);
    throw error;
  }
}

/**
 * Get technology types
 */
async function getTechnologyTypes() {
  try {
    // Fix the URL path to correctly match the endpoint defined in the blueprint
    const response = await fetch(`${API_BASE_URL}/technology/types`, {
      method: 'GET',
      credentials: 'include'
    });
    
    // Add more detailed debugging to help identify the issue
    console.log(`Fetching technology types from: ${API_BASE_URL}/technology/types`);
    console.log(`Response status: ${response.status}`);
    
    if (!response.ok) {
      console.error(`Error fetching technology types: ${response.status} ${response.statusText}`);
      return [];
    }
    
    const data = await response.json();
    console.log("Technology types loaded:", data);
    return data;
  } catch (error) {
    console.error("Error in getTechnologyTypes:", error);
    return [];
  }
}

export const gameAPI = {
  /**
   * Get all available scenarios
   */
  async getScenarios() {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/scenarios`);
      if (!response.ok) {
        throw new Error(`Failed to fetch scenarios: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error fetching scenarios:", error);
      throw error;
    }
  },

  /**
   * Get a specific scenario by ID
   */
  async getScenario(scenarioId) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/scenarios/${scenarioId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch scenario: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error fetching scenario ${scenarioId}:`, error);
      throw error;
    }
  },

  /**
   * Save a game state
   */
  async saveGame(gameData) {
    console.log("Saving game data:", gameData);
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/games`, {
        method: 'POST',
        body: JSON.stringify(gameData),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to save game: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error("Error saving game:", error);
      throw error;
    }
  },

  /**
   * Update an existing game
   */
  async updateGame(gameId, gameData) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/games/${gameId}`, {
        method: 'PUT',
        body: JSON.stringify(gameData),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to update game: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Error updating game ${gameId}:`, error);
      throw error;
    }
  },

  /**
   * Load a game by ID
   */
  async loadGame(gameId) {
    try {
      console.log(`Requesting game data for ID: ${gameId}`);
      const response = await fetchWithAuth(`${API_BASE_URL}/games/${gameId}`);
      
      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = `Failed to load game: ${response.status}`;
        
        try {
          // Try to parse the error response as JSON
          const errorData = JSON.parse(errorText);
          console.error(`Error response (${response.status}):`, errorData);
          if (errorData.error) {
            errorMessage = errorData.error;
          }
        } catch (parseError) {
          console.error(`Error response (${response.status}):`, errorText);
        }
        
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      console.log("Successfully loaded game data:", data);
      return data;
    } catch (error) {
      console.error(`Error loading game ${gameId}:`, error);
      throw error;
    }
  },

  /**
   * Get all saved games
   */
  async getSavedGames() {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/games`);
      if (!response.ok) {
        throw new Error(`Failed to fetch saved games: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error fetching saved games:", error);
      throw error;
    }
  },

  /**
   * Create a new game
   */
  async createGame(gameData) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/games`, {
        method: 'POST',
        body: JSON.stringify(gameData),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create game: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error("Error creating game:", error);
      throw error;
    }
  },

  /**
   * Delete a saved game
   */
  async deleteGame(gameId) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/games/${gameId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete game: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Error deleting game ${gameId}:`, error);
      throw error;
    }
  },

  /**
   * Get map data from the server
   */
  async getMapData() {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/map`);
      if (!response.ok) {
        throw new Error(`Failed to fetch map data: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error fetching map data:", error);
      throw error;
    }
  },

  /**
   * Save map data to server
   */
  async saveMapData(mapData) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/map`, {
        method: 'POST',
        body: JSON.stringify(mapData),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to save map data: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error("Error saving map data:", error);
      throw error;
    }
  },

  /**
   * Get first map from database
   * Returns map data in format: { width, height, grid, startPoint, fogOfWar, difficulty }
   */
  async getFirstMap() {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/maps/first`);
      if (!response.ok) {
        throw new Error(`Failed to fetch map: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error fetching first map:", error);
      throw error;
    }
  },

  /**
   * Get all maps from the server
   */
  async getAllMaps() {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/maps`);
      if (!response.ok) {
        // If it's a 404, it might mean there are no maps - return empty array
        if (response.status === 404) {
          console.log("No maps found (404 response)");
          return [];
        }
        throw new Error(`Failed to fetch maps: ${response.status}`);
      }
      
      // Parse response - handle empty responses
      const responseText = await response.text();
      if (!responseText || responseText.trim() === '') {
        console.log("Empty response when fetching maps - returning empty array");
        return [];
      }
      
      // Parse the JSON response
      const maps = JSON.parse(responseText);
      console.log("Fetched maps:", maps);
      
      // If response is not an array, return empty array
      if (!Array.isArray(maps)) {
        console.warn("Maps response is not an array, returning empty array instead");
        return [];
      }
      
      // Normalize map data to ensure consistent property names
      return maps.map(map => {
        // Preserve the original ID from the database when possible
        let mapId;
        if (map._id) {
          mapId = map._id;
        } else if (map.map_id) {
          mapId = map.map_id;
        } else {
          // Only use generated ID as a last resort
          mapId = `map-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
          console.warn(`Generated fallback ID for map: ${mapId}`);
        }
        
        return {
          map_id: mapId,
          width: map.width || 30,
          height: map.height || 15,
          difficulty: map.difficulty || 'medium',
          name: map.name || `Mapa ${map.width || 30}x${map.height || 15}`,
          startPoint: map.startPoint || [15, 7],
          // Include other properties as needed
        };
      });
    } catch (error) {
      console.error("Error fetching maps:", error);
      // Return empty array instead of throwing error
      return [];
    }
  },

  /**
   * Get a map by ID
   */
  async getMapById(mapId) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/maps/${mapId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch map with ID ${mapId}: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error(`Error fetching map ${mapId}:`, error);
      throw error;
    }
  },

  /**
   * Create a new map
   */
  async createMap(mapData) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/maps`, {
        method: 'POST',
        body: JSON.stringify(mapData),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create map: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error("Error creating map:", error);
      throw error;
    }
  },

  /**
   * Create a new game with a selected map
   */
  async createGameWithMap(gameData) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/game`, {
        method: 'POST',
        body: JSON.stringify(gameData),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
        throw new Error(errorData.error || `Failed to create game: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error("Error creating game with map:", error);
      throw error;
    }
  },

  /**
   * Create a new game with civilization selection
   */
  async createGameWithCivilization(gameData) {
    try {
      const response = await fetch('/api/games/civilization', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          map_id: gameData.map_id,
          name: gameData.name,
          difficulty: gameData.difficulty,
          civ_id: gameData.player_civ_id,
          ai_civ_id: gameData.ai_civ_id
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error("Error creating game with civilization:", error);
      throw error;
    }
  },

  /**
   * Delete a map by ID
   */
  async deleteMap(mapId) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/maps/${mapId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete map: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Error deleting map ${mapId}:`, error);
      throw error;
    }
  },

  /**
   * Get all games for the current user
   */
  async getUserGames() {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/user/games`);
      if (!response.ok) {
        throw new Error(`Failed to fetch user games: ${response.status}`);
      }
      const games = await response.json();
      
      // Process games to ensure they have all required fields
      return games.map(game => ({
        ...game,
        name: game.name || `Game ${game.game_id.substring(0, 6)}`,
        difficulty: game.difficulty || 'medium',
        map_size: game.map_size || {
          width: game.map_data?.width || 30,
          height: game.map_data?.height || 15
        }
      }));
    } catch (error) {
      console.error("Error fetching user games:", error);
      throw error;
    }
  },

  /**
   * Delete a specific game for the current user
   */
  async deleteUserGame(gameId) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/user/games/${gameId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete game: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Error deleting game ${gameId}:`, error);
      throw error;
    }
  },

  /**
   * Get the current game from the session
   */
  async getCurrentGame() {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/current-game`);
      if (!response.ok) {
        throw new Error(`Failed to fetch current game: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching current game:', error);
      return null;
    }
  },

  /**
   * Update the game session data
   */
  async updateGameSession(gameData) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/update-game-session`, {
        method: 'POST',
        body: JSON.stringify(gameData),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: `Failed to update game session: ${response.status}` }));
        throw new Error(errorData.error || `Failed to update game session: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error("Error updating game session:", error);
      throw error;
    }
  },

  /**
   * Tells the backend to save the current game from session to the database.
   */
  async saveCurrentGameSession() {
    try {
      console.log("Requesting to save current game session to database...");
      const response = await fetchWithAuth(`${API_BASE_URL}/current-game/save`, { // Endpoint
        method: 'POST',
      });
      
      console.log("Response status from saveCurrentGameSession:", response.status);
      
      // Try to get the response text for better error reporting
      const responseText = await response.text();
      console.log("Response text:", responseText);
      
      // If not OK, try to parse the error or use the text
      if (!response.ok) {
        let errorMessage = `Failed to save current game session: ${response.status}`;
        
        try {
          // Try to parse as JSON if possible
          const errorData = JSON.parse(responseText);
          if (errorData.error || errorData.message) {
            errorMessage = errorData.error || errorData.message;
          }
        } catch (parseError) {
          // If can't parse as JSON, use the raw text if available
          if (responseText) {
            errorMessage = responseText;
          }
        }
        
        throw new Error(errorMessage);
      }
      
      // Try to parse the response JSON
      try {
        return JSON.parse(responseText);
      } catch (parseError) {
        console.warn("Could not parse response as JSON:", parseError);
        return { success: true, message: "Game saved successfully" };
      }
    } catch (error) {
      console.error("Error saving current game session:", error);
      throw error;
    }
  },

  /**
   * Get AI action based on current game state
   * @param {Object} gameState - Current game state data
   * @param {string} prompt - Optional prompt to guide AI
   * @param {string} rules - Optional game rules for AI
   */
  async getAIAction(gameState, prompt = '', rules = null) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/ai/action`, {
        method: 'POST',
        body: JSON.stringify({
          game_state: gameState,
          prompt: prompt,
          rules: rules
        }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = `Failed to get AI action: ${response.status}`;
        
        try {
          // Try to parse the error response as JSON
          const errorData = JSON.parse(errorText);
          if (errorData.error) {
            errorMessage = errorData.error;
          }
        } catch (parseError) {
          // If can't parse as JSON, use the raw text
          errorMessage = errorText || errorMessage;
        }
        
        throw new Error(errorMessage);
      }
      
      return await response.json();
    } catch (error) {
      console.error("Error getting AI action:", error);
      throw error;
    }
  },

  /**
   * Get a specific troop type by ID
   * @param {string} typeId - The ID of the troop type
   * @param {Array} position - Optional position [x, y] for the troop
   */
  async getTroopType(typeId, position = null) {
    try {
      // Include position as a query parameter only if provided
      let url = `${API_BASE_URL}/troops/types/${typeId}`;
      
      // If position is provided, add it as a query parameter
      if (position && Array.isArray(position)) {
        url += `?position=${JSON.stringify(position)}`;
      }
      
      console.log(`Requesting troop type ${typeId}${position ? ' with position ' + JSON.stringify(position) : ''}`);
      
      const response = await fetchWithAuth(url);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: `Failed to get troop type: ${response.status}` }));
        throw new Error(errorData.error || 'Failed to get troop type');
      }
      
      const troopData = await response.json();
      console.log(`Received troop data for ${typeId}:`, troopData);
      
      // If position was provided but not included in the response, add it
      if (position && (!troopData.position || !Array.isArray(troopData.position))) {
        troopData.position = position;
      }
      
      return troopData;
    } catch (error) {
      console.error("Error in getTroopType:", error);
      // Provide fallback data so the game can continue
      return {
        name: `Type ${typeId}`,
        type_id: typeId,
        movement: 2,
        health: 100,
        attack: 10,
        defense: 10,
        position: position // Include the position in fallback data
      };
    }
  },

  /**
   * Get a specific building type by ID
   */
  async getBuildingType(typeId) {
    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/buildings/types/${typeId}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: `Failed to get building type: ${response.status}` }));
        throw new Error(errorData.error || 'Failed to get building type');
      }

      return await response.json();
    } catch (error) {
      console.error("Error in getBuildingType:", error);
      // Provide fallback data
      return {
        name: `Building ${typeId}`,
        production_bonus: 10,
        defense_bonus: 10
      };
    }
  },

  /**
   * Get building types
   */
  async getBuildingTypes() {
    try {
      // Fix URL path - use API_BASE_URL directly instead of this.apiUrl
      const response = await fetch(`${API_BASE_URL}/buildings/types`, {
        method: 'GET',
        credentials: 'include'
      });
      
      if (!response.ok) {
        console.error(`Error fetching building types: ${response.status} ${response.statusText}`);
        return [];
      }
      
      const data = await response.json();
      console.log("Building types loaded:", data);
      return data;
    } catch (error) {
      console.error("Error in getBuildingTypes:", error);
      return [];
    }
  },

  getTroopTypes,

  getTechnologyTypes,

  storeTemporaryData,
  getTemporaryData,
  clearTemporaryData
};
