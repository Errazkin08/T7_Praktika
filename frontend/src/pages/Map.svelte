<script>
  import { onMount } from 'svelte';
  import { gameAPI } from '../services/gameAPI.js';

  // Define multiple scenarios with different difficulties
  const availableScenarios = [
    {
      _id: "europe_map_01",
      name: "Europe Map - Easy",
      description: "An easier scenario with more resources for the player",
      difficulty: "easy",
      map_size: { width: 100, height: 60 },
      initial_state: {
        player: {
          resources: {
            food: 50,
            production: 40,
            science: 20,
            gold: 300
          },
          cities: [
            { id: "city1", name: 'London', position: { x: 30, y: 20 }, population: 4, buildings: [], production: { current_item: "warrior", turns_remaining: 2 } },
            { id: "city2", name: 'Paris', position: { x: 34, y: 24 }, population: 3, buildings: [], production: { current_item: "settler", turns_remaining: 3 } },
            { id: "city5", name: 'Madrid', position: { x: 24, y: 36 }, population: 3, buildings: [], production: { current_item: "archer", turns_remaining: 2 } },
            { id: "city9", name: 'Stockholm', position: { x: 52, y: 10 }, population: 2, buildings: [], production: { current_item: "warrior", turns_remaining: 2 } },
            { id: "city11", name: 'Barcelona', position: { x: 32, y: 34 }, population: 2, buildings: [], production: { current_item: null, turns_remaining: 0 } }
          ],
          units: [
            { id: "unit1", type: 'warrior', position: { x: 32, y: 22 }, movement_points: 2, movement_points_left: 2, strength: 6, health: 100 },
            { id: "unit2", type: 'archer', position: { x: 36, y: 26 }, movement_points: 2, movement_points_left: 2, strength: 5, health: 100 },
            { id: "unit3", type: 'knight', position: { x: 26, y: 34 }, movement_points: 3, movement_points_left: 3, strength: 8, health: 100 },
            { id: "unit4", type: 'settler', position: { x: 40, y: 24 }, movement_points: 2, movement_points_left: 2, strength: 0, health: 100 }
          ],
          technologies: [
            { id: "agriculture", completed: true },
            { id: "pottery", completed: true },
            { id: "animal_husbandry", in_progress: true, turns_remaining: 2 }
          ]
        },
        ai: {
          resources: {
            food: 30,
            production: 15,
            science: 5,
            gold: 150
          },
          cities: [
            { id: "ai_city1", name: 'Berlin', position: { x: 50, y: 18 }, visible: false },
            { id: "ai_city2", name: 'Rome', position: { x: 50, y: 38 }, visible: false },
            { id: "ai_city3", name: 'Warsaw', position: { x: 60, y: 20 }, visible: false },
            { id: "ai_city4", name: 'Athens', position: { x: 60, y: 42 }, visible: false }
          ],
          units: [
            { id: "ai_unit1", type: 'warrior', position: { x: 48, y: 20 }, visible: false },
            { id: "ai_unit2", type: 'archer', position: { x: 58, y: 22 }, visible: false }
          ],
          technologies: []
        },
        map: {
          explored: [],
          visible_objects: [
            { type: "resource", resource_type: "iron", position: { x: 40, y: 30 }, improved: false },
            { type: "resource", resource_type: "food", position: { x: 38, y: 20 }, improved: false },
            { type: "resource", resource_type: "gold", position: { x: 56, y: 24 }, improved: false },
            { type: "resource", resource_type: "iron", position: { x: 54, y: 36 }, improved: false },
            { type: "resource", resource_type: "food", position: { x: 64, y: 22 }, improved: false },
            { type: "resource", resource_type: "gold", position: { x: 28, y: 30 }, improved: false },
            { type: "resource", resource_type: "iron", position: { x: 72, y: 16 }, improved: false },
            { type: "resource", resource_type: "food", position: { x: 44, y: 42 }, improved: false },
            { type: "resource", resource_type: "gold", position: { x: 36, y: 28 }, improved: false },
            { type: "resource", resource_type: "food", position: { x: 42, y: 26 }, improved: false },
            { type: "resource", resource_type: "iron", position: { x: 32, y: 32 }, improved: false }
          ]
        }
      }
    },
    {
      _id: "europe_map_02",
      name: "Europe Map - Hard",
      description: "A challenging scenario with stronger AI opponents",
      difficulty: "hard",
      map_size: { width: 100, height: 60 },
      initial_state: {
        player: {
          resources: {
            food: 20,
            production: 15,
            science: 5,
            gold: 100
          },
          cities: [
            { id: "city1", name: 'London', position: { x: 30, y: 20 }, population: 2, buildings: [], production: { current_item: "warrior", turns_remaining: 3 } },
            { id: "city2", name: 'Paris', position: { x: 34, y: 24 }, population: 2, buildings: [], production: { current_item: "settler", turns_remaining: 5 } }
          ],
          units: [
            { id: "unit1", type: 'warrior', position: { x: 32, y: 22 }, movement_points: 2, movement_points_left: 2, strength: 5, health: 100 },
            { id: "unit2", type: 'settler', position: { x: 36, y: 26 }, movement_points: 2, movement_points_left: 2, strength: 0, health: 100 }
          ],
          technologies: [
            { id: "agriculture", completed: true },
            { id: "animal_husbandry", in_progress: true, turns_remaining: 4 }
          ]
        },
        ai: {
          resources: {
            food: 50,
            production: 35,
            science: 15,
            gold: 250
          },
          cities: [
            { id: "ai_city1", name: 'Berlin', position: { x: 50, y: 18 }, visible: false },
            { id: "ai_city2", name: 'Rome', position: { x: 50, y: 38 }, visible: false },
            { id: "ai_city3", name: 'Warsaw', position: { x: 60, y: 20 }, visible: false },
            { id: "ai_city4", name: 'Athens', position: { x: 60, y: 42 }, visible: false },
            { id: "ai_city5", name: 'Moscow', position: { x: 80, y: 14 }, visible: false },
            { id: "ai_city6", name: 'Istanbul', position: { x: 70, y: 36 }, visible: false },
            { id: "ai_city7", name: 'Vienna', position: { x: 56, y: 26 }, visible: false }
          ],
          units: [
            { id: "ai_unit1", type: 'warrior', position: { x: 48, y: 20 }, visible: false },
            { id: "ai_unit2", type: 'archer', position: { x: 58, y: 22 }, visible: false },
            { id: "ai_unit3", type: 'knight', position: { x: 52, y: 36 }, visible: false },
            { id: "ai_unit4", type: 'warrior', position: { x: 62, y: 40 }, visible: false }
          ],
          technologies: []
        },
        map: {
          explored: [],
          visible_objects: [
            { type: "resource", resource_type: "iron", position: { x: 40, y: 30 }, improved: false },
            { type: "resource", resource_type: "food", position: { x: 38, y: 20 }, improved: false },
            { type: "resource", resource_type: "gold", position: { x: 56, y: 24 }, improved: false },
            { type: "resource", resource_type: "iron", position: { x: 54, y: 36 }, improved: false },
            { type: "resource", resource_type: "food", position: { x: 64, y: 22 }, improved: false },
            { type: "resource", resource_type: "gold", position: { x: 28, y: 30 }, improved: false },
            { type: "resource", resource_type: "iron", position: { x: 72, y: 16 }, improved: false },
            { type: "resource", resource_type: "food", position: { x: 44, y: 42 }, improved: false }
          ]
        }
      }
    }
  ];

  let scenarioData = availableScenarios[0];
  let gameData = {
    game_id: "game_" + Date.now(),
    name: "Current Europe Game",
    scenario_id: scenarioData._id,
    created_at: new Date().toISOString(),
    last_saved: new Date().toISOString(),
    turn: 1,
    current_player: "player",
    cheats_used: [],
    player: null,
    ai: null,
    map: null
  };

  let gameStarted = false;

  let mapSize = scenarioData.map_size;
  let tileSize = 20;
  let selectedTile = null;

  let cities = [];
  let resources = [];
  let units = [];

  let exploredMap = []; // Tracks which tiles have been explored (1) or not (0)

  const TERRAIN = {
    DEEP_WATER: 0,
    SHALLOW_WATER: 1,
    DESERT: 2,
    GRASS: 3,
    FOREST: 4,
    PLAINS: 5,
    HILLS: 6,
    MOUNTAINS: 7,
    SNOW: 8,
    JUNGLE: 9
  };

  let terrainMap = [];

  let offsetX = 0;
  let offsetY = 0;
  let isDragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let zoomLevel = 0.5;

  function zoomIn() {
    zoomLevel += 0.1;
    if (zoomLevel > 2) zoomLevel = 2;
  }

  function zoomOut() {
    zoomLevel -= 0.1;
    if (zoomLevel < 0.2) zoomLevel = 0.2;
  }

  function startDrag(event) {
    isDragging = true;
    dragStartX = event.clientX - offsetX;
    dragStartY = event.clientY - offsetY;
  }

  function drag(event) {
    if (!isDragging) return;

    offsetX = event.clientX - dragStartX;
    offsetY = event.clientY - dragStartY;
  }

  function endDrag() {
    isDragging = false;
  }

  function initializeTerrainMap() {
    terrainMap = Array(mapSize.height).fill().map(() => Array(mapSize.width).fill(TERRAIN.GRASS));
  }

  // Initialize exploration data with fog of war
  function initializeExploration() {
    // Create exploration map (0 = unexplored, 1 = explored)
    exploredMap = Array(mapSize.height).fill().map(() => Array(mapSize.width).fill(0));
    
    // Mark areas around player cities and units as explored
    const exploreRadius = 4; // How many tiles around objects are visible
    
    // Explore around player cities
    if (gameData.player?.cities) {
      gameData.player.cities.forEach(city => {
        exploreArea(city.position.x, city.position.y, exploreRadius);
      });
    }
    
    // Explore around player units
    if (gameData.player?.units) {
      gameData.player.units.forEach(unit => {
        exploreArea(unit.position.x, unit.position.y, exploreRadius);
      });
    }
    
    // Update visibility of AI elements based on exploration
    updateAIVisibility();
  }

  // Mark an area as explored and update the game state
  function exploreArea(centerX, centerY, radius) {
    if (!exploredMap || !centerX || !centerY) return;
    
    let areaWasExplored = false;
    
    for (let y = Math.max(0, centerY - radius); y <= Math.min(mapSize.height - 1, centerY + radius); y++) {
      for (let x = Math.max(0, centerX - radius); x <= Math.min(mapSize.width - 1, centerX + radius); x++) {
        const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));
        if (distance <= radius && exploredMap[y][x] !== 1) {
          exploredMap[y][x] = 1;
          areaWasExplored = true;
        }
      }
    }
    
    // If something new was explored, update visibility and save game state
    if (areaWasExplored) {
      updateAIVisibility();
      saveExplorationState();
    }
  }

  // This is used to check if a specific tile is explored
  function isTileExplored(x, y) {
    return exploredMap && exploredMap[y] && exploredMap[y][x] === 1;
  }
  
  // Update which AI elements should be visible based on explored areas
  function updateAIVisibility() {
    if (!gameData?.ai) return;
    
    // Update AI cities visibility
    if (gameData.ai.cities) {
      gameData.ai.cities.forEach(city => {
        const x = city.position.x;
        const y = city.position.y;
        city.visible = isTileExplored(x, y);
      });
    }
    
    // Update AI units visibility
    if (gameData.ai.units) {
      gameData.ai.units.forEach(unit => {
        const x = unit.position.x;
        const y = unit.position.y;
        unit.visible = isTileExplored(x, y);
      });
    }
  }
  
  // Save the current exploration state to the game data and backend
  async function saveExplorationState() {
    try {
      // Update the game data with current exploration state
      gameData.map.explored = [...exploredMap]; // Create a copy of the exploration data
      
      // Save to backend
      await gameAPI.updateGame(gameData.game_id, gameData);
      console.log("Exploration state saved");
    } catch (error) {
      console.error("Error saving exploration state:", error);
    }
  }
  
  // This function handles moving units and updating exploration
  function moveUnit(unitId, newX, newY) {
    // Find the unit
    const unit = gameData.player.units.find(u => u.id === unitId);
    if (!unit) return;
    
    // Store old position for updating the UI
    const oldX = unit.position.x;
    const oldY = unit.position.y;
    
    // Update unit position
    unit.position.x = newX;
    unit.position.y = newY;
    unit.movement_points_left -= 1; // Reduce movement points
    
    // Explore the area around the new position
    exploreArea(newX, newY, 3); // Units can see 3 tiles around them
    
    // Update the rendering arrays
    updateRenderingArrays();
  }

  function handleTileClick(x, y) {
    const terrain = terrainMap[y] ? terrainMap[y][x] : TERRAIN.GRASS;
    const city = cities.find(c => c.x === x && c.y === y);
    const resource = resources.find(r => r.x === x && r.y === y);
    const unit = units.find(u => u.x === x && u.y === y);
    const isExplored = exploredMap[y] && exploredMap[y][x] === 1;

    selectedTile = { 
      x, y, 
      terrain, 
      city, 
      resource, 
      unit,
      explored: isExplored
    };
  }

  function centerMapOnPlayer() {
    if (gameData.player?.cities?.length > 0) {
      const firstCity = gameData.player.cities[0];
      const containerWidth = document.querySelector('.map-container')?.clientWidth || 800;
      const containerHeight = document.querySelector('.map-container')?.clientHeight || 600;

      offsetX = containerWidth/2 - firstCity.position.x * tileSize * zoomLevel;
      offsetY = containerHeight/2 - firstCity.position.y * tileSize * zoomLevel;
    }
  }

  function startNewGame() {
    console.log("Starting new game with scenario:", scenarioData.name);

    try {
      gameStarted = true;

      gameData = {
        game_id: "game_" + Date.now(),
        name: "Current Europe Game",
        scenario_id: scenarioData._id,
        created_at: new Date().toISOString(),
        last_saved: new Date().toISOString(),
        turn: 1,
        current_player: "player",
        cheats_used: [],
        player: null,
        ai: null,
        map: null
      };

      mapSize = scenarioData.map_size;

      initializeTerrainMap();
      console.log("Terrain map initialized");

      gameData.player = JSON.parse(JSON.stringify(scenarioData.initial_state.player));
      gameData.ai = JSON.parse(JSON.stringify(scenarioData.initial_state.ai));
      gameData.map = JSON.parse(JSON.stringify(scenarioData.initial_state.map));
      console.log("Game data populated from scenario");

      initializeExploration();
      gameData.map.explored = JSON.parse(JSON.stringify(exploredMap));

      console.log("Exploration initialized");

      updateRenderingArrays();
      console.log("Rendering arrays updated");

      setTimeout(centerMapOnPlayer, 200);

    } catch (error) {
      console.error("Error starting new game:", error);
      alert("Error starting game: " + error.message);
    }
  }

  function updateRenderingArrays() {
    cities = [
      ...gameData.player.cities.map(city => ({
        id: city.id,
        name: city.name,
        x: city.position.x,
        y: city.position.y,
        size: city.population,
        owner: 'player',
        strength: 10,
        health: 100
      })),
      ...gameData.ai.cities
        .filter(city => city.visible)
        .map(city => ({
          id: city.id,
          name: city.name,
          x: city.position.x,
          y: city.position.y,
          size: city.population || 2,
          owner: 'ai',
          strength: 10,
          health: 100
        }))
    ];

    units = [
      ...gameData.player.units.map(unit => ({
        id: unit.id,
        type: unit.type,
        x: unit.position.x,
        y: unit.position.y,
        owner: 'player',
        strength: unit.strength || 0,
        movement: unit.movement_points || 2,
        movementLeft: unit.movement_points_left || 0,
        health: unit.health || 100
      })),
      ...gameData.ai.units
        .filter(unit => unit.visible)
        .map(unit => ({
          id: unit.id,
          type: unit.type === 'unknown' ? 'unknown' : unit.type,
          x: unit.position.x,
          y: unit.position.y,
          owner: 'ai',
          strength: unit.strength || 3,
          movement: 2,
          health: unit.health || 100
        }))
    ];

    resources = gameData.map.visible_objects
      .filter(obj => obj.type === 'resource')
      .map(resource => ({
        id: resource.position.x + '_' + resource.position.y,
        type: resource.resource_type,
        x: resource.position.x,
        y: resource.position.y,
        improved: resource.improved || false
      }));
  }

  function getTerrainColor(terrainType) {
    switch(terrainType) {
      case TERRAIN.DEEP_WATER:
        return '#0066cc';
      case TERRAIN.SHALLOW_WATER:
        return '#3399ff';
      case TERRAIN.DESERT:
        return '#e6cc99';
      case TERRAIN.GRASS:
        return '#66cc66';
      case TERRAIN.FOREST:
        return '#006633';
      case TERRAIN.PLAINS:
        return '#cccc99';
      case TERRAIN.HILLS:
        return '#996633';
      case TERRAIN.MOUNTAINS:
        return '#666666';
      case TERRAIN.SNOW:
        return '#ffffff';
      case TERRAIN.JUNGLE:
        return '#339933';
      default:
        return '#66cc66';
    }
  }

  function getTerrainName(terrainType) {
    switch(terrainType) {
      case TERRAIN.DEEP_WATER: return 'Deep Water';
      case TERRAIN.SHALLOW_WATER: return 'Shallow Water';
      case TERRAIN.DESERT: return 'Desert';
      case TERRAIN.GRASS: return 'Grassland';
      case TERRAIN.FOREST: return 'Forest';
      case TERRAIN.PLAINS: return 'Plains';
      case TERRAIN.HILLS: return 'Hills';
      case TERRAIN.MOUNTAINS: return 'Mountains';
      case TERRAIN.SNOW: return 'Snow';
      case TERRAIN.JUNGLE: return 'Jungle';
      default: return 'Unknown';
    }
  }
</script>

{#if !gameStarted}
  <div class="scenario-selection-screen">
    <h2>Select Scenario</h2>
    <div class="scenario-options">
      {#each availableScenarios as scenario}
        <div 
          class="scenario-card" 
          class:selected={scenarioData._id === scenario._id}
          on:click={() => scenarioData = scenario}
        >
          <h3>{scenario.name}</h3>
          <p>{scenario.description}</p>
          <div class="difficulty-badge {scenario.difficulty}">
            {scenario.difficulty.toUpperCase()}
          </div>
        </div>
      {/each}
    </div>
    <button class="start-button" on:click|preventDefault={startNewGame}>Start Game</button>
  </div>
{:else}
  <div class="map-page">
    <div class="map-controls">
      <button on:click={zoomIn}>Zoom In (+)</button>
      <button on:click={zoomOut}>Zoom Out (-)</button>
      <button on:click={centerMapOnPlayer}>Center Map</button>
      <span class="game-info">Turn: {gameData.turn} | Player: {gameData.current_player} | Difficulty: {scenarioData.difficulty}</span>
    </div>
    
    <div 
      class="map-container"
      on:mousedown={startDrag}
      on:mousemove={drag}
      on:mouseup={endDrag}
      on:mouseleave={endDrag}
    >
      <div 
        class="map-grid"
        style="transform: translate({offsetX}px, {offsetY}px) scale({zoomLevel});"
      >
        {#each Array(mapSize.height) as _, y}
          {#each Array(mapSize.width) as _, x}
            {@const terrain = terrainMap[y] ? terrainMap[y][x] : TERRAIN.GRASS}
            {@const isExplored = isTileExplored(x, y)}
            
            <div 
              class="map-tile"
              style="
                left: {x * tileSize}px;
                top: {y * tileSize}px;
                width: {tileSize}px;
                height: {tileSize}px;
                background-color: {getTerrainColor(terrain)};
              "
              on:click={() => handleTileClick(x, y)}
              class:selected={selectedTile && selectedTile.x === x && selectedTile.y === y}
            >
              <!-- Only show contents for explored tiles -->
              {#if isExplored}
                {#if x % 10 === 0 && y % 10 === 0}
                  <div class="coord-marker">{x},{y}</div>
                {/if}
                
                {#each cities.filter(city => city.x === x && city.y === y) as city}
                  <div class="city-marker" class:enemy={city.owner === 'ai'} class:player={city.owner === 'player'}>
                    <div class="city-icon">
                      <div class="city-buildings">
                        <div class="city-building building1"></div>
                        <div class="city-building building2"></div>
                        <div class="city-building building3"></div>
                      </div>
                    </div>
                    <div class="city-name-label">{city.name}</div>
                  </div>
                {/each}
                
                {#each resources.filter(resource => resource.x === x && resource.y === y) as resource}
                  <div class="resource-marker" class:improved={resource.improved}>
                    {resource.type === 'iron' ? '⚒️' : resource.type === 'food' ? '🌾' : '💰'}
                  </div>
                {/each}
                
                {#each units.filter(unit => unit.x === x && unit.y === y) as unit}
                  <div class="unit-marker" class:enemy={unit.owner === 'ai'} class:player={unit.owner === 'player'}>
                    {unit.type === 'warrior' ? '⚔️' : 
                      unit.type === 'archer' ? '🏹' : 
                      unit.type === 'knight' ? '🐎' : 
                      unit.type === 'unknown' ? '❓' : '👨‍🌾'}
                  </div>
                {/each}
              {/if}
            </div>
          {/each}
        {/each}
      </div>
      
      <!-- Fog of war mask overlay -->
      <div 
        class="fog-of-war"
        style="transform: translate({offsetX}px, {offsetY}px) scale({zoomLevel});"
      >
        {#each Array(mapSize.height) as _, y}
          {#each Array(mapSize.width) as _, x}
            {@const isExplored = isTileExplored(x, y)}
            {#if !isExplored}
              <div 
                class="fog-tile"
                style="
                  left: {x * tileSize}px;
                  top: {y * tileSize}px;
                  width: {tileSize}px;
                  height: {tileSize}px;
                "
              ></div>
            {/if}
          {/each}
        {/each}
      </div>
    </div>
    
    <div class="info-panel">
      <h3>{scenarioData.name}</h3>
      <p>{scenarioData.description}</p>
      <p>Difficulty: {scenarioData.difficulty}</p>
      
      <div class="resources-display">
        <div class="resource-item">
          <span class="resource-icon">🌾</span>
          <span class="resource-amount">{gameData.player?.resources?.food || 0}</span>
        </div>
        <div class="resource-item">
          <span class="resource-icon">🔨</span>
          <span class="resource-amount">{gameData.player?.resources?.production || 0}</span>
        </div>
        <div class="resource-item">
          <span class="resource-icon">📚</span>
          <span class="resource-amount">{gameData.player?.resources?.science || 0}</span>
        </div>
        <div class="resource-item">
          <span class="resource-icon">💰</span>
          <span class="resource-amount">{gameData.player?.resources?.gold || 0}</span>
        </div>
      </div>
      
      {#if selectedTile}
        <div class="selected-info">
          <h4>Selected Tile: ({selectedTile.x}, {selectedTile.y})</h4>
          
          {#if selectedTile.explored}
            <div class="terrain-info">
              <h5>Terrain: {getTerrainName(selectedTile.terrain)}</h5>
              <div class="terrain-sample" style="background-color: {getTerrainColor(selectedTile.terrain)};"></div>
            </div>
            
            {#if selectedTile.city}
              <div class="city-info">
                <h5>City: {selectedTile.city.name}</h5>
                <p>Size: {selectedTile.city.size}</p>
                <p>Owner: {selectedTile.city.owner === 'player' ? 'You' : 'AI'}</p>
              </div>
            {/if}
            
            {#if selectedTile.resource}
              <div class="resource-info">
                <h5>Resource: {selectedTile.resource.type}</h5>
                <p>Status: {selectedTile.resource.improved ? 'Improved' : 'Not improved'}</p>
              </div>
            {/if}
            
            {#if selectedTile.unit}
              <div class="unit-info">
                <h5>Unit: {selectedTile.unit.type}</h5>
                <p>Owner: {selectedTile.unit.owner === 'player' ? 'You' : 'AI'}</p>
              </div>
            {/if}
            
            {#if !selectedTile.city && !selectedTile.resource && !selectedTile.unit}
              <p>Empty tile</p>
            {/if}
          {:else}
            <p>This area is unexplored. Send units to reveal what's there.</p>
          {/if}
        </div>
      {:else}
        <p>No tile selected. Click on a tile to see information.</p>
      {/if}
    </div>
  </div>
{/if}

<style>
  .map-page {
    display: grid;
    grid-template-columns: 3fr 1fr;
    grid-template-rows: auto 1fr;
    gap: 1rem;
    height: calc(100vh - 15rem);
  }
  
  .map-controls {
    grid-column: 1 / 3;
    display: flex;
    gap: 0.5rem;
    padding: 0.5rem;
    background-color: #f0f0f0;
    border-radius: 4px;
    align-items: center;
  }
  
  .map-controls button {
    padding: 0.5rem 1rem;
    background-color: #4c66af;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .map-controls button.active {
    background-color: #d9534f;
    font-weight: bold;
  }
  
  .game-info {
    margin-left: auto;
    margin-right: 20px;
    background-color: #eee;
    padding: 5px 10px;
    border-radius: 4px;
    font-weight: bold;
  }
  
  .map-container {
    grid-column: 1;
    border: 1px solid #ccc;
    border-radius: 4px;
    overflow: hidden;
    position: relative;
    cursor: grab;
    background-color: #0066cc;
  }
  
  .map-grid {
    position: relative;
    transform-origin: 0 0;
  }
  
  .map-tile {
    position: absolute;
    border: 1px solid rgba(0, 0, 0, 0.2);
    box-sizing: border-box;
    transition: all 0.1s;
  }
  
  .map-tile.unexplored {
    background-color: #000 !important;
    opacity: 0.9;
  }
  
  .coord-marker {
    position: absolute;
    bottom: 2px;
    right: 2px;
    font-size: 0.6rem;
    color: rgba(0, 0, 0, 0.7);
    background-color: rgba(255, 255, 255, 0.7);
    padding: 1px 3px;
    border-radius: 2px;
    z-index: 10;
  }
  
  .scenario-selector {
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 100;
    background: rgba(255,255,255,0.9);
    padding: 8px;
    border-radius: 5px;
    display: flex;
    gap: 8px;
  }
  
  .scenario-selector select {
    padding: 4px;
    border-radius: 4px;
  }
  
  .info-panel {
    grid-column: 2;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 1rem;
    background-color: #f9f9f9;
    overflow-y: auto;
  }
  
  .resources-display {
    display: flex;
    justify-content: space-between;
    margin: 1rem 0;
    background-color: #fff;
    padding: 0.5rem;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  }
  
  .resource-item {
    display: flex;
    align-items: center;
    gap: 0.3rem;
  }
  
  .resource-icon {
    font-size: 1.2rem;
  }
  
  .resource-amount {
    font-weight: bold;
  }
  
  .city-marker {
    position: absolute;
    z-index: 5;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 80%;
    height: 80%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }
  
  .city-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background-color: rgba(255, 255, 255, 0.9);
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    border: 2px solid;
  }
  
  .city-marker.player .city-icon {
    border-color: #4CAF50;
  }
  
  .city-marker.enemy .city-icon {
    border-color: #f44336;
  }
  
  .city-name-label {
    margin-top: 2px;
    font-size: 0.7rem;
    font-weight: bold;
    color: white;
    text-shadow: 0 0 3px black, 0 0 3px black, 0 0 3px black, 0 0 3px black;
    pointer-events: none;
  }

  .scenario-selection-screen {
    width: 100%;
    height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background: linear-gradient(to bottom, #2c3e50, #4c669f);
    color: white;
    padding: 2rem;
  }
  
  .scenario-options {
    display: flex;
    gap: 2rem;
    margin: 2rem 0;
    width: 100%;
    max-width: 1200px;
    justify-content: center;
  }
  
  .scenario-card {
    background-color: #f9f9f9;
    border-radius: 8px;
    padding: 1.5rem;
    width: 300px;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    color: #333;
    border: 3px solid transparent;
  }
  
  .scenario-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
  }
  
  .scenario-card.selected {
    border-color: #4CAF50;
    background-color: #f0f7f0;
  }
  
  .difficulty-badge {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    padding: 0.3rem 0.6rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: bold;
  }
  
  .difficulty-badge.easy {
    background-color: #4CAF50;
    color: white;
  }
  
  .difficulty-badge.hard {
    background-color: #f44336;
    color: white;
  }
  
  .start-button {
    padding: 0.8rem 2rem;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1.2rem;
    cursor: pointer;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    transition: all 0.2s ease;
  }
  
  .start-button:hover {
    background-color: #45a049;
    transform: translateY(-2px);
  }
  
  .map-controls button.toggled {
    background-color: #C9302C;
    box-shadow: inset 0 0 5px rgba(0, 0, 0, 0.3);
  }

  .fog-of-war {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 50;
    transform-origin: 0 0;
  }
  
  .fog-tile {
    position: absolute;
    background-color: black;
    opacity: 0.85;
    box-shadow: 0 0 5px rgba(0,0,0,0.5);
  }
</style>
