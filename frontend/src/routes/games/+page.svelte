<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  
  let games = [];
  let scenarios = [];
  let isLoading = true;
  let errorMessage = '';
  let isCreatingGame = false;
  let newGameName = '';
  let selectedScenario = '';
  
  onMount(async () => {
    await Promise.all([
      loadGames(),
      loadScenarios()
    ]);
  });
  
  async function loadGames() {
    try {
      const response = await fetch('http://localhost:5000/api/games', {
        method: 'GET',
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Failed to load games');
      }
      
      games = await response.json();
    } catch (error) {
      errorMessage = error.message || 'Error loading games';
    } finally {
      isLoading = false;
    }
  }
  
  async function loadScenarios() {
    try {
      const response = await fetch('http://localhost:5000/api/scenarios', {
        method: 'GET',
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Failed to load scenarios');
      }
      
      scenarios = await response.json();
      if (scenarios.length > 0) {
        selectedScenario = scenarios[0]._id;
      }
    } catch (error) {
      console.error('Error loading scenarios:', error);
    }
  }
  
  function toggleCreateGameForm() {
    isCreatingGame = !isCreatingGame;
    newGameName = '';
  }
  
  async function handleCreateGame() {
    try {
      const response = await fetch('http://localhost:5000/api/games', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          name: newGameName,
          scenario_id: selectedScenario
        }),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to create game');
      }
      
      const result = await response.json();
      
      // Add newly created game to list or reload games
      await loadGames();
      isCreatingGame = false;
      
      // Navigate to the new game
      goto(`/game/${result.game_id}`);
    } catch (error) {
      errorMessage = error.message || 'Error creating game';
    }
  }
  
  function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  }
</script>

<svelte:head>
  <title>My Games - Civilization Game</title>
</svelte:head>

<div class="games-container">
  <div class="header">
    <h1>My Games</h1>
    <button class="create-button" on:click={toggleCreateGameForm}>
      {isCreatingGame ? 'Cancel' : 'New Game'}
    </button>
  </div>
  
  {#if errorMessage}
    <div class="error-message">{errorMessage}</div>
  {/if}
  
  {#if isCreatingGame}
    <div class="create-game-form">
      <h2>Create New Game</h2>
      <div class="form-group">
        <label for="game-name">Game Name</label>
        <input 
          type="text" 
          id="game-name" 
          placeholder="Enter a name for your game" 
          bind:value={newGameName} 
          required 
        />
      </div>
      
      <div class="form-group">
        <label for="scenario">Scenario</label>
        <select id="scenario" bind:value={selectedScenario}>
          {#each scenarios as scenario}
            <option value={scenario._id}>{scenario.name} - {scenario.difficulty}</option>
          {/each}
        </select>
      </div>
      
      <div class="form-actions">
        <button class="cancel-button" on:click={toggleCreateGameForm}>Cancel</button>
        <button class="submit-button" on:click={handleCreateGame}>Create Game</button>
      </div>
    </div>
  {/if}
  
  {#if isLoading}
    <div class="loading">Loading your games...</div>
  {:else if games.length === 0}
    <div class="no-games">
      <p>You don't have any saved games.</p>
      <p>Click "New Game" to start playing!</p>
    </div>
  {:else}
    <div class="games-list">
      {#each games as game}
        <div class="game-card" on:click={() => goto(`/game/${game._id}`)}>
          <h3>{game.name}</h3>
          <div class="game-info">
            <div>
              <strong>Turn:</strong> {game.turn}
            </div>
            <div>
              <strong>Created:</strong> {formatDate(game.created_at)}
            </div>
            <div>
              <strong>Last played:</strong> {formatDate(game.last_saved)}
            </div>
          </div>
          <div class="card-footer">
            <span class="scenario-badge">{game.scenario_id}</span>
            {#if game.cheats_used && game.cheats_used.length > 0}
              <span class="cheat-badge">Cheats: {game.cheats_used.length}</span>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .games-container {
    margin: 0 auto;
    max-width: 900px;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }
  
  .create-button {
    padding: 0.5rem 1rem;
    background-color: #4c66af;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .create-button:hover {
    background-color: #3a4f8a;
  }
  
  .create-game-form {
    background-color: #f9f9f9;
    padding: 1.5rem;
    margin-bottom: 2rem;
    border-radius: 8px;
    border: 1px solid #ddd;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: bold;
  }
  
  input, select {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
  
  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    margin-top: 1rem;
  }
  
  .cancel-button {
    padding: 0.5rem 1rem;
    background-color: #f1f1f1;
    border: 1px solid #ccc;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .submit-button {
    padding: 0.5rem 1rem;
    background-color: #4c66af;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .error-message {
    background-color: #ffdddd;
    color: #ff0000;
    padding: 0.5rem;
    margin-bottom: 1rem;
    border-radius: 4px;
    text-align: center;
  }
  
  .loading, .no-games {
    text-align: center;
    padding: 2rem;
    color: #666;
  }
  
  .games-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1.5rem;
  }
  
  .game-card {
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
  }
  
  .game-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
  }
  
  .game-card h3 {
    margin-top: 0;
    margin-bottom: 0.5rem;
  }
  
  .game-info {
    font-size: 0.9rem;
    margin-bottom: 1rem;
  }
  
  .game-info div {
    margin-bottom: 0.25rem;
  }
  
  .card-footer {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
  }
  
  .scenario-badge, .cheat-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 100px;
    color: white;
  }
  
  .scenario-badge {
    background-color: #4c66af;
  }
  
  .cheat-badge {
    background-color: #e67e22;
  }
</style>