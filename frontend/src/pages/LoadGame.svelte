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
          map_size: { width: 30, height: 15 },
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
      error = null;
      
      console.log(`Attempting to load game with ID: ${gameId}`);
      
      // Fetch complete game data from server
      const gameData = await gameAPI.loadGame(gameId);
      console.log("Loaded game data:", gameData);
      
      // Extract map data - handle possibly different structures
      const mapData = gameData.map_data || {};
      const mapSize = gameData.map_size || {};
      
      // Use the values from the loaded game, with fallbacks
      const mapWidth = mapSize.width || mapData.width || 30;
      const mapHeight = mapSize.height || mapData.height || 15;
      const gameName = gameData.name || `Game ${gameId.substring(0, 6)}`;
      const difficulty = gameData.difficulty || 'medium';
      const mapId = gameData.map_id || (mapData._id ? mapData._id : null);
      
      // Get turn number (it might be called 'turn' in the database)
      const turnNumber = gameData.turnNumber || gameData.turn || 1;
      
      console.log(`Loading game "${gameName}" with map size ${mapWidth}x${mapHeight}`);
      
      // Initialize game state with loaded data
      startGame(
        gameName, 
        {
          mapId: mapId,
          difficulty: difficulty,
          width: mapWidth,
          height: mapHeight,
          turnNumber: turnNumber
        }
      );
      
      console.log("Game loaded and state updated, navigating to map");
      
      // Navigate to map to start playing (the backend already has the game in session)
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
  
  function getMapSizeDisplay(game) {
    if (game.map_size && typeof game.map_size.width !== 'undefined' && typeof game.map_size.height !== 'undefined') {
      return `${game.map_size.width}x${game.map_size.height}`;
    } else if (game.map_data && typeof game.map_data.width !== 'undefined' && typeof game.map_data.height !== 'undefined') {
      return `${game.map_data.width}x${game.map_data.height}`;
    }
    return 'Unknown size';
  }
  
  function getDifficultyDisplay(difficulty) {
    switch(difficulty) {
      case 'easy': return 'Fácil';
      case 'medium': return 'Media';
      case 'hard': return 'Difícil';
      default: return difficulty || 'Media';
    }
  }
</script>

<div class="load-game-page">
  <div class="page-header">
    <h1>Cargar Partida</h1>
    <button class="back-button" on:click={() => navigate('/home')}>
      Volver al Inicio
    </button>
  </div>
  
  <div class="games-container">
    {#if isLoading}
      <div class="loading-state">
        <div class="loading-spinner"></div>
        <p>Cargando partidas guardadas...</p>
      </div>
    {:else if error}
      <div class="error-state">
        <p>{error}</p>
        <button class="retry-button" on:click={loadUserGames}>
          Reintentar
        </button>
      </div>
    {:else if savedGames.length === 0}
      <div class="empty-state">
        <h2>No hay partidas guardadas</h2>
        <p>Aún no tienes partidas guardadas. ¡Comienza una nueva partida!</p>
        <button class="new-game-button" on:click={() => navigate('/new-game')}>
          Iniciar Nueva Partida
        </button>
      </div>
    {:else}
      <div class="games-list">
        {#each savedGames as game}
          <div class="game-card" on:click={() => loadGame(game.game_id)}>
            <div class="game-info">
              <h3>{game.name || `Partida ${game.game_id.substring(0, 6)}...`}</h3>
              
              <div class="game-stats">
                <div class="stat">
                  <span class="stat-label">Dificultad:</span>
                  <span class="stat-value">{getDifficultyDisplay(game.difficulty)}</span>
                </div>
                
                <div class="stat">
                  <span class="stat-label">Tamaño de mapa:</span>
                  <span class="stat-value">{getMapSizeDisplay(game)}</span>
                </div>
                
                {#if game.created_at}
                <div class="stat">
                  <span class="stat-label">Creado:</span>
                  <span class="stat-value">{formatDate(game.created_at)}</span>
                </div>
                {/if}
                
                {#if game.last_saved && game.last_saved !== game.created_at}
                <div class="stat">
                  <span class="stat-label">Guardado:</span>
                  <span class="stat-value">{formatDate(game.last_saved)}</span>
                </div>
                {/if}
              </div>
            </div>
            <div class="card-actions">
              <button class="load-button">Cargar Partida</button>
              <button class="delete-button" on:click={(e) => deleteGame(e, game.game_id)}>
                Borrar
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
        <h3>Confirmar Borrado</h3>
        <p>¿Estás seguro de que quieres borrar esta partida? Esta acción no se puede deshacer.</p>
        <div class="dialog-buttons">
          <button class="cancel-button" on:click={cancelDelete}>Cancelar</button>
          <button class="confirm-button" on:click={confirmDelete}>Borrar</button>
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
  
  .loading-spinner {
    border: 4px solid rgba(0, 0, 0, 0.1);
    border-left-color: #4CAF50;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .error-state {
    color: #dc3545;
  }
  
  .retry-button {
    padding: 0.5rem 1rem;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    margin-top: 1rem;
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
    cursor: pointer;
  }
  
  .game-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
  }
  
  .game-info {
    flex: 1;
  }
  
  .game-info h3 {
    margin: 0 0 0.5rem;
    font-size: 1.3rem;
  }
  
  .game-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.5rem;
    margin-top: 0.8rem;
  }
  
  .stat {
    display: flex;
    font-size: 0.9rem;
  }
  
  .stat-label {
    font-weight: bold;
    color: #495057;
    margin-right: 0.5rem;
  }
  
  .stat-value {
    color: #6c757d;
  }
  
  .card-actions {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    min-width: 130px;
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
