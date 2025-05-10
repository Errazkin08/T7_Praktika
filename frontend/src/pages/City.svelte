<script>
  import { onMount, onDestroy } from 'svelte';
  import { navigate } from '../router.js';
  import { user } from '../stores/auth.js';
  import { gameAPI } from '../services/gameAPI.js';
  import { gameState } from '../stores/gameState.js';
  
  let city = null;
  let isLoading = true;
  let error = null;
  let gameData = null;

  // Add state variable to track the active tab
  let activeTab = 'summary'; // Options: 'summary', 'production', 'buildings', 'citizens'
  
  // Function to change the active tab
  function setActiveTab(tab) {
    activeTab = tab;
  }
  
  onMount(async () => {
    try {
      // Add full-screen classes similar to Map component
      document.body.classList.add('city-active');
      document.documentElement.classList.add('city-active');

      if (!$user) {
        navigate('/');
        return;
      }
      
      // Get the current game session data
      gameData = await gameAPI.getCurrentGame();
      if (!gameData) {
        throw new Error("No hay datos de juego disponibles.");
      }
      
      // Get the selected city ID
      const selectedCityId = await gameAPI.getTemporaryData('selectedCityId');
      if (!selectedCityId) {
        throw new Error("No se ha seleccionado ninguna ciudad.");
      }
      
      // Find the city in the game data
      if (gameData.player && gameData.player.cities) {
        city = gameData.player.cities.find(c => c.id === selectedCityId);
      }
      
      if (!city) {
        throw new Error("No se encontró la ciudad seleccionada.");
      }
      
      isLoading = false;
    } catch (err) {
      console.error("Error loading city:", err);
      error = err.message;
      isLoading = false;
    }
  });
  
  onDestroy(() => {
    // Clean up classes when component is destroyed
    document.body.classList.remove('city-active');
    document.documentElement.classList.remove('city-active');
  });
  
  function returnToMap() {
    navigate('/map');
  }
</script>

<svelte:head>
  <title>Ciudad {city ? city.name : ''} - Civilization Game</title>
</svelte:head>

<div class="city-page game-view">
  <div class="city-background"></div>
  
  <button class="back-button" on:click={returnToMap}>← Volver al Mapa</button>
  
  {#if isLoading}
    <div class="loading-container">
      <div class="loading-spinner"></div>
      <h2>Cargando datos de la ciudad...</h2>
    </div>
  {:else if error}
    <div class="error-container">
      <h2>Error al cargar la ciudad</h2>
      <p>{error}</p>
      <button class="retry-button" on:click={returnToMap}>Volver al Mapa</button>
    </div>
  {:else if city}
    <div class="content-container">
      <div class="city-overlay-panel">
        <div class="city-header">
          <h1>{city.name}</h1>
          <div class="population-indicator">
            <span class="population-icon">👥</span>
            <span class="population-value">{city.population || 0}</span>
          </div>
        </div>
        
        <div class="city-tabs">
          <button 
            class="tab-button" 
            class:active={activeTab === 'summary'} 
            on:click={() => setActiveTab('summary')}
          >
            Resumen
          </button>
          <button 
            class="tab-button" 
            class:active={activeTab === 'production'} 
            on:click={() => setActiveTab('production')}
          >
            Producción
          </button>
          <button 
            class="tab-button" 
            class:active={activeTab === 'buildings'} 
            on:click={() => setActiveTab('buildings')}
          >
            Edificios
          </button>
          <button 
            class="tab-button" 
            class:active={activeTab === 'citizens'} 
            on:click={() => setActiveTab('citizens')}
          >
            Ciudadanos
          </button>
        </div>
        
        <div class="city-content">
          <!-- Summary Tab -->
          <div class="tab-content" class:active={activeTab === 'summary'}>
            <h3>Resumen de la Ciudad</h3>
            <p>Panel de gestión de la ciudad. Aquí se mostrarán más opciones en futuras implementaciones.</p>
            
            <div class="info-section">
              <h4>Información</h4>
              <p><strong>Posición:</strong> {Array.isArray(city.position) ? 
                `${city.position[0]}, ${city.position[1]}` : 
                `${city.position.x}, ${city.position.y}`}</p>
            </div>
            
            {#if city.buildings && city.buildings.length > 0}
              <div class="info-section">
                <h4>Edificios ({city.buildings.length})</h4>
                <ul class="buildings-list">
                  {#each city.buildings as building}
                    <li>{building.name || building}</li>
                  {/each}
                </ul>
              </div>
            {:else}
              <div class="info-section">
                <h4>Edificios</h4>
                <p>No hay edificios construidos en esta ciudad.</p>
              </div>
            {/if}
            
            {#if city.production && city.production.current_item}
              <div class="info-section">
                <h4>Producción Actual</h4>
                <div class="production-item">
                  <span class="production-name">{city.production.current_item}</span>
                  <div class="production-progress">
                    <div class="progress-bar" style="width: 30%;"></div>
                    <span class="progress-text">{city.production.turns_remaining} turnos restantes</span>
                  </div>
                </div>
              </div>
            {:else}
              <div class="info-section">
                <h4>Producción</h4>
                <p>No hay producción en curso.</p>
                <button class="start-production-button" on:click={() => setActiveTab('production')}>Iniciar Producción</button>
              </div>
            {/if}
          </div>
          
          <!-- Production Tab -->
          <div class="tab-content" class:active={activeTab === 'production'}>
            <h3>Producción</h3>
            <p>En este panel podrás gestionar qué construye tu ciudad.</p>
            
            <div class="info-section">
              <h4>Producción Actual</h4>
              {#if city.production && city.production.current_item}
                <div class="production-item">
                  <span class="production-name">{city.production.current_item}</span>
                  <div class="production-progress">
                    <div class="progress-bar" style="width: 30%;"></div>
                    <span class="progress-text">{city.production.turns_remaining} turnos restantes</span>
                  </div>
                  <button class="cancel-production-button">Cancelar Producción</button>
                </div>
              {:else}
                <p>No hay producción en curso.</p>
              {/if}
            </div>
            
            <div class="info-section">
              <h4>Construir</h4>
              <div class="production-options">
                <div class="production-option">
                  <h5>Unidades</h5>
                  <button class="production-button">Colono (10 turnos)</button>
                  <button class="production-button">Guerrero (5 turnos)</button>
                </div>
                <div class="production-option">
                  <h5>Edificios</h5>
                  <button class="production-button">Granero (8 turnos)</button>
                  <button class="production-button">Monumento (12 turnos)</button>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Buildings Tab -->
          <div class="tab-content" class:active={activeTab === 'buildings'}>
            <h3>Edificios</h3>
            <p>Gestiona los edificios de tu ciudad.</p>
            
            {#if city.buildings && city.buildings.length > 0}
              <div class="info-section buildings-grid">
                {#each city.buildings as building}
                  <div class="building-card">
                    <div class="building-icon">🏛️</div>
                    <h4>{building.name || building}</h4>
                    <p>Proporciona beneficios a la ciudad.</p>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="info-section">
                <p>No hay edificios construidos en esta ciudad.</p>
                <button class="action-button" on:click={() => setActiveTab('production')}>Construir Edificios</button>
              </div>
            {/if}
          </div>
          
          <!-- Citizens Tab -->
          <div class="tab-content" class:active={activeTab === 'citizens'}>
            <h3>Ciudadanos</h3>
            <p>Administra a los ciudadanos de tu ciudad.</p>
            
            <div class="info-section">
              <h4>Población Total: {city.population || 0}</h4>
              <div class="population-breakdown">
                <div class="citizen-group">
                  <span class="citizen-icon">👨‍🌾</span>
                  <span class="citizen-label">Agricultores:</span>
                  <span class="citizen-count">0</span>
                </div>
                <div class="citizen-group">
                  <span class="citizen-icon">⛏️</span>
                  <span class="citizen-label">Mineros:</span>
                  <span class="citizen-count">0</span>
                </div>
                <div class="citizen-group">
                  <span class="citizen-icon">🔨</span>
                  <span class="citizen-label">Artesanos:</span>
                  <span class="citizen-count">0</span>
                </div>
                <div class="citizen-group">
                  <span class="citizen-icon">📚</span>
                  <span class="citizen-label">Científicos:</span>
                  <span class="citizen-count">0</span>
                </div>
              </div>
            </div>
            
            <div class="info-section">
              <h4>Asignación de Trabajadores</h4>
              <p>Próximamente podrás asignar ciudadanos a diferentes tareas.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}

  {#if gameData && gameData.player && gameData.player.resources}
    <div class="resources-bar">
      <div class="resource food">
        <div class="resource-icon">🌾</div>
        <div class="resource-value">{gameData.player.resources.food || 0}</div>
      </div>
      <div class="resource gold">
        <div class="resource-icon">💰</div>
        <div class="resource-value">{gameData.player.resources.gold || 0}</div>
      </div>
      <div class="resource wood">
        <div class="resource-icon">🪵</div>
        <div class="resource-value">{gameData.player.resources.wood || 0}</div>
      </div>
      <div class="resource iron">
        <div class="resource-icon">⚙️</div>
        <div class="resource-value">{gameData.player.resources.iron || 0}</div>
      </div>
      <div class="resource stone">
        <div class="resource-icon">🪨</div>
        <div class="resource-value">{gameData.player.resources.stone || 0}</div>
      </div>
    </div>
  {/if}
</div>

<style>
  /* Full-screen styles similar to Map component */
  :global(body.city-active),
  :global(html.city-active) {
    overflow: hidden !important;
    margin: 0;
    padding: 0;
    height: 100%;
    width: 100%;
  }
  
  .city-page {
    position: absolute;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    color: white;
    z-index: 1000; /* Ensure it's above other app elements */
  }
  
  .city-background {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: url('./ia_assets/city.jpg');
    background-size: cover;
    background-position: center;
    z-index: -1;
  }
  
  .back-button {
    position: absolute;
    top: 20px;
    left: 20px;
    padding: 10px 20px;
    background-color: rgba(0, 0, 0, 0.7);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    z-index: 10;
    font-weight: bold;
    transition: background-color 0.2s;
  }
  
  .back-button:hover {
    background-color: rgba(0, 0, 0, 0.9);
  }
  
  .content-container {
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
    z-index: 1;
  }
  
  .city-overlay-panel {
    width: 90%;
    max-width: 800px;
    background-color: rgba(0, 0, 0, 0.7);
    border-radius: 10px;
    backdrop-filter: blur(5px);
    padding: 30px;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .city-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }
  
  .city-header h1 {
    margin: 0;
    font-size: 2.5rem;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  }
  
  .population-indicator {
    display: flex;
    align-items: center;
    font-size: 1.2rem;
    background-color: rgba(255, 255, 255, 0.1);
    padding: 5px 15px;
    border-radius: 20px;
  }
  
  .population-icon {
    margin-right: 8px;
  }
  
  .city-tabs {
    display: flex;
    margin-bottom: 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .tab-button {
    background: none;
    border: none;
    color: rgba(255, 255, 255, 0.7);
    padding: 10px 20px;
    cursor: pointer;
    font-size: 1rem;
    border-bottom: 3px solid transparent;
    transition: all 0.3s;
  }
  
  .tab-button:hover {
    color: white;
  }
  
  .tab-button.active {
    color: white;
    border-bottom-color: #4CAF50;
  }
  
  .city-content {
    background-color: rgba(0, 0, 0, 0.5);
    border-radius: 5px;
    padding: 20px;
    max-height: 50vh;
    overflow-y: auto;
  }
  
  .tab-content {
    display: none;
  }
  
  .tab-content.active {
    display: block;
  }
  
  .info-section {
    margin-bottom: 25px;
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 5px;
    padding: 15px;
  }
  
  .info-section h4 {
    margin-top: 0;
    margin-bottom: 10px;
    color: #4CAF50;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 5px;
  }
  
  .buildings-list {
    list-style-type: none;
    padding: 0;
    margin: 0;
  }
  
  .buildings-list li {
    padding: 5px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .buildings-list li:last-child {
    border-bottom: none;
  }
  
  .production-item {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  
  .production-progress {
    background-color: rgba(0, 0, 0, 0.3);
    border-radius: 10px;
    height: 20px;
    position: relative;
    overflow: hidden;
  }
  
  .progress-bar {
    height: 100%;
    background-color: #4CAF50;
    border-radius: 10px;
  }
  
  .progress-text {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: bold;
    text-shadow: 0 0 2px rgba(0, 0, 0, 0.8);
  }
  
  .start-production-button {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    margin-top: 10px;
  }
  
  .start-production-button:hover {
    background-color: #45a049;
  }
  
  /* New styles for the new tab content */
  .production-options {
    display: flex;
    gap: 15px;
    flex-wrap: wrap;
  }
  
  .production-option {
    flex: 1;
    min-width: 200px;
  }
  
  .production-button {
    display: block;
    width: 100%;
    padding: 8px;
    margin-bottom: 8px;
    background-color: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    color: white;
    cursor: pointer;
    text-align: left;
    transition: background-color 0.2s;
  }
  
  .production-button:hover {
    background-color: rgba(255, 255, 255, 0.2);
  }
  
  .cancel-production-button {
    margin-top: 10px;
    padding: 6px 12px;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .buildings-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 15px;
  }
  
  .building-card {
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 15px;
    text-align: center;
  }
  
  .building-icon {
    font-size: 2rem;
    margin-bottom: 10px;
  }
  
  .building-card h4 {
    margin: 0 0 10px 0;
    color: white;
    border-bottom: none;
  }
  
  .population-breakdown {
    margin-top: 15px;
  }
  
  .citizen-group {
    display: flex;
    align-items: center;
    margin-bottom: 8px;
  }
  
  .citizen-icon {
    margin-right: 10px;
    font-size: 1.2rem;
  }
  
  .citizen-label {
    flex: 1;
  }
  
  .citizen-count {
    font-weight: bold;
    min-width: 30px;
    text-align: right;
  }
  
  /* Loading and error styles */
  .loading-container, .error-container {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background-color: rgba(0, 0, 0, 0.7);
    z-index: 100;
    color: white;
    text-align: center;
  }
  
  .loading-spinner {
    border: 6px solid rgba(255, 255, 255, 0.3);
    border-top: 6px solid #4CAF50;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    animation: spin 1s linear infinite;
    margin-bottom: 20px;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .error-container h2 {
    color: #ff6b6b;
    margin-top: 0;
  }
  
  .retry-button {
    padding: 10px 20px;
    border: none;
    border-radius: 4px;
    background-color: #4CAF50;
    color: white;
    font-size: 16px;
    cursor: pointer;
    margin: 10px;
  }
  
  /* Resources bar (copied from Map component for consistency) */
  .resources-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: rgba(0, 0, 0, 0.7);
    color: white;
    display: flex;
    justify-content: center;
    padding: 8px 0;
    z-index: 100;
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.5);
  }
  
  .resource {
    display: flex;
    align-items: center;
    margin: 0 20px;
    background-color: rgba(50, 50, 50, 0.7);
    padding: 5px 15px;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    min-width: 90px;
    justify-content: center;
    transition: transform 0.2s;
  }
  
  .resource:hover {
    transform: translateY(-2px);
  }
  
  .resource-icon {
    font-size: 20px;
    margin-right: 8px;
  }
  
  .resource-value {
    font-weight: bold;
    font-size: 16px;
  }
  
  .resource.food {
    border-left: 3px solid #8BC34A;
  }
  
  .resource.gold {
    border-left: 3px solid #FFD700;
  }
  
  .resource.wood {
    border-left: 3px solid #795548;
  }
  
  .resource.iron {
    border-left: 3px solid #A8A9AD;
  }
  
  .resource.stone {
    border-left: 3px solid #777777;
  }
</style>
