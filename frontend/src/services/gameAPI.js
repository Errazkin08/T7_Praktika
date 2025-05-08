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
      const response = await fetchWithAuth(`${API_BASE_URL}/current-game/save`, { // Endpoint from app.py
        method: 'POST',
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: `Failed to save current game session: ${response.status}` }));
        throw new Error(errorData.error || `Failed to save current game session: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error saving current game session:", error);
      throw error;
    }
  },
};
