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

  let gameData = null;
  let mapSize = { width: 30, height: 15 };
  let tileSize = 24;
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
  let zoomLevel = 0.8;

  let activeUnit = null;
  let movementTiles = [];

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

  onMount(() => {
    try {
      if (!$user) {
        navigate('/');
        return;
      }

      window.addEventListener('keydown', handleKeyPress);
      initializeGame();

      return () => {
        window.removeEventListener('keydown', handleKeyPress);
      };
    } catch (err) {
      console.error("Error mounting Map component:", err);
      loadingError = err.message;
    }
  });

  function handleKeyPress(event) {
    if (event.key === 'Escape') {
      togglePauseMenu();
    }
  }

  function togglePauseMenu() {
    showPauseMenu = !showPauseMenu;
    pauseGame(showPauseMenu);
  }

  async function initializeGame() {
    try {
      isLoading = true;
      loadingError = null;

      createBasicGameData();

      try {
        const mapData = await gameAPI.getFirstMap();

        if (mapData) {
          mapSize = {
            width: mapData.width || 30,
            height: mapData.height || 15
          };

          if (mapData.grid && Array.isArray(mapData.grid)) {
            terrainMap = convertGridToTerrain(mapData.grid);

            if (mapData.fogOfWar && Array.isArray(mapData.fogOfWar)) {
              exploredMap = mapData.fogOfWar;
            } else {
              initializeFogOfWar(mapData.difficulty || gameData.difficulty);
            }

            if (mapData.startPoint && Array.isArray(mapData.startPoint) && mapData.startPoint.length === 2) {
              const [startX, startY] = mapData.startPoint;

              if (gameData.player?.cities?.length > 0) {
                gameData.player.cities[0].position.x = startX;
                gameData.player.cities[0].position.y = startY;

                if (gameData.player.cities.length > 1) {
                  gameData.player.cities[1].position.x = Math.min(startX + 3, mapSize.width - 1);
                  gameData.player.cities[1].position.y = Math.min(startY + 3, mapSize.height - 1);
                }
              }

              if (gameData.player?.units?.length > 0) {
                gameData.player.units[0].position.x = startX + 1;
                gameData.player.units[0].position.y = startY;

                if (gameData.player.units.length > 1) {
                  gameData.player.units[1].position.x = startX;
                  gameData.player.units[1].position.y = startY + 1;
                }
              }

              const radius = 3;
              for (let y = Math.max(0, startY - radius); y <= Math.min(mapSize.height - 1, startY + radius); y++) {
                for (let x = Math.max(0, startX - radius); x <= Math.min(mapSize.width - 1, startX + radius); x++) {
                  const distance = Math.sqrt(Math.pow(x - startX, 2) + Math.pow(y - startY, 2));
                  if (distance <= radius) {
                    exploredMap[y][x] = 1;
                  }
                }
              }
            }
          } else {
            initializeTerrainMap();
            initializeFogOfWar(gameData.difficulty);
          }
        } else {
          initializeTerrainMap();
          initializeFogOfWar(gameData.difficulty);
        }
      } catch (apiError) {
        initializeTerrainMap();
        initializeFogOfWar(gameData.difficulty);
      }

      gameData.map.explored = JSON.parse(JSON.stringify(exploredMap));
      updateRenderingArrays();

      gameStarted = true;
      isLoading = false;

      setTimeout(centerMapOnPlayer, 200);
    } catch (error) {
      loadingError = error.message || "Unknown error occurred while starting the game.";
      isLoading = false;
    }
  }

  function initializeFogOfWar(difficulty) {
    exploredMap = Array(mapSize.height).fill().map(() => Array(mapSize.width).fill(0));

    let exploreRadius;

    switch (difficulty) {
      case "easy":
        exploreRadius = 5;
        break;
      case "medium":
        exploreRadius = 3;
        break;
      case "hard":
        exploreRadius = 2;
        break;
      default:
        exploreRadius = 3;
    }

    if (gameData.player?.cities) {
      gameData.player.cities.forEach(city => {
        const centerX = city.position.x;
        const centerY = city.position.y;
        const radius = exploreRadius;

        for (let y = Math.max(0, centerY - radius); y <= Math.min(mapSize.height - 1, centerY + radius); y++) {
          for (let x = Math.max(0, centerX - radius); x <= Math.min(mapSize.width - 1, centerX + radius); x++) {
            const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));
            if (distance <= radius) {
              exploredMap[y][x] = 1;
            }
          }
        }
      });
    }

    if (gameData.player?.units) {
      gameData.player.units.forEach(unit => {
        const centerX = unit.position.x;
        const centerY = unit.position.y;
        const radius = exploreRadius - 1;

        for (let y = Math.max(0, centerY - radius); y <= Math.min(mapSize.height - 1, centerY + radius); y++) {
          for (let x = Math.max(0, centerX - radius); x <= Math.min(mapSize.width - 1, centerX + radius); x++) {
            const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));
            if (distance <= radius) {
              exploredMap[y][x] = 1;
            }
          }
        }
      });
    }

    updateAIVisibility();
  }

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

  function isTileExplored(x, y) {
    return exploredMap && exploredMap[y] && exploredMap[y][x] === 1;
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

  function centerMapOnPlayer() {
    if (gameData.player?.cities?.length > 0) {
      const firstCity = gameData.player.cities[0];
      const containerWidth = document.querySelector('.map-container')?.clientWidth || 800;
      const containerHeight = document.querySelector('.map-container')?.clientHeight || 600;

      offsetX = containerWidth / 2 - firstCity.position.x * tileSize * zoomLevel;
      offsetY = containerHeight / 2 - firstCity.position.y * tileSize * zoomLevel;
    }
  }

  function createBasicGameData() {
    const difficulty = $gameState.currentScenario?.difficulty || "easy";

    gameData = {
      game_id: "game_" + Date.now(),
      name: $gameState.gameName || "My Game",
      scenario_id: $gameState.currentScenario?._id || "default_scenario",
      created_at: new Date().toISOString(),
      last_saved: new Date().toISOString(),
      turn: 1,
      current_player: "player",
      difficulty: difficulty,
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

  function convertGridToTerrain(grid) {
    const height = grid.length;
    const width = grid[0]?.length || 30;
    let newTerrainMap = Array(height).fill().map(() => Array(width).fill(TERRAIN.GRASS));

    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        let tileValue = grid[y][x];

        if (typeof tileValue !== 'number' || tileValue < 0 || tileValue > 9) {
          const rnd = Math.random();
          if (rnd < 0.2) tileValue = TERRAIN.DEEP_WATER;
          else if (rnd < 0.3) tileValue = TERRAIN.SHALLOW_WATER;
          else if (rnd < 0.45) tileValue = TERRAIN.PLAINS;
          else if (rnd < 0.6) tileValue = TERRAIN.GRASS;
          else if (rnd < 0.75) tileValue = TERRAIN.FOREST;
          else if (rnd < 0.85) tileValue = TERRAIN.HILLS;
          else if (rnd < 0.9) tileValue = TERRAIN.MOUNTAINS;
          else if (rnd < 0.95) tileValue = TERRAIN.DESERT;
          else tileValue = TERRAIN.JUNGLE;
        }

        switch (tileValue) {
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
    terrainMap = Array(mapSize.height).fill().map(() => Array(mapSize.width).fill(TERRAIN.GRASS));
  }

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

  function getTerrainColor(terrainType) {
    switch (terrainType) {
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
    switch (terrainType) {
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

  function moveUnit(unit, newX, newY) {
    const tile = movementTiles.find(t => t.x === newX && t.y === newY);
    if (!tile) return;

    const gameUnit = gameData.player.units.find(u => u.id === unit.id);
    if (!gameUnit) return;

    const movementCost = tile.movementCost || 1;
    gameUnit.movement_points_left = Math.max(0, gameUnit.movement_points_left - movementCost);

    gameUnit.position.x = newX;
    gameUnit.position.y = newY;

    exploreArea(newX, newY, 2);

    gameData.map.explored = JSON.parse(JSON.stringify(exploredMap));

    const renderUnit = units.find(u => u.id === unit.id);
    if (renderUnit) {
      renderUnit.x = newX;
      renderUnit.y = newY;
      renderUnit.movementLeft = gameUnit.movement_points_left;
    }

    selectedTile = {
      x: newX,
      y: newY,
      terrain: terrainMap[newY][newX],
      city: cities.find(c => c.x === newX && c.y === newY),
      resource: resources.find(r => r.x === newX && r.y === newY),
      unit: renderUnit,
      explored: true
    };

    if (gameUnit.movement_points_left > 0) {
      activeUnit = renderUnit;
      movementTiles = calculateMovementOptions(renderUnit);
    } else {
      activeUnit = null;
      movementTiles = [];
    }
  }

  function skipUnitTurn(unit) {
    const gameUnit = gameData.player.units.find(u => u.id === unit.id);
    if (!gameUnit) return;

    gameUnit.movement_points_left = 0;

    const renderUnit = units.find(u => u.id === unit.id);
    if (renderUnit) {
      renderUnit.movementLeft = 0;
    }

    activeUnit = null;
    movementTiles = [];
  }

  function handleTileClick(x, y) {
    if (activeUnit && movementTiles.some(tile => tile.x === x && tile.y === y)) {
      moveUnit(activeUnit, x, y);
      return;
    }

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

    if (unit?.id !== activeUnit?.id) {
      activeUnit = null;
      movementTiles = [];
    }

    if (unit && unit.owner === 'player' && unit.movementLeft > 0) {
      activeUnit = unit;
      movementTiles = calculateMovementOptions(unit);
    }
  }

  function calculateMovementOptions(unit) {
    if (!unit || unit.movementLeft <= 0) return [];

    const options = [];
    const maxDistance = unit.movementLeft;
    const directions = [
      { dx: 0, dy: -1 },
      { dx: 1, dy: 0 },
      { dx: 0, dy: 1 },
      { dx: -1, dy: 0 },
      { dx: 1, dy: -1 },
      { dx: 1, dy: 1 },
      { dx: -1, dy: 1 },
      { dx: -1, dy: -1 }
    ];

    directions.forEach(dir => {
      const newX = unit.x + dir.dx;
      const newY = unit.y + dir.dy;

      if (newX >= 0 && newX < mapSize.width &&
        newY >= 0 && newY < mapSize.height &&
        isTileExplored(newX, newY)) {

        const terrain = terrainMap[newY][newX];
        if (isTerrainPassable(terrain, unit.type)) {
          const hasUnit = units.some(u => u.x === newX && u.y === newY);
          const hasEnemyCity = cities.some(c => c.x === newX && c.y === newY && c.owner !== 'player');

          if (!hasUnit && !hasEnemyCity) {
            options.push({ x: newX, y: newY, movementCost: getTerrainMovementCost(terrain) });
          }
        }
      }
    });

    return options;
  }

  function isTerrainPassable(terrain, unitType) {
    if (unitType === 'ship') {
      return terrain === TERRAIN.DEEP_WATER || terrain === TERRAIN.SHALLOW_WATER;
    }

    return terrain !== TERRAIN.DEEP_WATER;
  }

  function getTerrainMovementCost(terrain) {
    switch (terrain) {
      case TERRAIN.DEEP_WATER: return 1;
      case TERRAIN.SHALLOW_WATER: return 1;
      case TERRAIN.PLAINS: return 1;
      case TERRAIN.GRASS: return 1;
      case TERRAIN.DESERT: return 2;
      case TERRAIN.FOREST: return 2;
      case TERRAIN.HILLS: return 2;
      case TERRAIN.MOUNTAINS: return 3;
      case TERRAIN.JUNGLE: return 2;
      case TERRAIN.SNOW: return 2;
      default: return 1;
    }
  }

  function endTurn() {
    gameData.turn++;

    gameData.player.units.forEach(unit => {
      unit.movement_points_left = unit.movement_points || 2;
    });

    updateRenderingArrays();

    activeUnit = null;
    movementTiles = [];

    simulateAITurn();

    selectedTile = null;
  }

  function simulateAITurn() {
    console.log("AI turn completed");
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
      const saveData = {
        game_id: gameData.game_id,
        name: $gameState.gameName || "My Game",
        scenario_id: $gameState.currentScenario?._id || gameData.scenario_id,
        player: gameData.player,
        ai: gameData.ai,
        map: gameData.map,
        turn: gameData.turn,
        current_player: gameData.current_player,
        terrain: terrainMap,
        exploration: exploredMap
      };

      await gameAPI.saveGame(saveData);

      endGame();
      navigate('/home');
    } catch (error) {
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
</script>

<svelte:head>
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
    <div class="map-controls">
      <div class="left-controls">
        <button class="menu-button" on:click={togglePauseMenu}>☰ Menu</button>
        <span class="game-info">Turn: {gameData.turn} | Difficulty: {gameData.difficulty?.charAt(0).toUpperCase() + gameData.difficulty?.slice(1) || 'Easy'}</span>
      </div>
      <div class="center-controls">
        <button class="end-turn-button" on:click={endTurn}>End Turn</button>
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
            {@const isMoveTile = movementTiles.some(tile => tile.x === x && tile.y === y)}
            
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
              class:movement-option={isMoveTile}
            >
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
                  <div 
                    class="unit-marker" 
                    class:enemy={unit.owner === 'ai'} 
                    class:player={unit.owner === 'player'}
                    class:active={activeUnit && activeUnit.id === unit.id}
                    class:no-moves={unit.owner === 'player' && unit.movementLeft <= 0}
                  >
                    {unit.type === 'warrior' ? '⚔️' : 
                      unit.type === 'archer' ? '🏹' : 
                      unit.type === 'knight' ? '🐎' :
                      unit.type === 'settler' ? '👨‍🌾' :
                      unit.type === 'unknown' ? '❓' : '👨‍🌾'}
                      
                    {#if unit.owner === 'player'}
                      <div class="unit-moves">{unit.movementLeft}/{unit.movement}</div>
                    {/if}
                  </div>
                {/each}
              {/if}
              
              {#if isMoveTile}
                <div class="movement-indicator"></div>
              {/if}
            </div>
          {/each}
        {/each}
      </div>
      
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
              <p>Movement Cost: {getTerrainMovementCost(selectedTile.terrain)}</p>
            </div>
            
            {#if selectedTile.city}
              <div class="city-info">
                <h5>City: {selectedTile.city.name}</h5>
                <p>Size: {selectedTile.city.size}</p>
                <p>Owner: {selectedTile.city.owner === 'player' ? 'You' : 'AI'}</p>
                <p>Strength: {selectedTile.city.strength}</p>
                <p>Health: {selectedTile.city.health}/100</p>
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
                <p>Strength: {selectedTile.unit.strength}</p>
                <p>Health: {selectedTile.unit.health}/100</p>
                
                {#if selectedTile.unit.owner === 'player'}
                  <p>Movement: {selectedTile.unit.movementLeft}/{selectedTile.unit.movement}</p>
                  
                  {#if selectedTile.unit.movementLeft > 0}
                    <button 
                      class="unit-action-button"
                      on:click={() => {
                        activeUnit = selectedTile.unit;
                        movementTiles = calculateMovementOptions(selectedTile.unit);
                      }}
                    >
                      Move
                    </button>
                  {/if}
                  
                  <button class="unit-action-button" on:click={() => skipUnitTurn(selectedTile.unit)}>
                    Skip Turn
                  </button>
                {/if}
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
    align-items: center;
  }
  
  .left-controls, .right-controls {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .center-controls {
    display: flex;
    align-items: center;
  }
  
  .end-turn-button {
    padding: 0.5rem 1rem;
    background-color: #4CAF50;
    color: white;
    font-weight: bold;
    border: 2px solid #2E7D32;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
  }
  
  .end-turn-button:hover {
    background-color: #66BB6A;
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
  
  .movement-option {
    position: relative;
    border: 2px dashed rgba(255, 255, 255, 0.7) !important;
  }
  
  .movement-indicator {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(255, 255, 255, 0.2);
    pointer-events: none;
  }
  
  .tile-info-overlay {
    position: fixed;
    top: 60px;
    right: 10px;
    z-index: 200;
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
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
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
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  
  .unit-marker.enemy {
    text-shadow: 0 0 3px red;
  }
  
  .unit-marker.player {
    text-shadow: 0 0 3px green;
  }
  
  .unit-marker.active {
    filter: drop-shadow(0 0 4px yellow);
    transform: scale(1.2);
  }
  
  .unit-marker.no-moves {
    opacity: 0.6;
  }
  
  .unit-moves {
    font-size: 0.6rem;
    color: white;
    background-color: rgba(0, 0, 0, 0.5);
    border-radius: 2px;
    padding: 0 2px;
    margin-top: 2px;
  }
  
  .unit-action-button {
    background-color: #444;
    color: white;
    border: 1px solid #666;
    border-radius: 3px;
    padding: 3px 8px;
    margin: 2px;
    cursor: pointer;
    font-size: 0.9rem;
  }
  
  .unit-action-button:hover {
    background-color: #555;
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

  .resources-overlay {
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: rgba(0, 0, 0, 0.7);
    padding: 0.5rem;
    z-index: 20;
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
