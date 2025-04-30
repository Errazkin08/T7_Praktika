<script>
  import { onMount } from 'svelte';
  import { navigate } from '../router.js';
  import { gameAPI } from '../services/gameAPI.js';
  import { gameState, pauseGame, endGame } from '../stores/gameState.js';
  import { user } from '../stores/auth.js';

  let showPauseMenu = false;
  let gameStarted = false;
  let isLoading = true;
  let loadingError = null;
  
  // Game data structures
  let gameData = null;
  let mapSize = { width: 30, height: 30 }; // Changed to 30x30
  let tileSize = 24; // Larger tiles for better visibility with smaller map
  let selectedTile = null;
  let cities = [];
  let resources = [];
  let units = [];
  let exploredMap = []; 
  let terrainMap = [];
  let offsetX = 0;
  let offsetY = 0;
  let isDragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let zoomLevel = 0.8; // Adjusted zoom level for better visibility
  
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

  // Make sure we have a valid game in progress
  onMount(() => {
    try {
      // If no user is logged in, redirect to login
      if (!$user) {
        navigate('/');
        return;
      }
      
      // Set up keyboard shortcuts
      window.addEventListener('keydown', handleKeyPress);
      
      // Initialize the game
      initializeGame();
      
      return () => {
        // Clean up event listeners
        window.removeEventListener('keydown', handleKeyPress);
      };
    } catch (err) {
      console.error("Error mounting Map component:", err);
      loadingError = err.message;
    }
  });

  function handleKeyPress(event) {
    // ESC key toggles pause menu
    if (event.key === 'Escape') {
      togglePauseMenu();
    }
  }
  
  function togglePauseMenu() {
    showPauseMenu = !showPauseMenu;
    pauseGame(showPauseMenu);
  }
  
  // Function to properly initialize the game with improved error handling
  async function initializeGame() {
    try {
      isLoading = true;
      loadingError = null;
      
      // Create basic game data
      createBasicGameData();

      // Fetch map data from API
      try {
        console.log("Fetching map data from API...");
        const mapData = await gameAPI.getFirstMap();
        
        if (mapData) {
          console.log("Map data loaded successfully from API");
          
          // Update map size
          mapSize = {
            width: mapData.width || 30,
            height: mapData.height || 30
          };
          
          // Create terrain map from grid
          if (mapData.grid && Array.isArray(mapData.grid)) {
            console.log(`Map grid received: ${mapData.grid.length}x${mapData.grid[0]?.length}`);
            
            // Convert grid data to terrain map
            terrainMap = convertGridToTerrain(mapData.grid);
            
            // Set player starting position based on startPoint if available
            if (mapData.startPoint && Array.isArray(mapData.startPoint) && mapData.startPoint.length === 2) {
              const [startX, startY] = mapData.startPoint;
              
              // Update city and unit positions
              if (gameData.player?.cities?.length > 0) {
                gameData.player.cities[0].position.x = startX;
                gameData.player.cities[0].position.y = startY;
                
                // Position second city near first if it exists
                if (gameData.player.cities.length > 1) {
                  gameData.player.cities[1].position.x = Math.min(startX + 3, mapSize.width - 1);
                  gameData.player.cities[1].position.y = Math.min(startY + 3, mapSize.height - 1);
                }
              }
              
              // Update unit positions
              if (gameData.player?.units?.length > 0) {
                gameData.player.units[0].position.x = startX + 1;
                gameData.player.units[0].position.y = startY;
                
                if (gameData.player.units.length > 1) {
                  gameData.player.units[1].position.x = startX;
                  gameData.player.units[1].position.y = startY + 1;
                }
              }
            }
          } else {
            console.warn("Map grid data missing or invalid, using generated terrain");
            initializeTerrainMap();
          }
        } else {
          console.warn("No map data returned from API, using local generation");
          initializeTerrainMap();
        }
      } catch (apiError) {
        console.error("Error fetching map data:", apiError);
        console.log("Falling back to local map generation");
        initializeTerrainMap();
      }
      
      // Initialize exploration data after terrain is set up
      initializeExploration();
      
      // Update game map with exploration data
      gameData.map.explored = JSON.parse(JSON.stringify(exploredMap));
      
      // Update rendering arrays
      updateRenderingArrays();
      console.log("Rendering arrays updated");
      
      // Mark game as started
      gameStarted = true;
      isLoading = false;
      
      // Center the map on player after a short delay
      setTimeout(centerMapOnPlayer, 200);
      
    } catch (error) {
      console.error("Error starting new game:", error);
      loadingError = error.message || "Unknown error occurred while starting the game.";
      isLoading = false;
    }
  }

  // Helper function to create basic game data
  function createBasicGameData() {
    // Get difficulty from gameState if available
    const difficulty = $gameState.currentScenario?.difficulty || "easy";
    
    gameData = {
      game_id: "game_" + Date.now(),
      name: $gameState.gameName || "My Game",
      scenario_id: $gameState.currentScenario?._id || "default_scenario",
      created_at: new Date().toISOString(),
      last_saved: new Date().toISOString(),
      turn: 1,
      current_player: "player",
      difficulty: difficulty, // Store difficulty in game data
      cheats_used: [],
      player: {
        resources: {
          food: 50,
          production: 40,
          science: 20,
          gold: 300
        },
        cities: [
          { id: "city1", name: 'London', position: { x: 12, y: 8 }, population: 4, buildings: [], production: { current_item: "warrior", turns_remaining: 2 } },
          { id: "city2", name: 'Paris', position: { x: 15, y: 12 }, population: 3, buildings: [], production: { current_item: "settler", turns_remaining: 3 } }
        ],
        units: [
          { id: "unit1", type: 'warrior', position: { x: 13, y: 9 }, movement_points: 2, movement_points_left: 2, strength: 6, health: 100 },
          { id: "unit2", type: 'archer', position: { x: 16, y: 13 }, movement_points: 2, movement_points_left: 2, strength: 5, health: 100 }
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
          { id: "ai_city1", name: 'Berlin', position: { x: 20, y: 8 }, visible: false },
          { id: "ai_city2", name: 'Rome', position: { x: 20, y: 18 }, visible: false }
        ],
        units: [
          { id: "ai_unit1", type: 'warrior', position: { x: 19, y: 9 }, visible: false }
        ],
        technologies: []
      },
      map: {
        explored: [],
        visible_objects: [
          { type: "resource", resource_type: "iron", position: { x: 17, y: 15 }, improved: false },
          { type: "resource", resource_type: "food", position: { x: 14, y: 10 }, improved: false },
          { type: "resource", resource_type: "gold", position: { x: 11, y: 16 }, improved: false }
        ]
      }
    };
  }
  
  // Convert API grid to terrain map
  function convertGridToTerrain(grid) {
    // Create terrain map from grid data
    const height = grid.length;
    const width = grid[0]?.length || 30;
    let newTerrainMap = Array(height).fill().map(() => Array(width).fill(TERRAIN.GRASS));
    
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        // Convert grid value to terrain type
        // Assuming grid has values that can be mapped to terrain types:
        // 0 = water, 1 = plains, 2 = forest, 3 = mountains, etc.
        switch (grid[y][x]) {
          case 0:
            newTerrainMap[y][x] = TERRAIN.DEEP_WATER;
            break;
          case 1:
            newTerrainMap[y][x] = TERRAIN.PLAINS;
            break;
          case 2:
            newTerrainMap[y][x] = TERRAIN.FOREST;
            break;
          case 3:
            newTerrainMap[y][x] = TERRAIN.MOUNTAINS;
            break;
          case 4:
            newTerrainMap[y][x] = TERRAIN.HILLS;
            break;
          case 5:
            newTerrainMap[y][x] = TERRAIN.DESERT;
            break;
          case 6:
            newTerrainMap[y][x] = TERRAIN.SHALLOW_WATER;
            break;
          case 7:
            newTerrainMap[y][x] = TERRAIN.GRASS;
            break;
          case 8:
            newTerrainMap[y][x] = TERRAIN.SNOW;
            break;
          case 9:
            newTerrainMap[y][x] = TERRAIN.JUNGLE;
            break;
          default:
            newTerrainMap[y][x] = TERRAIN.GRASS;
        }
      }
    }
    
    return newTerrainMap;
  }

  function initializeTerrainMap() {
    // First fill everything with deep water
    terrainMap = Array(mapSize.height).fill().map(() => Array(mapSize.width).fill(TERRAIN.DEEP_WATER));
    
    // Create a realistic continent shape using noise/probability
    const centerX = Math.floor(mapSize.width / 2);
    const centerY = Math.floor(mapSize.height / 2);
    const maxRadius = Math.min(mapSize.width, mapSize.height) * 0.4; // Size of the continent
    
    // Create landmass using distance from center + noise
    for (let y = 0; y < mapSize.height; y++) {
      for (let x = 0; x < mapSize.width; x++) {
        // Calculate distance from center
        const dx = x - centerX;
        const dy = y - centerY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        // Add some noise to the distance
        const noise = (Math.random() - 0.5) * maxRadius * 0.5;
        const adjustedDistance = distance + noise;
        
        // Determine terrain based on distance from center
        if (adjustedDistance < maxRadius * 0.6) {
          // Main continent
          terrainMap[y][x] = TERRAIN.PLAINS;
          
          // Add terrain variety
          const terrainVariety = Math.random();
          if (terrainVariety < 0.3) terrainMap[y][x] = TERRAIN.GRASS;
          else if (terrainVariety < 0.4) terrainMap[y][x] = TERRAIN.HILLS;
          else if (terrainVariety < 0.45) terrainMap[y][x] = TERRAIN.FOREST;
          else if (terrainVariety < 0.48) terrainMap[y][x] = TERRAIN.MOUNTAINS;
        } else if (adjustedDistance < maxRadius * 0.8) {
          // Coast and islands
          const coastal = Math.random();
          if (coastal < 0.7) {
            terrainMap[y][x] = TERRAIN.SHALLOW_WATER;
          } else {
            // Small islands
            terrainMap[y][x] = Math.random() < 0.6 ? TERRAIN.GRASS : TERRAIN.PLAINS;
          }
        }
      }
    }
    
    // Create a river
    let riverX = centerX + Math.floor(Math.random() * 5) - 2;
    let riverY = 0;
    
    while (riverY < mapSize.height) {
      // Make the river meander
      riverX += Math.floor(Math.random() * 3) - 1;
      
      // Keep river in bounds
      if (riverX < 0) riverX = 0;
      if (riverX >= mapSize.width) riverX = mapSize.width - 1;
      
      // Add river tile
      terrainMap[riverY][riverX] = TERRAIN.SHALLOW_WATER;
      
      // Sometimes make the river wider
      if (Math.random() < 0.3 && riverX > 0) {
        terrainMap[riverY][riverX - 1] = TERRAIN.SHALLOW_WATER;
      }
      if (Math.random() < 0.3 && riverX < mapSize.width - 1) {
        terrainMap[riverY][riverX + 1] = TERRAIN.SHALLOW_WATER;
      }
      
      riverY++;
    }
    
    // Add desert area in one corner
    const desertX = Math.random() < 0.5 ? 0 : mapSize.width - 6;
    const desertY = Math.random() < 0.5 ? 0 : mapSize.height - 6;
    
    for (let y = desertY; y < desertY + 6 && y < mapSize.height; y++) {
      for (let x = desertX; x < desertX + 6 && x < mapSize.width; x++) {
        if (terrainMap[y][x] !== TERRAIN.DEEP_WATER && terrainMap[y][x] !== TERRAIN.SHALLOW_WATER) {
          if (Math.random() < 0.8) {
            terrainMap[y][x] = TERRAIN.DESERT;
          }
        }
      }
    }
    
    // Make sure cities and units are on valid terrain
    if (gameData && gameData.player) {
      gameData.player.cities.forEach(city => {
        const x = city.position.x;
        const y = city.position.y;
        
        if (y >= 0 && y < mapSize.height && x >= 0 && x < mapSize.width) {
          const terrainType = terrainMap[y][x];
          if (terrainType === TERRAIN.DEEP_WATER || terrainType === TERRAIN.SHALLOW_WATER) {
            terrainMap[y][x] = TERRAIN.PLAINS;
          }
        }
      });
      
      gameData.player.units.forEach(unit => {
        const x = unit.position.x;
        const y = unit.position.y;
        
        if (y >= 0 && y < mapSize.height && x >= 0 && x < mapSize.width) {
          const terrainType = terrainMap[y][x];
          if (terrainType === TERRAIN.DEEP_WATER || terrainType === TERRAIN.SHALLOW_WATER) {
            terrainMap[y][x] = TERRAIN.PLAINS;
          }
        }
      });
    }
    
    if (gameData && gameData.ai) {
      gameData.ai.cities.forEach(city => {
        const x = city.position.x;
        const y = city.position.y;
        
        if (y >= 0 && y < mapSize.height && x >= 0 && x < mapSize.width) {
          const terrainType = terrainMap[y][x];
          if (terrainType === TERRAIN.DEEP_WATER || terrainType === TERRAIN.SHALLOW_WATER) {
            terrainMap[y][x] = TERRAIN.PLAINS;
          }
        }
      });
    }
  }
  
  // Initialize exploration data with fog of war
  function initializeExploration() {
    // Create exploration map (0 = unexplored, 1 = explored)
    exploredMap = Array(mapSize.height).fill().map(() => Array(mapSize.width).fill(0));
    
    // Mark areas around player cities and units as explored
    const exploreRadius = 4;
    
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

  // Mark an area as explored
  function exploreArea(centerX, centerY, radius) {
    if (!exploredMap || !centerX || !centerY) return;
    
    for (let y = Math.max(0, centerY - radius); y <= Math.min(mapSize.height - 1, centerY + radius); y++) {
      for (let x = Math.max(0, centerX - radius); x <= Math.min(mapSize.width - 1, centerX + radius); x++) {
        const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));
        if (distance <= radius) {
          exploredMap[y][x] = 1;
        }
      }
    }
    
    updateAIVisibility();
  }

  // Check if a tile is explored
  function isTileExplored(x, y) {
    return exploredMap && exploredMap[y] && exploredMap[y][x] === 1;
  }
  
  // Update which AI elements should be visible based on exploration
  function updateAIVisibility() {
    if (!gameData?.ai) return;
    
    if (gameData.ai.cities) {
      gameData.ai.cities.forEach(city => {
        city.visible = isTileExplored(city.position.x, city.position.y);
      });
    }
    
    if (gameData.ai.units) {
      gameData.ai.units.forEach(unit => {
        unit.visible = isTileExplored(unit.position.x, unit.position.y);
      });
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

  async function saveAndExit() {
    try {
      // Save the current game state
      const saveData = {
        game_id: gameData.game_id,
        name: $gameState.gameName || "My Game",
        scenario_id: $gameState.currentScenario?._id || gameData.scenario_id,
        player: gameData.player,
        ai: gameData.ai,
        map: gameData.map,
        turn: gameData.turn,
        current_player: gameData.current_player,
        terrain: terrainMap,  // Save terrain data
        exploration: exploredMap  // Save exploration data
      };
      
      await gameAPI.saveGame(saveData);
      console.log("Game saved successfully");
      
      // End the game and navigate back to home
      endGame();
      navigate('/home');
    } catch (error) {
      console.error("Error saving game:", error);
      if (confirm("Failed to save game. Do you want to exit anyway?")) {
        endGame();
        navigate('/home');
      }
    }
  }
  
  function exitWithoutSaving() {
    if (confirm("Are you sure you want to exit without saving? All progress will be lost.")) {
      endGame();
      navigate('/home');
    }
  }

  function getTerrainColor(terrainType) {
    switch(terrainType) {
      case TERRAIN.DEEP_WATER: return '#0066cc';
      case TERRAIN.SHALLOW_WATER: return '#3399ff';
      case TERRAIN.DESERT: return '#e6cc99';
      case TERRAIN.GRASS: return '#66cc66';
      case TERRAIN.FOREST: return '#006633';
      case TERRAIN.PLAINS: return '#cccc99';
      case TERRAIN.HILLS: return '#996633';
      case TERRAIN.MOUNTAINS: return '#666666';
      case TERRAIN.SNOW: return '#ffffff';
      case TERRAIN.JUNGLE: return '#339933';
      default: return '#66cc66';
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

<svelte:head>
  <!-- Ensure full screen capabilities -->
  <style>
    body, html {
      margin: 0;
      padding: 0;
      overflow: hidden;
      height: 100%;
      width: 100%;
    }
  </style>
</svelte:head>

<div class="map-page">
  {#if isLoading}
    <div class="loading">
      <div class="loading-spinner"></div>
      <h2>Initializing Game...</h2>
      {#if loadingError}
        <div class="error-message">Error: {loadingError}</div>
        <button class="retry-button" on:click={initializeGame}>Retry</button>
      {/if}
    </div>
  {:else if loadingError}
    <div class="error">
      <h2>Error loading game</h2>
      <p>{loadingError}</p>
      <button on:click={() => navigate('/new-game')}>Back to New Game</button>
    </div>
  {:else if gameStarted}
    <!-- Game controls row -->
    <div class="map-controls">
      <div class="left-controls">
        <button class="menu-button" on:click={togglePauseMenu}>☰ Menu</button>
        <span class="game-info">Turn: {gameData.turn} | Difficulty: {gameData.difficulty?.charAt(0).toUpperCase() + gameData.difficulty?.slice(1) || 'Easy'}</span>
      </div>
      <div class="right-controls">
        <button on:click={zoomIn} title="Zoom In">+</button>
        <button on:click={zoomOut} title="Zoom Out">-</button>
        <button on:click={centerMapOnPlayer} title="Center Map">⌖</button>
      </div>
    </div>
    
    <div 
      class="map-container"
      class:blurred={showPauseMenu}
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
    
    <!-- Tile info overlay -->
    {#if selectedTile && !showPauseMenu}
      <div class="tile-info-overlay">
        <div class="tile-info-card">
          <div class="tile-info-header">
            <h4>Tile ({selectedTile.x}, {selectedTile.y})</h4>
            <button class="close-button" on:click={() => selectedTile = null}>×</button>
          </div>
          
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
      </div>
    {/if}
    
    <!-- Pause menu overlay -->
    {#if showPauseMenu}
      <div class="pause-menu-overlay">
        <div class="pause-menu">
          <div class="pause-header">
            <h2>Game Paused</h2>
            <button class="close-button" on:click={togglePauseMenu}>×</button>
          </div>
          
          <div class="menu-options">
            <button class="menu-option primary" on:click={togglePauseMenu}>
              Continue Game
            </button>
            
            <button class="menu-option" on:click={saveAndExit}>
              Save and Exit
            </button>
            
            <button class="menu-option danger" on:click={exitWithoutSaving}>
              Exit Without Saving
            </button>
          </div>
          
          <div class="game-details">
            <p>Game: {$gameState.gameName || "My Game"}</p>
            <p>Difficulty: {gameData.difficulty?.charAt(0).toUpperCase() + gameData.difficulty?.slice(1) || 'Easy'}</p>
            <p>Turn: {gameData?.turn || 1}</p>
          </div>
        </div>
      </div>
    {/if}
    
    <!-- Resources info at the bottom -->
    <div class="resources-overlay">
      <div class="resources-display">
        <div class="resource-item">
          <span class="resource-icon">🌾</span>
          <span class="resource-amount">{gameData?.player?.resources?.food || 0}</span>
        </div>
        <div class="resource-item">
          <span class="resource-icon">🔨</span>
          <span class="resource-amount">{gameData?.player?.resources?.production || 0}</span>
        </div>
        <div class="resource-item">
          <span class="resource-icon">📚</span>
          <span class="resource-amount">{gameData?.player?.resources?.science || 0}</span>
        </div>
        <div class="resource-item">
          <span class="resource-icon">💰</span>
          <span class="resource-amount">{gameData?.player?.resources?.gold || 0}</span>
        </div>
      </div>
    </div>
  {:else}
    <div class="error">
      <h2>Game not started</h2>
      <button on:click={() => navigate('/new-game')}>Start New Game</button>
    </div>
  {/if}
</div>

<style>
  .map-page {
    position: absolute;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: #000;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
  
  .blurred {
    filter: blur(2px);
  }

  .loading {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 100%;
    color: white;
    background-color: rgba(0, 0, 0, 0.8);
    gap: 20px;
  }

  .loading-spinner {
    border: 6px solid rgba(255, 255, 255, 0.3);
    border-top: 6px solid #4CAF50;
    border-radius: 50%;
    width: 50px;
    height: 50px;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  .error-message {
    color: #ff5252;
    background-color: rgba(255, 82, 82, 0.1);
    padding: 10px;
    border-radius: 5px;
    max-width: 80%;
    text-align: center;
  }

  .retry-button, .back-button {
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    background-color: #4CAF50;
    color: white;
    font-size: 16px;
    cursor: pointer;
    margin: 10px;
  }

  .back-button {
    background-color: #607D8B;
  }
  
  .map-controls {
    display: flex;
    justify-content: space-between;
    padding: 0.3rem 0.5rem;
    background-color: rgba(0, 0, 0, 0.7);
    color: white;
    z-index: 10;
  }
  
  .left-controls, .right-controls {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .map-controls button {
    padding: 0.3rem 0.6rem;
    background-color: #333;
    color: white;
    border: 1px solid #555;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .menu-button {
    font-size: 1.1rem;
  }
  
  .game-info {
    font-size: 0.9rem;
  }
  
  .map-container {
    flex: 1;
    position: relative;
    cursor: grab;
    background-color: #0066cc;
    overflow: hidden;
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
  
  .map-tile.selected {
    border: 2px solid #ffcc00;
    box-shadow: 0 0 10px #ffcc00;
    z-index: 5;
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
  
  /* Tile info overlay - Updated to ensure it stays on top */
  .tile-info-overlay {
    position: fixed; /* Changed from absolute to fixed */
    top: 60px;
    right: 10px;
    z-index: 200; /* Increased z-index */
    max-width: 300px;
    width: 100%;
    pointer-events: none;
  }
  
  .tile-info-card {
    background-color: rgba(0, 0, 0, 0.8);
    color: white;
    border-radius: 8px;
    padding: 1rem;
    pointer-events: auto;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.2); /* Added border for better visibility */
  }
  
  /* Updated tile-info-header styles for proper close button positioning */
  .tile-info-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
    width: 100%;
  }
  
  .close-button {
    background: none;
    border: none;
    color: white;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    line-height: 1;
    height: 24px;
    width: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .close-button:hover {
    color: #ff9999;
  }
  
  /* City, resource and unit markers */
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
  
  .resource-marker {
    position: absolute;
    z-index: 4;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 1rem;
    text-shadow: 0 0 3px white;
  }
  
  .unit-marker {
    position: absolute;
    z-index: 6;
    bottom: 2px;
    right: 2px;
    font-size: 1rem;
  }
  
  .unit-marker.enemy {
    text-shadow: 0 0 3px red;
  }
  
  .unit-marker.player {
    text-shadow: 0 0 3px green;
  }
  
  /* Fog of war */
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
  
  /* Pause menu */
  .pause-menu-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.7);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 300;
    filter: none;
  }
  
  .pause-menu {
    background-color: #1a1a1a;
    border: 2px solid #4CAF50;
    border-radius: 10px;
    padding: 2rem;
    width: 400px;
    color: white;
    filter: none;
  }
  
  .pause-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid #333;
    padding-bottom: 0.5rem;
  }
  
  .menu-options {
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    margin-bottom: 1.5rem;
  }
  
  .menu-option {
    padding: 0.8rem;
    border: none;
    border-radius: 4px;
    background-color: #333;
    color: white;
    cursor: pointer;
    font-size: 1rem;
    transition: all 0.2s;
  }
  
  .menu-option:hover {
    transform: translateY(-2px);
  }
  
  .menu-option.primary {
    background-color: #4CAF50;
    font-weight: bold;
  }
  
  .menu-option.danger {
    background-color: #f44336;
  }
  
  .game-details {
    font-size: 0.9rem;
    color: #aaa;
    border-top: 1px solid #333;
    padding-top: 1rem;
  }
  
  .game-details p {
    margin: 0.3rem 0;
  }

  /* Reset resources overlay to original styling */
  .resources-overlay {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: rgba(0, 0, 0, 0.7);
    padding: 0.5rem;
    z-index: 20; /* Original z-index */
  }
  
  .resources-display {
    display: flex;
    justify-content: center;
    gap: 2rem;
    color: white;
  }
  
  .resource-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .resource-icon {
    font-size: 1.2rem;
  }
  
  .resource-amount {
    font-weight: bold;
    font-size: 1.1rem;
  }
</style>
