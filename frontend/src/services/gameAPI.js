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
      const response = await fetchWithAuth(`${API_BASE_URL}/games/${gameId}`);
      if (!response.ok) {
        throw new Error(`Failed to load game: ${response.status}`);
      }
      return await response.json();
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
        throw new Error(`Failed to fetch maps: ${response.status}`);
      }
      const maps = await response.json();
      
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
      throw error;
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
  }
};
