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
  let troopTypes = [];
  let loadingTroopTypes = false;
  let activeTab = 'summary';
  let selectedTroopType = null;

  function setActiveTab(tab) {
    activeTab = tab;
  }

  async function fetchTroopTypes() {
    loadingTroopTypes = true;
    try {
      const types = await gameAPI.getTroopTypes();
      troopTypes = types;
      console.log("Troop types loaded:", troopTypes);
    } catch (err) {
      console.error("Error loading troop types:", err);
    } finally {
      loadingTroopTypes = false;
    }
  }

  function toggleTroopSelection(troopType, index) {
    const troopId = troopType.id || `troop-${index}`;
    
    if (selectedTroopType && selectedTroopType._uniqueId === troopId) {
      selectedTroopType = null;
    } else {
      selectedTroopType = {
        ...troopType,
        _uniqueId: troopId
      };
      console.log("Selected troop:", selectedTroopType);
    }
  }

  async function startTrainingTroop(troopType) {
    try {
      if (!city) {
        showToastNotification("Error: No hay ciudad seleccionada", "error");
        return;
      }
      
      // Check if there's already production in progress
      if (city.production && city.production.current_item) {
        showToastNotification("Ya hay una unidad en producción", "error");
        return;
      }
      
      // Get the number of turns required for this troop type
      const turnsToComplete = troopType.turns_to_build || troopType.turns || 3;
      
      // Get the proper type/id for production
      // Fix: Use type_id instead of type
      const troopTypeId = troopType.id || troopType.type_id;
      
      if (!troopTypeId) {
        showToastNotification("Error: No se puede identificar el tipo de tropa", "error");
        return;
      }
      
      console.log("Setting troop for production:", troopTypeId);
      
      // Create the production object with the proper current_item
      city.production = {
        current_item: troopTypeId,
        turns_remaining: turnsToComplete
      };
      
      console.log("Setting production:", city.production);
      
      // Update the game data with the new production
      if (gameData && gameData.player && gameData.player.cities) {
        const cityIndex = gameData.player.cities.findIndex(c => c.id === city.id);
        if (cityIndex !== -1) {
          gameData.player.cities[cityIndex].production = city.production;
          
          // Save changes to game session
          await gameAPI.updateGameSession(gameData);
          
          // Clear selected troop to hide the expanded panel
          selectedTroopType = null;
          
          // Show feedback messages - now this will create a visual toast
          showToastNotification(`¡Iniciada producción de ${troopType.name}!`, "success");
          
          // Switch to the summary tab to show the production info
          setActiveTab('summary');
        }
      }
    } catch (err) {
      console.error("Error starting troop production:", err);
      showToastNotification("Error al iniciar la producción", "error");
    }
  }

  function showToastNotification(message, type = "info") {
    console.log(`[${type}] ${message}`);
    
    // Create a toast element
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    toast.innerHTML = `<span class="toast-message">${message}</span>`;
    
    // Create container if it doesn't exist
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    
    // Add toast to container
    container.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  function returnToMap() {
    navigate('/map');
  }

  function getDefaultTroopIcon(type) {
    switch (type && type.toLowerCase()) {
      case 'warrior': return { type: 'image', url: './ia_assets/warrior.png' };
      case 'settler': return { type: 'image', url: './ia_assets/settler.png' };
      case 'archer': return { type: 'emoji', value: '🏹' };
      case 'cavalry': return { type: 'emoji', value: '🐎' };
      case 'builder': return { type: 'emoji', value: '🔨' };
      default: return { type: 'emoji', value: '👤' };
    }
  }

  onMount(async () => {
    try {
      document.body.classList.add('city-active');
      document.documentElement.classList.add('city-active');

      if (!$user) {
        navigate('/');
        return;
      }
      
      gameData = await gameAPI.getCurrentGame();
      if (!gameData) {
        throw new Error("No hay datos de juego disponibles.");
      }
      
      const selectedCityId = await gameAPI.getTemporaryData('selectedCityId');
      if (!selectedCityId) {
        throw new Error("No se ha seleccionado ninguna ciudad.");
      }
      
      if (gameData.player && gameData.player.cities) {
        city = gameData.player.cities.find(c => c.id === selectedCityId);
      }
      
      if (!city) {
        throw new Error("No se encontró la ciudad seleccionada.");
      }
      
      await fetchTroopTypes();
      
      isLoading = false;
    } catch (err) {
      console.error("Error loading city:", err);
      error = err.message;
      isLoading = false;
    }
  });

  onDestroy(() => {
    document.body.classList.remove('city-active');
    document.documentElement.classList.remove('city-active');
  });
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
              {@const productionType = troopTypes.find(t => t.id === city.production.current_item || t.type_id === city.production.current_item)}
              <div class="info-section production-status-section">
                <h4>Producción Actual</h4>
                <div class="production-item">
                  <div class="production-icon">
                    {#if productionType && getDefaultTroopIcon(productionType.name).type === 'image'}
                      <img src={getDefaultTroopIcon(productionType.name).url} alt={productionType ? productionType.name : city.production.current_item} class="production-image" />
                    {:else}
                      <span class="production-emoji">
                        {productionType ? getDefaultTroopIcon(productionType.name).value : '🛠️'}
                      </span>
                    {/if}
                  </div>
                  <div class="production-details">
                    <span class="production-name">
                      {productionType ? productionType.name : city.production.current_item}
                    </span>
                    <div class="production-progress">
                      <div class="progress-bar" style="width: {100 - (city.production.turns_remaining * 100 / (productionType?.turns_to_build || productionType?.turns || 3))}%;"></div>
                      <span class="progress-text">{city.production.turns_remaining} turnos restantes</span>
                    </div>
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
          
          <div class="tab-content" class:active={activeTab === 'production'}>
            <h3>Producción</h3>
            <p>En este panel podrás gestionar qué construye tu ciudad.</p>
            
            <div class="info-section">
              <h4>Producción Actual</h4>
              {#if city.production && city.production.current_item}
                {@const productionType = troopTypes.find(t => t.id === city.production.current_item || t.type_id === city.production.current_item)}
                <div class="production-item">
                  <div class="production-icon">
                    {#if productionType && getDefaultTroopIcon(productionType.name).type === 'image'}
                      <img src={getDefaultTroopIcon(productionType.name).url} alt={productionType ? productionType.name : city.production.current_item} class="production-image" />
                    {:else}
                      <span class="production-emoji">
                        {productionType ? getDefaultTroopIcon(productionType.name).value : '🛠️'}
                      </span>
                    {/if}
                  </div>
                  <div class="production-details">
                    <span class="production-name">
                      {productionType ? productionType.name : city.production.current_item}
                    </span>
                    <div class="production-progress">
                      <div class="progress-bar" style="width: {100 - (city.production.turns_remaining * 100 / (productionType?.turns_to_build || productionType?.turns || 3))}%;"></div>
                      <span class="progress-text">{city.production.turns_remaining} turnos restantes</span>
                    </div>
                    <button class="cancel-production-button">Cancelar Producción</button>
                  </div>
                </div>
              {:else}
                <p>No hay producción en curso. Selecciona una unidad para comenzar la producción.</p>
              {/if}
            </div>
            
            <div class="info-section">
              <h4>Construir</h4>
              <div class="production-options">
                <div class="production-option">
                  <h5>Unidades</h5>
                  {#if loadingTroopTypes}
                    <p>Cargando tipos de tropas...</p>
                  {:else if troopTypes.length === 0}
                    <p>No hay tipos de tropas disponibles.</p>
                  {:else}
                    {#each troopTypes as troopType, index}
                      {@const uniqueKey = troopType.id || `troop-type-${index}`}
                      {@const iconData = getDefaultTroopIcon(troopType.name)}
                      <div class="troop-container">
                        <button 
                          class="production-button troop-button" 
                          class:expanded={selectedTroopType && (selectedTroopType._uniqueId === (troopType.id || `troop-${index}`))}
                          on:click={() => toggleTroopSelection(troopType, index)}
                        >
                          <div class="troop-info">
                            {#if iconData.type === 'image'}
                              <div class="troop-image-container">
                                <img src={iconData.url} alt={troopType.name} class="troop-image" />
                              </div>
                            {:else}
                              <span class="troop-icon">{iconData.value}</span>
                            {/if}
                            
                            <div class="troop-details">
                              <span class="troop-name">{troopType.name}</span>
                              <span class="troop-cost">{troopType.cost ? `${troopType.cost.food || 0}🌾 ${troopType.cost.gold || 0}💰` : 'Costo no disponible'}</span>
                            </div>
                            <span class="production-turns">
                              <span class="turns-icon">🕒</span>
                              <span class="turns-count">{troopType.turns_to_build || troopType.turns || '?'}</span>
                              <span class="turns-label">turnos</span>
                            </span>
                          </div>
                        </button>
                        
                        {#if selectedTroopType && (selectedTroopType._uniqueId === (troopType.id || `troop-${index}`))}
                          <div class="troop-details-expanded">
                            <div class="troop-attributes">
                              {#if troopType.description}
                                <p class="troop-description">{troopType.description}</p>
                              {/if}
                              
                              <div class="attributes-grid">
                                {#if troopType.attack !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">⚔️</span>
                                    <span class="attribute-label">Ataque:</span>
                                    <span class="attribute-value">{troopType.attack}</span>
                                  </div>
                                {/if}
                                
                                {#if troopType.defense !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">🛡️</span>
                                    <span class="attribute-label">Defensa:</span>
                                    <span class="attribute-value">{troopType.defense}</span>
                                  </div>
                                {/if}
                                
                                {#if troopType.health !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">❤️</span>
                                    <span class="attribute-label">Salud:</span>
                                    <span class="attribute-value">{troopType.health}</span>
                                  </div>
                                {/if}
                                
                                {#if troopType.movement !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">👣</span>
                                    <span class="attribute-label">Movimiento:</span>
                                    <span class="attribute-value">{troopType.movement}</span>
                                  </div>
                                {/if}
                                
                                {#if troopType.range !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">🎯</span>
                                    <span class="attribute-label">Alcance:</span>
                                    <span class="attribute-value">{troopType.range}</span>
                                  </div>
                                {/if}
                              </div>
                              
                              <div class="troop-action">
                                <button class="train-button" on:click={() => startTrainingTroop(troopType)}>
                                  Entrenar {troopType.name}
                                </button>
                              </div>
                            </div>
                          </div>
                        {/if}
                      </div>
                    {/each}
                  {/if}
                </div>
                <div class="production-option">
                  <h5>Edificios</h5>
                  <button class="production-button">Granero (8 turnos)</button>
                  <button class="production-button">Monumento (12 turnos)</button>
                </div>
              </div>
            </div>
          </div>
          
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
    z-index: 1000;
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
  
  .troop-container {
    margin-bottom: 8px;
  }
  
  .troop-button {
    transition: background-color 0.2s, border-radius 0.2s;
  }
  
  .troop-button.expanded {
    background-color: rgba(76, 175, 80, 0.2);
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
    border-bottom: none;
  }
  
  .troop-details-expanded {
    background-color: rgba(0, 0, 0, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-top: none;
    padding: 12px;
    border-bottom-left-radius: 4px;
    border-bottom-right-radius: 4px;
    animation: slide-down 0.2s ease-out;
  }
  
  @keyframes slide-down {
    from {
      max-height: 0;
      opacity: 0;
    }
    to {
      max-height: 500px;
      opacity: 1;
    }
  }
  
  .troop-description {
    margin-top: 0;
    margin-bottom: 12px;
    font-style: italic;
    opacity: 0.9;
    font-size: 0.9rem;
  }
  
  .attributes-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 8px;
    margin-bottom: 12px;
  }
  
  .attribute {
    display: flex;
    align-items: center;
    gap: 5px;
    background-color: rgba(255, 255, 255, 0.1);
    padding: 6px 8px;
    border-radius: 4px;
  }
  
  .attribute-icon {
    font-size: 1.1rem;
  }
  
  .attribute-label {
    font-size: 0.8rem;
    opacity: 0.8;
  }
  
  .attribute-value {
    font-weight: bold;
    margin-left: auto;
  }
  
  .troop-action {
    display: flex;
    justify-content: flex-end;
  }
  
  .train-button {
    background-color: #4CAF50;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.2s;
  }
  
  .train-button:hover {
    background-color: #45a049;
  }
  
  .troop-image-container {
    width: 40px;
    height: 40px;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
    flex-shrink: 0;
  }
  
  .troop-image {
    width: 100%;
    height: 100%;
    object-fit: contain;
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

  /* Toast notification styles */
  .toast-container {
    position: fixed;
    top: 80px;
    right: 20px;
    z-index: 9999;
    max-width: 350px;
  }

  .toast-notification {
    padding: 12px 16px;
    margin-bottom: 12px;
    border-radius: 4px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    display: flex;
    align-items: center;
    font-weight: 500;
    color: white;
    opacity: 0.95;
    animation: toast-in 0.3s ease-out;
    transition: opacity 0.3s;
  }

  .toast-notification.success {
    background-color: #28a745;
    border-left: 5px solid #1e7e34;
  }

  .toast-notification.error {
    background-color: #dc3545;
    border-left: 5px solid #bd2130;
  }

  .toast-notification.warning {
    background-color: #ffc107;
    border-left: 5px solid #d39e00;
    color: #212529;
  }

  .toast-notification.info {
    background-color: #17a2b8;
    border-left: 5px solid #138496;
  }

  .toast-message {
    margin: 0;
    padding: 0;
    font-size: 14px;
  }

  @keyframes toast-in {
    from {
      transform: translateY(-20px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 0.95;
    }
  }

  .production-status-section {
    background-color: rgba(76, 175, 80, 0.1);
    border-left: 4px solid #4CAF50;
  }

  .production-item {
    display: flex;
    align-items: center;
    gap: 15px;
  }

  .production-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: rgba(0, 0, 0, 0.2);
    border-radius: 4px;
  }

  .production-emoji {
    font-size: 32px;
  }

  .production-image {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }

  .production-details {
    flex: 1;
  }

  .production-name {
    font-size: 18px;
    font-weight: bold;
    display: block;
    margin-bottom: 8px;
  }
</style>
