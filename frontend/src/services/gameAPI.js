/**
 * Game API service to interact with the backend
 */

const API_BASE_URL = '/api'; // Adjust this to match your backend URL

export const gameAPI = {
  /**
   * Get all available scenarios
   */
  async getScenarios() {
    try {
      const response = await fetch(`${API_BASE_URL}/scenarios`);
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
      const response = await fetch(`${API_BASE_URL}/scenarios/${scenarioId}`);
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
      const response = await fetch(`${API_BASE_URL}/games`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
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
      const response = await fetch(`${API_BASE_URL}/games/${gameId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
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
      const response = await fetch(`${API_BASE_URL}/games/${gameId}`);
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
      const response = await fetch(`${API_BASE_URL}/games`);
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
   * Delete a saved game
   */
  async deleteGame(gameId) {
    try {
      const response = await fetch(`${API_BASE_URL}/games/${gameId}`, {
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
  }
};
