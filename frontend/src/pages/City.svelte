<script>
  import { onMount, onDestroy } from 'svelte';
  import { navigate } from '../router.js';
  import { user } from '../stores/auth.js';
  import { gameAPI } from '../services/gameAPI.js';
  import { gameState } from '../stores/gameState.js';
  import '../styles/pages/city.css'; 
  
  let city = null;
  let isLoading = true;
  let error = null;
  let gameData = null;
  let troopTypes = [];
  let loadingTroopTypes = false;
  let activeTab = 'summary';
  let selectedTroopType = null;
  
  // Add new state variables for building types
  let buildingTypes = [];
  let loadingBuildingTypes = false;
  let selectedBuildingType = null;

  // Add a helper function to render costs dynamically based on what's in the cost object
  function getResourceCostString(costObject) {
    if (!costObject) return 'Costo no disponible';
    
    const resourceDisplay = [];
    
    // Process each resource in the cost object
    if (costObject.food && costObject.food > 0) {
      resourceDisplay.push(`<span class="resource-cost-item"><img src="./ia_assets/janaria.png" alt="Food" class="resource-icon-small" style="width:12px;height:12px;vertical-align:middle;" /> ${costObject.food}</span>`);
    }
    
    if (costObject.gold && costObject.gold > 0) {
      resourceDisplay.push(`<span class="resource-cost-item"><img src="./ia_assets/lingotes_oro.png" alt="Gold" class="resource-icon-small" style="width:12px;height:12px;vertical-align:middle;" /> ${costObject.gold}</span>`);
    }
    
    if (costObject.wood && costObject.wood > 0) {
      resourceDisplay.push(`<span class="resource-cost-item"><img src="./ia_assets/zuhaitza.png" alt="Wood" class="resource-icon-small" style="width:12px;height:12px;vertical-align:middle;" /> ${costObject.wood}</span>`);
    }
    
    if (costObject.stone && costObject.stone > 0) {
      resourceDisplay.push(`<span class="resource-cost-item"><img src="./ia_assets/harria.png" alt="Stone" class="resource-icon-small" style="width:12px;height:12px;vertical-align:middle;" /> ${costObject.stone}</span>`);
    }
    
    if (costObject.iron && costObject.iron > 0) {
      resourceDisplay.push(`<span class="resource-cost-item"><img src="./ia_assets/lingote_hierro.png" alt="Iron" class="resource-icon-small" style="width:12px;height:12px;vertical-align:middle;" /> ${costObject.iron}</span>`);
    }
    
    return resourceDisplay.length > 0 ? resourceDisplay.join(' ') : 'Costo no disponible';
  }

  // Function to get detailed building information
  function getBuildingDetails(building) {
    // If building is just a string, find its details in buildingTypes
    if (typeof building === 'string') {
      const foundType = buildingTypes.find(type => 
        type.name.toLowerCase() === building.toLowerCase() || 
        type.type?.toLowerCase() === building.toLowerCase()
      );
      return foundType || { name: building };
    } 
    
    // If building already has details
    return building;
  }

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

  async function fetchBuildingTypes() {
    loadingBuildingTypes = true;
    try {
      const types = await gameAPI.getBuildingTypes();
      buildingTypes = types;
      console.log("Building types loaded:", buildingTypes);
    } catch (err) {
      console.error("Error loading building types:", err);
    } finally {
      loadingBuildingTypes = false;
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

  function toggleBuildingSelection(buildingType, index) {
    const buildingId = buildingType.id || `building-${index}`;
    
    if (selectedBuildingType && selectedBuildingType._uniqueId === buildingId) {
      selectedBuildingType = null;
    } else {
      selectedBuildingType = {
        ...buildingType,
        _uniqueId: buildingId
      };
      console.log("Selected building:", selectedBuildingType);
    }
  }

  async function startProduction(item, itemType) {
    try {
      if (!city) {
        showToastNotification("Error: No hay ciudad seleccionada", "error");
        return;
      }
      
      // Check if there's already production in progress
      if (city.production && city.production.current_item) {
        showToastNotification("Ya hay una producción en curso", "error");
        return;
      }
      
      // Get the number of turns required for this item
      const turnsToComplete = item.turns_to_build || item.turns || 3;
      
      // Get the proper type/id for production
      const itemId = item.id || item.type_id;
      
      if (!itemId) {
        showToastNotification(`Error: No se puede identificar el tipo de ${itemType === 'troop' ? 'tropa' : 'edificio'}`, "error");
        return;
      }
      
      console.log(`Setting ${itemType} for production:`, itemId);
      
      // Create the production object with the proper values including itemType
      city.production = {
        current_item: itemId,
        turns_remaining: turnsToComplete,
        itemType: itemType // Add new itemType attribute
      };
      
      console.log("Setting production:", city.production);
      
      // Update the game data with the new production
      if (gameData && gameData.player && gameData.player.cities) {
        const cityIndex = gameData.player.cities.findIndex(c => c.id === city.id);
        if (cityIndex !== -1) {
          gameData.player.cities[cityIndex].production = city.production;
          
          // Save changes to game session
          await gameAPI.updateGameSession(gameData);
          
          // Clear selected item to hide the expanded panel
          if (itemType === 'troop') {
            selectedTroopType = null;
          } else if (itemType === 'building') {
            selectedBuildingType = null;
          }
          
          // Show feedback messages
          showToastNotification(`¡Iniciada producción de ${item.name}!`, "success");
          
          // Switch to the summary tab to show the production info
          setActiveTab('summary');
        }
      }
    } catch (err) {
      console.error(`Error starting ${itemType} production:`, err);
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
      case 'archer': return { type: 'image', url: './ia_assets/archer.png' }; // Changed from emoji to image
      case 'cavalry': return { type: 'image', url: './ia_assets/cavalry.png' };
      case 'builder': return { type: 'emoji', value: '🔨' };
      default: return { type: 'emoji', value: '👤' };
    }
  }

  function getBuildingIcon(type) {
    switch (type && type.toLowerCase()) {
      case 'farm': return { type: 'emoji', value: '🌾' };
      case 'barracks': return { type: 'emoji', value: '⚔️' };
      case 'library': return { type: 'emoji', value: '📚' };
      case 'market': return { type: 'emoji', value: '🏪' };
      case 'wall': return { type: 'emoji', value: '🧱' };
      case 'tower': return { type: 'emoji', value: '🗼' };
      case 'temple': return { type: 'emoji', value: '⛪' };
      default: return { type: 'emoji', value: '🏛️' };
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
        // Improved error handling with more specific error
        showToastNotification("No se ha seleccionado ninguna ciudad. Volviendo al mapa...", "error");
        setTimeout(() => navigate('/map'), 1500);
        throw new Error("No se ha seleccionado ninguna ciudad.");
      }
      
      if (gameData.player && gameData.player.cities) {
        city = gameData.player.cities.find(c => c.id === selectedCityId);
      }
      
      if (!city) {
        // Improved error handling when city isn't found
        showToastNotification("La ciudad seleccionada no se encontró. Volviendo al mapa...", "error");
        setTimeout(() => navigate('/map'), 1500);
        throw new Error("No se encontró la ciudad seleccionada.");
      }
      
      // Only fetch these if we have a valid city
      await fetchTroopTypes();
      await fetchBuildingTypes();
      
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
              {@const isProducingTroop = !city.production.itemType || city.production.itemType === 'troop'}
              {@const productionType = isProducingTroop 
                ? troopTypes.find(t => t.id === city.production.current_item || t.type_id === city.production.current_item)
                : buildingTypes.find(b => b.id === city.production.current_item || b.type_id === city.production.current_item)}
              <div class="info-section production-status-section">
                <h4>Producción Actual</h4>
                <div class="production-item">
                  <div class="production-icon">
                    {#if isProducingTroop}
                      {#if productionType && getDefaultTroopIcon(productionType.name).type === 'image'}
                        <img src={getDefaultTroopIcon(productionType.name).url} alt={productionType ? productionType.name : city.production.current_item} class="production-image" />
                      {:else}
                        <span class="production-emoji">
                          {productionType ? getDefaultTroopIcon(productionType.name).value : '🛠️'}
                        </span>
                      {/if}
                    {:else}
                      <span class="production-emoji">
                        {productionType ? getBuildingIcon(productionType.type || productionType.name).value : '🏗️'}
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
                {@const isProducingTroop = !city.production.itemType || city.production.itemType === 'troop'}
                {@const productionType = isProducingTroop 
                  ? troopTypes.find(t => t.id === city.production.current_item || t.type_id === city.production.current_item)
                  : buildingTypes.find(b => b.id === city.production.current_item || b.type_id === city.production.current_item)}
                <div class="production-item">
                  <div class="production-icon">
                    {#if isProducingTroop}
                      {#if productionType && getDefaultTroopIcon(productionType.name).type === 'image'}
                        <img src={getDefaultTroopIcon(productionType.name).url} alt={productionType ? productionType.name : city.production.current_item} class="production-image" />
                      {:else}
                        <span class="production-emoji">
                          {productionType ? getDefaultTroopIcon(productionType.name).value : '🛠️'}
                        </span>
                      {/if}
                    {:else}
                      <span class="production-emoji">
                        {productionType ? getBuildingIcon(productionType.type || productionType.name).value : '🏗️'}
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
                              <span class="troop-cost">{@html getResourceCostString(troopType.cost)}</span>
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
                                <button class="train-button" on:click={() => startProduction(troopType, 'troop')}>
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
                  {#if loadingBuildingTypes}
                    <p>Cargando tipos de edificios...</p>
                  {:else if buildingTypes.length === 0}
                    <p>No hay tipos de edificios disponibles.</p>
                  {:else}
                    {#each buildingTypes as buildingType, index}
                      {@const uniqueKey = buildingType.id || `building-type-${index}`}
                      {@const iconData = getBuildingIcon(buildingType.type || buildingType.name)}
                      <div class="building-container">
                        <button 
                          class="production-button building-button" 
                          class:expanded={selectedBuildingType && (selectedBuildingType._uniqueId === (buildingType.id || `building-${index}`))}
                          on:click={() => toggleBuildingSelection(buildingType, index)}
                        >
                          <div class="building-info">
                            {#if iconData.type === 'image'}
                              <div class="building-image-container">
                                <img src={iconData.url} alt={buildingType.name} class="building-image" />
                              </div>
                            {:else}
                              <span class="building-icon">{iconData.value}</span>
                            {/if}
                            
                            <div class="building-details">
                              <span class="building-name">{buildingType.name}</span>
                              <span class="building-cost">{@html getResourceCostString(buildingType.cost)}</span>
                            </div>
                            <span class="production-turns">
                              <span class="turns-icon">🕒</span>
                              <span class="turns-count">{buildingType.turns_to_build || buildingType.turns || '?'}</span>
                              <span class="turns-label">turnos</span>
                            </span>
                          </div>
                        </button>
                        
                        {#if selectedBuildingType && (selectedBuildingType._uniqueId === (buildingType.id || `building-${index}`))}
                          <div class="building-details-expanded">
                            <div class="building-attributes">
                              {#if buildingType.description}
                                <p class="building-description">{buildingType.description}</p>
                              {/if}
                              
                              <div class="attributes-grid">
                                {#if buildingType.production_bonus !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">⚒️</span>
                                    <span class="attribute-label">Producción:</span>
                                    <span class="attribute-value">+{buildingType.production_bonus}%</span>
                                  </div>
                                {/if}
                                
                                {#if buildingType.research_bonus !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">📚</span>
                                    <span class="attribute-label">Investigación:</span>
                                    <span class="attribute-value">+{buildingType.research_bonus}%</span>
                                  </div>
                                {/if}
                                
                                {#if buildingType.defense_bonus !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">🛡️</span>
                                    <span class="attribute-label">Defensa:</span>
                                    <span class="attribute-value">+{buildingType.defense_bonus}%</span>
                                  </div>
                                {/if}
                              </div>
                              
                              <div class="building-action">
                                <button class="construct-button" on:click={() => startProduction(buildingType, 'building')}>
                                  Construir {buildingType.name}
                                </button>
                              </div>
                            </div>
                          </div>
                        {/if}
                      </div>
                    {/each}
                  {/if}
                </div>
              </div>
            </div>
          </div>
          
          <div class="tab-content" class:active={activeTab === 'buildings'}>
            <h3>Edificios</h3>
            <p>Gestiona los edificios de tu ciudad.</p>
            
            {#if city.buildings && city.buildings.length > 0}
              <div class="info-section buildings-grid">
                {#each city.buildings as buildingItem}
                  {@const building = getBuildingDetails(buildingItem)}
                  {@const iconData = getBuildingIcon(building.type || building.name)}
                  <div class="building-card">
                    <div class="building-icon-wrapper">
                      {#if iconData.type === 'image'}
                        <img src={iconData.url} alt={building.name} class="building-image" />
                      {:else}
                        <span class="building-icon">{iconData.value}</span>
                      {/if}
                    </div>
                    <h4>{building.name}</h4>
                    
                    {#if building.description}
                      <p class="building-description">{building.description}</p>
                    {:else}
                      <p class="building-description">Edificio de la ciudad.</p>
                    {/if}
                    
                    <div class="building-stats">
                      {#if building.production_bonus !== undefined}
                        <div class="building-stat">
                          <span class="stat-icon">⚒️</span>
                          <span class="stat-label">Producción:</span>
                          <span class="stat-value">+{building.production_bonus}%</span>
                        </div>
                      {/if}
                      
                      {#if building.research_bonus !== undefined}
                        <div class="building-stat">
                          <span class="stat-icon">📚</span>
                          <span class="stat-label">Investigación:</span>
                          <span class="stat-value">+{building.research_bonus}%</span>
                        </div>
                      {/if}
                      
                      {#if building.defense_bonus !== undefined}
                        <div class="building-stat">
                          <span class="stat-icon">🛡️</span>
                          <span class="stat-label">Defensa:</span>
                          <span class="stat-value">+{building.defense_bonus}%</span>
                        </div>
                      {/if}
                      
                      {#if building.food_bonus !== undefined}
                        <div class="building-stat">
                          <span class="stat-icon">🌾</span>
                          <span class="stat-label">Alimento:</span>
                          <span class="stat-value">+{building.food_bonus}%</span>
                        </div>
                      {/if}
                      
                      {#if building.gold_bonus !== undefined}
                        <div class="building-stat">
                          <span class="stat-icon">💰</span>
                          <span class="stat-label">Oro:</span>
                          <span class="stat-value">+{building.gold_bonus}%</span>
                        </div>
                      {/if}
                    </div>
                    
                    <div class="building-level">
                      <span class="level-label">Nivel:</span>
                      <span class="level-value">{building.level || 1}</span>
                    </div>
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
        <div class="resource-icon">
          <img src="./ia_assets/janaria.png" alt="Food" class="resource-bar-icon" />
        </div>
        <div class="resource-value">{gameData.player.resources.food || 0}</div>
      </div>
      <div class="resource gold">
        <div class="resource-icon">
          <img src="./ia_assets/lingotes_oro.png" alt="Gold" class="resource-bar-icon" />
        </div>
        <div class="resource-value">{gameData.player.resources.gold || 0}</div>
      </div>
      <div class="resource wood">
        <div class="resource-icon">
          <img src="./ia_assets/zuhaitza.png" alt="Wood" class="resource-bar-icon" />
        </div>
        <div class="resource-value">{gameData.player.resources.wood || 0}</div>
      </div>
      <div class="resource iron">
        <div class="resource-icon">
          <img src="./ia_assets/lingote_hierro.png" alt="Iron" class="resource-bar-icon" />
        </div>
        <div class="resource-value">{gameData.player.resources.iron || 0}</div>
      </div>
      <div class="resource stone">
        <div class="resource-icon">
          <img src="./ia_assets/harria.png" alt="Stone" class="resource-bar-icon" />
        </div>
        <div class="resource-value">{gameData.player.resources.stone || 0}</div>
      </div>
    </div>
  {/if}
</div>

