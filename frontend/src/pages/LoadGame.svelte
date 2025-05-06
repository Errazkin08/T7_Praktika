<script>
  import { navigate } from '../router.js';
  import { user } from '../stores/auth.js';
  import { onMount } from 'svelte';
  import { gameAPI } from '../services/gameAPI.js';
  import { startGame } from '../stores/gameState.js';
  
  let savedGames = [];
  let isLoading = true;
  let error = null;
  let confirmingDelete = null;
  
  // Redirect to welcome page if not logged in
  onMount(async () => {
    if (!$user) {
      navigate('/');
      return;
    }
    
    // Load user's saved games
    await loadUserGames();
  });

  async function loadUserGames() {
    try {
      isLoading = true;
      error = null;
      savedGames = await gameAPI.getUserGames();
      console.log("Loaded saved games:", savedGames);
    } catch (err) {
      console.error("Error loading saved games:", err);
      error = "Failed to load saved games: " + err.message;
      // Fallback to sample data for testing
      savedGames = [
        {
          game_id: "sample1",
          name: "My First Empire",
          difficulty: "medium",
          created_at: new Date().toISOString(),
          last_saved: new Date().toISOString()
        }
      ];
    } finally {
      isLoading = false;
    }
  }
  
  async function loadGame(gameId) {
    try {
      isLoading = true;
      const gameData = await gameAPI.loadGame(gameId);
      
      // Initialize game state with loaded data
      startGame(
        gameData.name || "Loaded Game", 
        {
          mapId: gameData.map_id,
          difficulty: gameData.difficulty,
          width: gameData.map_data?.width || 30,
          height: gameData.map_data?.height || 15
        }
      );
      
      // Navigate to map
      navigate('/map');
    } catch (err) {
      console.error("Error loading game:", err);
      error = "Failed to load game: " + err.message;
      isLoading = false;
    }
  }
  
  async function deleteGame(event, gameId) {
    // Prevent event propagation to avoid loading the game
    event.stopPropagation();
    
    // Set the game to confirm deletion
    confirmingDelete = gameId;
  }
  
  async function confirmDelete() {
    if (!confirmingDelete) return;
    
    try {
      isLoading = true;
      await gameAPI.deleteUserGame(confirmingDelete);
      
      // Reload games list
      await loadUserGames();
      
      // Reset confirmation
      confirmingDelete = null;
    } catch (err) {
      console.error("Error deleting game:", err);
      error = "Failed to delete game: " + err.message;
    } finally {
      isLoading = false;
    }
  }
  
  function cancelDelete() {
    confirmingDelete = null;
  }
  
  function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  }
</script>

<div class="load-game-page">
  <div class="page-header">
    <h1>Load Game</h1>
    <button class="back-button" on:click={() => navigate('/home')}>
      Back to Dashboard
    </button>
  </div>
  
  <div class="games-container">
    {#if isLoading}
      <div class="loading-state">
        <p>Loading saved games...</p>
      </div>
    {:else if error}
      <div class="error-state">
        <p>{error}</p>
        <p class="note">Note: This is a development version, so we're showing sample data.</p>
      </div>
    {:else if savedGames.length === 0}
      <div class="empty-state">
        <h2>No Saved Games</h2>
        <p>You don't have any saved games yet. Start a new game first!</p>
        <button class="new-game-button" on:click={() => navigate('/new-game')}>
          Start New Game
        </button>
      </div>
    {:else}
      <div class="games-list">
        {#each savedGames as game}
          <div class="game-card" on:click={() => loadGame(game.game_id)}>
            <div class="game-info">
              <h3>{game.name || `Game ${game.game_id}`}</h3>
              <p class="scenario-name">Difficulty: {game.difficulty || 'medium'}</p>
              <p class="game-details">
                Created: {formatDate(game.created_at)}
              </p>
            </div>
            <div class="card-actions">
              <button class="load-button">Load Game</button>
              <button class="delete-button" on:click={(e) => deleteGame(e, game.game_id)}>
                Delete
              </button>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
  
  {#if confirmingDelete}
    <div class="confirm-dialog-overlay">
      <div class="confirm-dialog">
        <h3>Confirm Deletion</h3>
        <p>Are you sure you want to delete this game? This action cannot be undone.</p>
        <div class="dialog-buttons">
          <button class="cancel-button" on:click={cancelDelete}>Cancel</button>
          <button class="confirm-button" on:click={confirmDelete}>Delete</button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .load-game-page {
    max-width: 1000px;
    margin: 0 auto;
    padding: 2rem 1rem;
  }
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }
  
  .back-button {
    padding: 0.5rem 1rem;
    background-color: #6c757d;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .games-container {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 2rem;
    min-height: 400px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }
  
  .loading-state, .empty-state, .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 300px;
    text-align: center;
  }
  
  .error-state {
    color: #dc3545;
  }
  
  .error-state .note {
    color: #6c757d;
    margin-top: 1rem;
    font-style: italic;
  }
  
  .new-game-button, .load-button {
    padding: 0.7rem 1.5rem;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-top: 1rem;
  }
  
  .new-game-button:hover, .load-button:hover {
    background-color: #45a049;
    transform: translateY(-2px);
  }
  
  .games-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .game-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
    transition: all 0.2s ease;
  }
  
  .game-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
  }
  
  .game-info h3 {
    margin: 0 0 0.5rem;
    font-size: 1.3rem;
  }
  
  .scenario-name {
    color: #495057;
    margin: 0.3rem 0;
  }
  
  .game-details {
    color: #6c757d;
    font-size: 0.9rem;
    margin: 0.3rem 0;
  }
  
  .card-actions {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .delete-button {
    padding: 0.5rem 1rem;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .delete-button:hover {
    background-color: #c82333;
  }
  
  .confirm-dialog-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }
  
  .confirm-dialog {
    background-color: white;
    border-radius: 8px;
    padding: 1.5rem;
    max-width: 400px;
    width: 90%;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }
  
  .confirm-dialog h3 {
    margin-top: 0;
    color: #dc3545;
  }
  
  .dialog-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    margin-top: 1.5rem;
  }
  
  .cancel-button {
    padding: 0.5rem 1rem;
    background-color: #6c757d;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .confirm-button {
    padding: 0.5rem 1rem;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
</style>
