<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  
  let game = null;
  let isLoading = true;
  let errorMessage = '';
  let isCheatFormOpen = false;
  let cheatCode = '';
  let targetId = '';
  let targetType = 'city';
  
  onMount(async () => {
    await loadGame();
    
    // Detect Ctrl+Tab for cheat interface
    window.addEventListener('keydown', (e) => {
      if (e.ctrlKey && e.key === 'Tab') {
        e.preventDefault();
        toggleCheatForm();
      }
    });
    
    return () => {
      window.removeEventListener('keydown', (e) => {});
    };
  });
  
  async function loadGame() {
    try {
      const gameId = $page.params.gameId;
      
      const response = await fetch(`http://localhost:5000/api/games/${gameId}`, {
        method: 'GET',
        credentials: 'include'
      });
      
      if (!response.ok) {
        throw new Error('Failed to load game');
      }
      
      game = await response.json();
    } catch (error) {
      errorMessage = error.message || 'Error loading game';
    } finally {
      isLoading = false;
    }
  }
  
  function toggleCheatForm() {
    isCheatFormOpen = !isCheatFormOpen;
    if (!isCheatFormOpen) {
      cheatCode = '';
      targetId = '';
    }
  }
  
  async function applyCheat() {
    try {
      const gameId = $page.params.gameId;
      
      const response = await fetch(`http://localhost:5000/api/games/${gameId}/cheat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          cheat_code: cheatCode,
          target: {
            type: targetType,
            id: targetId
          }
        }),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Cheat failed');
      }
      
      const result = await response.json();
      
      if (result.success) {
        // Update game state with the new state from result
        game.game_state = result.game_state;
        if (!game.cheats_used.includes(cheatCode)) {
          game.cheats_used.push(cheatCode);
        }
        
        // Close cheat form
        toggleCheatForm();
      } else {
        errorMessage = result.message || 'Cheat failed';
      }
    } catch (error) {
      errorMessage = error.message || 'Error applying cheat';
    }
  }
  
  async function endTurn() {
    try {
      const gameId = $page.params.gameId;
      
      // Show loading state for AI turn
      isLoading = true;
      
      const response = await fetch(`http://localhost:5000/api/games/${gameId}/endTurn`, {
        method: 'POST',
        credentials: 'include'
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to end turn');
      }
      
      const result = await response.json();
      
      // Process the AI actions and animate them
      await processAIActions(result.ai_actions);
      
      // Reload the game state
      await loadGame();
      
    } catch (error) {
      errorMessage = error.message || 'Error ending turn';
      isLoading = false;
    }
  }
  
  async function processAIActions(actions) {
    // This would be where we animate the AI's turn
    // For now, just wait a bit to simulate the AI turn
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // In a real implementation, we would process each action sequentially
    // and animate them on the game board
  }
</script>

<svelte:head>
  <title>
    {#if game}
      {game.name} - Civilization Game
    {:else}
      Loading Game - Civilization Game
    {/if}
  </title>
</svelte:head>

<div class="game-container">
  {#if isLoading}
    <div class="loading-overlay">
      <div class="loading-spinner"></div>
      <div class="loading-text">
        {#if game}
          AI is thinking...
        {:else}
          Loading game...
        {/if}
      </div>
    </div>
  {/if}
  
  {#if errorMessage}
    <div class="error-message">{errorMessage}</div>
  {/if}
  
  {#if isCheatFormOpen}
    <div class="cheat-overlay" on:click={toggleCheatForm}>
      <div class="cheat-panel" on:click|stopPropagation>
        <h2>Cheat Console</h2>
        <div class="form-group">
          <label for="cheat-code">Cheat Code</label>
          <input 
            type="text" 
            id="cheat-code" 
            bind:value={cheatCode} 
            placeholder="Enter cheat code..." 
          />
        </div>
        
        <div class="form-group">
          <label for="target-type">Target Type</label>
          <select id="target-type" bind:value={targetType}>
            <option value="city">City</option>
            <option value="unit">Unit</option>
            <option value="resource">Resource</option>
          </select>
        </div>
        
        <div class="form-group">
          <label for="target-id">Target ID</label>
          <input 
            type="text" 
            id="target-id" 
            bind:value={targetId} 
            placeholder="Enter target ID..." 
          />
        </div>
        
        <div class="cheat-actions">
          <button class="cancel-button" on:click={toggleCheatForm}>Cancel</button>
          <button class="submit-button" on:click={applyCheat}>Apply Cheat</button>
        </div>
      </div>
    </div>
  {/if}
  
  {#if game}
    <div class="game-header">
      <h1>{game.name}</h1>
      <div class="game-info">
        <div><strong>Turn:</strong> {game.turn}</div>
        <div><strong>Current Player:</strong> {game.current_player}</div>
      </div>
    </div>
    
    <div class="game-ui">
      <div class="game-board">
        <!-- This would be replaced with an actual game board rendering -->
        <div class="placeholder-board">
          <h3>Game Board Placeholder</h3>
          <p>Interactive game map would render here</p>
          <p>Map Size: {game.game_state?.map?.size?.width || 0} x {game.game_state?.map?.size?.height || 0}</p>
        </div>
      </div>
      
      <div class="game-sidebar">
        <div class="resources-panel">
          <h3>Resources</h3>
          <div class="resources-grid">
            <div class="resource">
              <span class="resource-icon">🍞</span> 
              <span class="resource-value">{game.game_state?.player?.resources?.food || 0}</span>
            </div>
            <div class="resource">
              <span class="resource-icon">⚒️</span> 
              <span class="resource-value">{game.game_state?.player?.resources?.production || 0}</span>
            </div>
            <div class="resource">
              <span class="resource-icon">📚</span> 
              <span class="resource-value">{game.game_state?.player?.resources?.science || 0}</span>
            </div>
            <div class="resource">
              <span class="resource-icon">💰</span> 
              <span class="resource-value">{game.game_state?.player?.resources?.gold || 0}</span>
            </div>
          </div>
        </div>
        
        <div class="cities-panel">
          <h3>Cities ({game.game_state?.player?.cities?.length || 0})</h3>
          <div class="cities-list">
            {#if game.game_state?.player?.cities?.length > 0}
              {#each game.game_state.player.cities as city}
                <div class="city-item">
                  <div class="city-name">{city.name}</div>
                  <div class="city-details">Pop: {city.population}</div>
                  {#if city.production?.current_item}
                    <div class="city-production">
                      Building: {city.production.current_item} 
                      ({city.production.turns_remaining} turns)
                    </div>
                  {/if}
                </div>
              {/each}
            {:else}
              <div class="no-items">No cities founded yet</div>
            {/if}
          </div>
        </div>
        
        <div class="units-panel">
          <h3>Units ({game.game_state?.player?.units?.length || 0})</h3>
          <div class="units-list">
            {#if game.game_state?.player?.units?.length > 0}
              {#each game.game_state.player.units as unit}
                <div class="unit-item">
                  <div class="unit-name">{unit.type}</div>
                  <div class="unit-details">
                    Position: ({unit.position.x}, {unit.position.y})
                  </div>
                  <div class="unit-moves">
                    Moves: {unit.movement_points_left}/{unit.movement_points}
                  </div>
                </div>
              {/each}
            {:else}
              <div class="no-items">No units available</div>
            {/if}
          </div>
        </div>
        
        <div class="actions-panel">
          <button class="end-turn-button" on:click={endTurn}>
            End Turn
          </button>
        </div>
        
        <div class="debug-panel">
          <div>
            <strong>Cheats Used:</strong> 
            {game.cheats_used?.length ? game.cheats_used.join(', ') : 'None'}
          </div>
          <button class="cheat-button" on:click={toggleCheatForm}>
            Open Cheat Console (Ctrl+Tab)
          </button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .game-container {
    position: relative;
    height: calc(100vh - 16rem);
    margin-bottom: 4rem;
  }
  
  .loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }
  
  .loading-spinner {
    width: 50px;
    height: 50px;
    border: 5px solid #f3f3f3;
    border-top: 5px solid #3498db;
    border-radius: 50%;
    animation: spin 2s linear infinite;
  }
  
  .loading-text {
    color: white;
    margin-top: 1rem;
    font-size: 1.2rem;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .error-message {
    background-color: #ffdddd;
    color: #ff0000;
    padding: 0.5rem;
    margin-bottom: 1rem;
    border-radius: 4px;
    text-align: center;
  }
  
  .game-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #ddd;
  }
  
  .game-ui {
    display: flex;
    gap: 1rem;
    height: calc(100vh - 15rem);
  }
  
  .game-board {
    flex: 1;
    border: 1px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
    background-color: #f0f0f0;
  }
  
  .placeholder-board {
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    color: #666;
  }
  
  .game-sidebar {
    width: 300px;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .resources-panel, .cities-panel, .units-panel, .actions-panel, .debug-panel {
    background-color: #f9f9f9;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 1rem;
  }
  
  .resources-panel h3, .cities-panel h3, .units-panel h3 {
    margin-top: 0;
    margin-bottom: 0.5rem;
    font-size: 1rem;
    border-bottom: 1px solid #eee;
    padding-bottom: 0.5rem;
  }
  
  .resources-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }
  
  .resource {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .city-item, .unit-item {
    border-bottom: 1px solid #eee;
    padding: 0.5rem 0;
  }
  
  .city-item:last-child, .unit-item:last-child {
    border-bottom: none;
  }
  
  .city-name, .unit-name {
    font-weight: bold;
  }
  
  .city-details, .unit-details, .city-production, .unit-moves {
    font-size: 0.8rem;
    color: #666;
  }
  
  .end-turn-button {
    width: 100%;
    padding: 0.75rem;
    background-color: #e74c3c;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1.1rem;
    cursor: pointer;
  }
  
  .end-turn-button:hover {
    background-color: #c0392b;
  }
  
  .debug-panel {
    font-size: 0.8rem;
  }
  
  .cheat-button {
    margin-top: 0.5rem;
    width: 100%;
    padding: 0.5rem;
    background-color: #7f8c8d;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
  }
  
  .cheat-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }
  
  .cheat-panel {
    background-color: white;
    border-radius: 8px;
    padding: 1.5rem;
    width: 400px;
    max-width: 90%;
  }
  
  .cheat-panel h2 {
    margin-top: 0;
    margin-bottom: 1rem;
  }
  
  .cheat-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-top: 1rem;
  }
  
  .no-items {
    font-style: italic;
    color: #999;
    padding: 0.5rem 0;
  }
  
  .cities-list, .units-list {
    max-height: 200px;
    overflow-y: auto;
  }
</style>