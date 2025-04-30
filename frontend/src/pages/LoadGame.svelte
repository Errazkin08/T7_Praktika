<script>
  import { navigate } from '../router.js';
  import { user } from '../stores/auth.js';
  import { onMount } from 'svelte';
  import { gameAPI } from '../services/gameAPI.js';
  
  let savedGames = [];
  let isLoading = true;
  let error = null;
  
  // Redirect to welcome page if not logged in
  onMount(async () => {
    if (!$user) {
      navigate('/');
      return;
    }
    
    // Try to load saved games from API
    try {
      isLoading = true;
      savedGames = await gameAPI.getSavedGames();
    } catch (err) {
      console.error("Error loading saved games:", err);
      error = "Failed to load saved games. The API endpoint might not be implemented yet.";
      // For demo purposes, we can add some mock data
      savedGames = [
        /* This is just example data that would come from the API */
        {
          game_id: "sample1",
          name: "My First Empire",
          scenario_id: "europe_map_01",
          created_at: "2023-04-10T15:30:22Z",
          last_saved: "2023-04-12T18:45:33Z",
          turn: 12
        },
        {
          game_id: "sample2",
          name: "World Domination",
          scenario_id: "europe_map_02",
          created_at: "2023-04-05T09:20:15Z",
          last_saved: "2023-04-11T21:37:42Z",
          turn: 28
        }
      ];
    } finally {
      isLoading = false;
    }
  });
  
  function loadGame(gameId) {
    // In the future, this will load the game via API
    console.log(`Loading game: ${gameId}`);
    navigate('/map'); // For now, just navigate to the map
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
              <h3>{game.name}</h3>
              <p class="scenario-name">Scenario: {game.scenario_id}</p>
              <p class="game-details">
                Turn: {game.turn} | 
                Created: {formatDate(game.created_at)} | 
                Last Played: {formatDate(game.last_saved)}
              </p>
            </div>
            <button class="load-button">Load Game</button>
          </div>
        {/each}
      </div>
    {/if}
  </div>
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
</style>
