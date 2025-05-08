<script>
  import { onMount } from 'svelte';
  import { navigate } from '../router.js';
  import { gameAPI } from '../services/gameAPI.js';
  import { gameState, pauseGame, endGame } from '../stores/gameState.js';
  import { user } from '../stores/auth.js';

  let showPauseMenu = false;
  let isLoading = true;
  let loadingError = null;
  let selectedMapId = null;

  // Propiedades del mapa
  let mapData = null;
  let tileSize = 32; // Tamaño de cada celda en píxeles
  let grid = []; // Grid del mapa (fog of war)
  let terrain = []; // Terreno del mapa
  let mapWidth = 0;
  let mapHeight = 0;
  let startPoint = [0, 0];
  let difficulty = "medium";

  // Propiedades de navegación
  let offsetX = 0;
  let offsetY = 0;
  let isDragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let zoomLevel = 1.0;

  // Información de selección
  let selectedTile = null;

  // Fog of War
  let showFogOfWar = true; // Estado para mostrar/ocultar el fog of war

  // Constantes para tipos de terreno real (según API)
  const TERRAIN_TYPES = {
    NORMAL: 0, // Tierra normal
    WATER: 1,  // Agua
    MINERAL: 2  // Mineral
  };

  // Constantes para fog of war
  const FOG_OF_WAR = {
    HIDDEN: 0, // No visible
    VISIBLE: 1 // Visible
  };

  let units = []; // Array to store units from the game JSON
  let gameData = null; // To store session game data

  // Unit movement state
  let selectedUnit = null;
  let validMoveTargets = [];
  let movementInProgress = false;

  onMount(async () => {
    try {
      // Verificar si el usuario está autenticado
      if (!$user) {
        navigate('/');
        return;
      }

      // Escuchar eventos de teclado para el menú de pausa
      window.addEventListener('keydown', handleKeyPress);

      // Obtener el ID del mapa seleccionado del estado del juego o usar uno predeterminado
      selectedMapId = $gameState?.currentScenario?.mapId;
      console.log("Selected map ID:", selectedMapId);

      // Inicializar el juego
      await initializeGame();

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

      // Intentar obtener el juego de la sesión primero
      try {
        // First, try to load game data from the session via an API call
        gameData = await gameAPI.getCurrentGame();
        console.log("Game data from session:", gameData);

        if (gameData) {
          // We have game data from session, use this for map rendering
          console.log("Using game data from session");

          // Get map data from the game object
          mapData = gameData.map_data || {};
          console.log("Map data from session game:", mapData);

          // Configure map properties from the map_data
          mapWidth = gameData.map_size?.width || mapData.width || 30;
          mapHeight = gameData.map_size?.height || mapData.height || 15;
          grid = mapData.grid || [];
          terrain = mapData.terrain || [];
          startPoint = mapData.startPoint || [15, 7];
          difficulty = gameData.difficulty || mapData.difficulty || "medium";

          // Load units from player.units
          if (gameData.player && Array.isArray(gameData.player.units)) {
            units = gameData.player.units;
            console.log("Units loaded from session game:", units);
          } else {
            units = [];
            console.log("No units found in session game data");
          }
        } else {
          // If no game in session, try to load a map directly
          if (selectedMapId) {
            // Si tenemos un ID específico, intentamos cargarlo
            mapData = await gameAPI.getMapById(selectedMapId);
            console.log("Loaded map by ID:", mapData);
          } else {
            // De lo contrario, cargamos el primer mapa disponible
            mapData = await gameAPI.getFirstMap();
            console.log("Loaded first available map:", mapData);
          }

          if (mapData) {
            // Configure map properties
            mapWidth = mapData.width || 30;
            mapHeight = mapData.height || 15;
            grid = mapData.grid || [];
            terrain = mapData.terrain || [];
            startPoint = mapData.startPoint || [15, 7];
            difficulty = mapData.difficulty || "medium";
            units = []; // No units when just loading a map
          }
        }

        // Si no tenemos grid o terrain, los inicializamos
        if (!grid || !grid.length || grid.length !== mapHeight) {
          initializeFogOfWar();
        }

        if (!terrain || !terrain.length || terrain.length !== mapHeight) {
          initializeTerrain();
        }
      } catch (apiError) {
        console.error("Error loading game/map:", apiError);
        // En caso de error, inicializar con valores predeterminados
        mapWidth = 30;
        mapHeight = 15;
        initializeFogOfWar();
        initializeTerrain();
        units = [];
      }

      isLoading = false;

      // Centrar el mapa
      setTimeout(centerMapOnStartPoint, 200);
    } catch (error) {
      loadingError = error.message || "Error desconocido al iniciar el juego.";
      isLoading = false;
    }
  }

  // Función para inicializar el fog of war
  function initializeFogOfWar() {
    grid = Array(mapHeight).fill().map(() => Array(mapWidth).fill(FOG_OF_WAR.HIDDEN));

    // Si tenemos un punto de inicio, hacemos visible esa zona
    if (startPoint && startPoint.length === 2) {
      const [startX, startY] = startPoint;
      const visibilityRadius = 3;

      for (let y = Math.max(0, startY - visibilityRadius); y <= Math.min(mapHeight - 1, startY + visibilityRadius); y++) {
        for (let x = Math.max(0, startX - visibilityRadius); x <= Math.min(mapWidth - 1, startX + visibilityRadius); x++) {
          // Calculamos la distancia al punto de inicio
          const distance = Math.sqrt(Math.pow(x - startX, 2) + Math.pow(y - startY, 2));

          // Si está dentro del radio de visibilidad, lo hacemos visible
          if (distance <= visibilityRadius) {
            grid[y][x] = FOG_OF_WAR.VISIBLE;
          }
        }
      }
    }
  }

  // Función para inicializar el terreno
  function initializeTerrain() {
    terrain = Array(mapHeight).fill().map(() => Array(mapWidth).fill(TERRAIN_TYPES.NORMAL));

    // Generar un terreno aleatorio básico
    for (let y = 0; y < mapHeight; y++) {
      for (let x = 0; x < mapWidth; x++) {
        const rnd = Math.random();

        if (rnd < 0.15) {
          terrain[y][x] = TERRAIN_TYPES.WATER; // 15% agua
        } else if (rnd < 0.25) {
          terrain[y][x] = TERRAIN_TYPES.MINERAL; // 10% minerales
        } else {
          terrain[y][x] = TERRAIN_TYPES.NORMAL; // 75% tierra normal
        }
      }
    }

    // Asegurar que el punto de inicio sea terreno adecuado
    if (startPoint && startPoint.length === 2) {
      const [startX, startY] = startPoint;
      if (startX >= 0 && startX < mapWidth && startY >= 0 && startY < mapHeight) {
        terrain[startY][startX] = TERRAIN_TYPES.NORMAL;

        // También hacer el área alrededor adecuada para empezar
        for (let y = Math.max(0, startY - 1); y <= Math.min(mapHeight - 1, startY + 1); y++) {
          for (let x = Math.max(0, startX - 1); x <= Math.min(mapWidth - 1, startX + 1); x++) {
            if (terrain[y][x] === TERRAIN_TYPES.WATER) {
              terrain[y][x] = TERRAIN_TYPES.NORMAL;
            }
          }
        }
      }
    }
  }

  // Función para centrar el mapa en el punto de inicio
  function centerMapOnStartPoint() {
    if (startPoint && startPoint.length === 2) {
      const [startX, startY] = startPoint;
      // Calcula la posición central de la pantalla
      const containerWidth = window.innerWidth;
      const containerHeight = window.innerHeight;

      // Ajusta el offset para centrar el punto de inicio
      offsetX = (containerWidth / 2) - (startX * tileSize * zoomLevel);
      offsetY = (containerHeight / 2) - (startY * tileSize * zoomLevel);
    }
  }

  // Función para alternar el fog of war
  function toggleFogOfWar() {
    showFogOfWar = !showFogOfWar;
  }

  function getTerrainColor(terrainType) {
    switch (terrainType) {
      case TERRAIN_TYPES.WATER: return '#3399ff'; // Azul para agua
      case TERRAIN_TYPES.MINERAL: return '#cc9900'; // Dorado para minerales
      case TERRAIN_TYPES.NORMAL: return '#66cc66'; // Verde para tierra normal
      default: return '#66cc66'; // Verde por defecto
    }
  }

  function getTerrainName(terrainType) {
    switch (terrainType) {
      case TERRAIN_TYPES.WATER: return 'Agua';
      case TERRAIN_TYPES.MINERAL: return 'Terreno mineralizado';
      case TERRAIN_TYPES.NORMAL: return 'Tierra';
      default: return 'Desconocido';
    }
  }

  // Enhanced tile click handler to support unit selection and movement
  function handleTileClick(x, y) {
    // If a unit is already selected and we click on a valid move target
    if (selectedUnit && validMoveTargets.some(target => target.x === x && target.y === y)) {
      moveUnitToPosition(selectedUnit, x, y);
      return;
    }
    
    // Check if there's a unit at this position to select
    const unitAtPosition = units.find(unit => 
      unit && 
      unit.position && 
      Array.isArray(unit.position) && 
      unit.position[0] === x && 
      unit.position[1] === y
    );
    
    // If we found a unit and it's not exhausted, select it
    if (unitAtPosition && (!unitAtPosition.status || unitAtPosition.status !== 'exhausted')) {
      selectUnit(unitAtPosition);
      return;
    } else if (unitAtPosition) {
      // If unit is exhausted, just show a message
      alert("Esta unidad ya ha agotado sus movimientos este turno.");
      selectedUnit = null;
      validMoveTargets = [];
    } else {
      // No unit found, clear selection
      selectedUnit = null;
      validMoveTargets = [];
    }
    
    // Handle regular tile info (original behavior)
    if (showFogOfWar && grid[y] && grid[y][x] === FOG_OF_WAR.HIDDEN) {
      selectedTile = {
        x, y,
        terrainName: 'Desconocido (no explorado)',
        isExplored: false
      };
    } else {
      const terrainType = terrain[y] ? terrain[y][x] : TERRAIN_TYPES.NORMAL;

      selectedTile = {
        x, y,
        terrain: terrainType,
        terrainName: getTerrainName(terrainType),
        isExplored: grid[y] && grid[y][x] === FOG_OF_WAR.VISIBLE
      };
    }
  }

  // Select a unit and calculate its possible move targets
  function selectUnit(unit) {
    selectedUnit = unit;
    validMoveTargets = [];
    
    // Get unit's available movement points
    const movementPoints = unit.movement || 2;
    
    // Get current position
    const [unitX, unitY] = unit.position;
    
    // For each movement point, calculate valid adjacent tiles
    calculateValidMoveTargets(unitX, unitY, movementPoints);
  }
  
  // Calculate valid movement targets based on unit's position and movement points
  function calculateValidMoveTargets(startX, startY, movementPoints) {
    // Reset valid targets
    validMoveTargets = [];
    
    // Use breadth-first search to find all reachable tiles within movement points
    const queue = [[startX, startY, movementPoints]];
    const visited = {};
    
    while (queue.length > 0) {
      const [x, y, remainingMovement] = queue.shift();
      
      // Skip if out of bounds
      if (x < 0 || x >= mapWidth || y < 0 || y >= mapHeight) continue;
      
      // Skip if this is water terrain
      if (terrain[y] && terrain[y][x] === TERRAIN_TYPES.WATER) continue;
      
      // Skip if already visited with better movement
      const key = `${x},${y}`;
      if (visited[key] !== undefined && visited[key] >= remainingMovement) continue;
      
      // Mark as visited with current movement
      visited[key] = remainingMovement;
      
      // Add to valid targets if not the starting position
      if (x !== startX || y !== startY) {
        validMoveTargets.push({ x, y, remainingMovement });
      }
      
      // If we still have movement points, explore adjacent tiles
      if (remainingMovement > 0) {
        // Only allow orthogonal movement (no diagonals)
        queue.push([x+1, y, remainingMovement-1]); // Right
        queue.push([x-1, y, remainingMovement-1]); // Left
        queue.push([x, y+1, remainingMovement-1]); // Down
        queue.push([x, y-1, remainingMovement-1]); // Up
      }
    }
  }
  
  // Move the selected unit to a target position
  async function moveUnitToPosition(unit, targetX, targetY) {
    if (movementInProgress) return;
    movementInProgress = true;
    
    try {
      const targetInfo = validMoveTargets.find(target => 
        target.x === targetX && target.y === targetY
      );
      
      if (!targetInfo) {
        console.error("Target position not in valid moves");
        movementInProgress = false;
        return;
      }
      
      const localUnitIndex = units.findIndex(u => u === unit); // Find in local reactive 'units' array
      
      if (localUnitIndex !== -1) {
        const originalUnitPosition = [...units[localUnitIndex].position]; // Capture original position from local unit

        // Update position in local 'units' array for Svelte reactivity
        units[localUnitIndex].position = [targetX, targetY];
        
        const totalMovement = units[localUnitIndex].movement || 2;
        const movementRemaining = targetInfo.remainingMovement;
        
        if (movementRemaining <= 0) {
          units[localUnitIndex].status = 'exhausted';
        } else {
          units[localUnitIndex].status = 'moved';
        }
        
        units = [...units]; // Trigger Svelte reactivity
        
        // Update the unit in the main 'gameData' object, which will be sent to session
        if (gameData && gameData.player && Array.isArray(gameData.player.units)) {
          let gameDataUnitIndex = -1;

          // Try to find by a unique ID (e.g., unit._id if it's from DB)
          // Ensure 'unit.id' is the correct unique identifier.
          if (unit.id) { // 'unit' here is the one selected from the 'units' array
            gameDataUnitIndex = gameData.player.units.findIndex(u => u.id === unit.id);
          }
          
          // Fallback: if no ID or ID match failed, try by type and original position
          if (gameDataUnitIndex === -1) {
            gameDataUnitIndex = gameData.player.units.findIndex(u =>
              u.type_id === unit.type_id && // 'unit.type_id' from selected unit
              u.position && Array.isArray(u.position) &&
              u.position[0] === originalUnitPosition[0] &&
              u.position[1] === originalUnitPosition[1]
            );
          }
          
          if (gameDataUnitIndex !== -1) {
            gameData.player.units[gameDataUnitIndex].position = [targetX, targetY];
            gameData.player.units[gameDataUnitIndex].status = units[localUnitIndex].status;
            
            console.log(`Unit updated in gameData: ID ${unit.id || 'N/A'}, New Pos [${targetX},${targetY}], Status ${units[localUnitIndex].status}`);

            try {
              await gameAPI.updateGameSession(gameData); // Send the whole gameData to update session
              console.log('Game session updated on server.');
            } catch (error) {
              console.error("Failed to update game session on server:", error);
              // Optionally, revert local changes or notify user
            }
          } else {
            console.warn("Moved unit not found in gameData.player.units. Session not updated for this unit.");
          }
        }
        
        updateFogOfWarAroundPosition(targetX, targetY, 2);
        
        selectedUnit = null;
        validMoveTargets = [];
      } else {
         console.error("Selected unit not found in local 'units' array.");
      }
    } catch(err) {
      console.error("Error in moveUnitToPosition:", err);
    } 
    finally {
      movementInProgress = false;
    }
  }
  
  // Update fog of war around a position
  function updateFogOfWarAroundPosition(centerX, centerY, radius) {
    if (!showFogOfWar) return;
    
    for (let y = Math.max(0, centerY - radius); y <= Math.min(mapHeight - 1, centerY + radius); y++) {
      for (let x = Math.max(0, centerX - radius); x <= Math.min(mapWidth - 1, centerX + radius); x++) {
        // Calculate distance to center
        const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));
        
        // If within radius, mark as visible
        if (distance <= radius && grid[y] && grid[y][x] !== undefined) {
          grid[y][x] = FOG_OF_WAR.VISIBLE;
        }
      }
    }
    
    // Force update of grid to trigger reactivity
    grid = [...grid];
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
      if (gameData) {
        // Step 1: Ensure the latest gameData (with all local changes) is in the backend session
        console.log("Updating game session before saving and exiting...", gameData);
        await gameAPI.updateGameSession(gameData);
        
        // Step 2: Tell the backend to persist the session's game to the database
        console.log("Requesting backend to save current game session to DB...");
        await gameAPI.saveCurrentGameSession();
        console.log("Game saved and session persisted.");
      }
      endGame(); // This should clear local stores (like $gameState)
      navigate('/home');
    } catch (error) {
      console.error("Error saving and exiting game:", error);
      // Provide more specific feedback if possible
      alert(`Error saving game: ${error.message}. Please try again or exit without saving.`);
    }
  }

  function exitWithoutSaving() {
    if (confirm("¿Estás seguro de que quieres salir sin guardar? Se perderá todo el progreso.")) {
      endGame();
      navigate('/home');
    }
  }

  function getUnitIcon(unitType) {
    // Return an appropriate icon for each unit type
    switch (unitType) {
      case "settler":
        return "🏠";
      case "warrior":
        return "⚔️";
      case "archer":
        return "🏹";
      case "cavalry":
        return "🐎";
      case "builder":
        return "🔨";
      default:
        return "❓";
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
      <h2>Inicializando juego...</h2>
      {#if loadingError}
        <div class="error-message">Error: {loadingError}</div>
        <button class="retry-button" on:click={initializeGame}>Reintentar</button>
      {/if}
    </div>
  {:else if loadingError}
    <div class="error">
      <h2>Error al cargar el juego</h2>
      <p>{loadingError}</p>
      <button on:click={() => navigate('/new-game')}>Volver a Nueva Partida</button>
    </div>
  {:else}
    <div class="map-controls">
      <div class="left-controls">
        <button class="menu-button" on:click={togglePauseMenu}>☰ Menú</button>
        <span class="game-info">Tamaño del mapa: {mapWidth}x{mapHeight} | Dificultad: {difficulty}</span>
      </div>
      <div class="right-controls">
        <button on:click={toggleFogOfWar} title="{showFogOfWar ? 'Desactivar' : 'Activar'} Niebla de Guerra" class:active={showFogOfWar}>
          {showFogOfWar ? '👁️' : '🌫️'} Niebla
        </button>
        <button on:click={zoomIn} title="Aumentar zoom">+</button>
        <button on:click={zoomOut} title="Reducir zoom">-</button>
        <button on:click={centerMapOnStartPoint} title="Centrar mapa">⌖</button>
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
        {#each Array(mapHeight) as _, y}
          {#each Array(mapWidth) as _, x}
            {@const isVisible = !showFogOfWar || (grid[y] && grid[y][x] === FOG_OF_WAR.VISIBLE)}
            {@const terrainType = terrain[y] && terrain[y][x] !== undefined ? terrain[y][x] : TERRAIN_TYPES.NORMAL}
            {@const isValidMoveTarget = validMoveTargets.some(target => target.x === x && target.y === y)}
            {@const unitAtPosition = units.find(unit => 
              unit && 
              unit.position && 
              Array.isArray(unit.position) && 
              unit.position.length >= 2 && 
              unit.position[0] === x && 
              unit.position[1] === y
            )}
            {@const isSelectedUnit = selectedUnit && unitAtPosition === selectedUnit}
            
            <div 
              class="map-tile"
              class:fog={showFogOfWar && !isVisible}
              class:water={isVisible && terrainType === TERRAIN_TYPES.WATER}
              class:mineral={isVisible && terrainType === TERRAIN_TYPES.MINERAL}
              class:valid-move={isVisible && isValidMoveTarget}
              class:selected-unit-tile={isVisible && isSelectedUnit}
              style="
                left: {x * tileSize}px;
                top: {y * tileSize}px;
                width: {tileSize}px;
                height: {tileSize}px;
                background-color: {isVisible ? getTerrainColor(terrainType) : '#000'};
              "
              on:click={() => handleTileClick(x, y)}
              class:selected={selectedTile && selectedTile.x === x && selectedTile.y === y}
            >
              {#if x % 10 === 0 && y % 10 === 0 && isVisible}
                <div class="coord-marker">{x},{y}</div>
              {/if}
              
              {#if unitAtPosition && isVisible}
                <div 
                  class="unit-marker" 
                  class:selected={isSelectedUnit}
                  class:exhausted={unitAtPosition.status === 'exhausted'}
                  title="{unitAtPosition.name || unitAtPosition.type_id} {unitAtPosition.status ? '(' + unitAtPosition.status + ')' : ''}"
                >
                  <span class="unit-icon">{getUnitIcon(unitAtPosition.type_id)}</span>
                </div>
              {/if}
            </div>
          {/each}
        {/each}
      </div>
    </div>
    
    {#if selectedTile && !showPauseMenu}
      <div class="tile-info-overlay">
        <div class="tile-info-card">
          <div class="tile-info-header">
            <h4>Casilla ({selectedTile.x}, {selectedTile.y})</h4>
            <button class="close-button" on:click={() => selectedTile = null}>×</button>
          </div>
          
          <div class="terrain-info">
            <h5>Terreno: {selectedTile.terrainName}</h5>
            {#if selectedTile.isExplored !== false}
              <div class="terrain-sample" style="background-color: {getTerrainColor(selectedTile.terrain)};"></div>
            {/if}
          </div>
          
          {#if startPoint && startPoint[0] === selectedTile.x && startPoint[1] === selectedTile.y}
            <div class="start-info">
              <h5>Punto de inicio del mapa</h5>
              <p>Esta es la posición inicial recomendada para comenzar la partida.</p>
            </div>
          {/if}
          
          {#if selectedTile.isExplored === false}
            <div class="fog-info">
              <p>Esta zona no ha sido explorada todavía.</p>
            </div>
          {/if}
        </div>
      </div>
    {/if}
    
    {#if showPauseMenu}
      <div class="pause-menu-overlay">
        <div class="pause-menu">
          <div class="pause-header">
            <h2>Juego Pausado</h2>
            <button class="close-button" on:click={togglePauseMenu}>×</button>
          </div>
          
          <div class="menu-options">
            <button class="menu-option primary" on:click={togglePauseMenu}>
              Continuar Partida
            </button>
            
            <button class="menu-option" on:click={saveAndExit}>
              Guardar y Salir
            </button>
            
            <button class="menu-option danger" on:click={exitWithoutSaving}>
              Salir sin Guardar
            </button>
          </div>
          
          <div class="game-details">
            <p>Nombre: {$gameState.gameName || "Mi Partida"}</p>
            <p>Dificultad: {difficulty}</p>
            <p>Tamaño del mapa: {mapWidth}x{mapHeight}</p>
          </div>
        </div>
      </div>
    {/if}
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

  .retry-button {
    padding: 10px 20px;
    border: none;
    border-radius: 5px;
    background-color: #4CAF50;
    color: white;
    font-size: 16px;
    cursor: pointer;
    margin: 10px;
  }
  
  .map-controls {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 1rem;
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
  
  .menu-button, .right-controls button {
    padding: 0.3rem 0.6rem;
    background-color: #444;
    color: white;
    border: 1px solid #666;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .menu-button:hover, .right-controls button:hover {
    background-color: #555;
  }
  
  .game-info {
    margin-left: 1rem;
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
  
  .map-tile.fog {
    background-color: #000 !important;
    border: 1px solid #222;
  }
  
  .map-tile.water {
    background-color: #3399ff;
    border: 1px solid rgba(0, 0, 150, 0.3);
    animation: waterWave 2s infinite alternate;
  }
  
  @keyframes waterWave {
    from { border-color: rgba(0, 0, 150, 0.3); }
    to { border-color: rgba(100, 200, 255, 0.7); }
  }
  
  .map-tile.mineral {
    background-color: #cc9900;
    border: 1px solid rgba(150, 100, 0, 0.5);
    position: relative;
    overflow: hidden;
  }
  
  .map-tile.mineral::after {
    content: "💎";
    position: absolute;
    font-size: 0.7rem;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    opacity: 0.7;
  }
  
  .map-tile.valid-move {
    box-shadow: inset 0 0 10px rgba(255, 255, 0, 0.7);
    cursor: pointer;
    border: 1px dashed #ffcc00;
  }
  
  .map-tile.selected-unit-tile {
    box-shadow: inset 0 0 10px rgba(255, 255, 255, 0.9);
  }
  
  .right-controls button {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-left: 5px;
    font-size: 0.9rem;
  }
  
  .right-controls button.active {
    background-color: #4CAF50;
    border-color: #2E7D32;
    box-shadow: 0 0 5px rgba(76, 175, 80, 0.5);
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
  
  .start-marker {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 5;
  }
  
  .start-icon {
    font-size: 1.2rem;
    filter: drop-shadow(0px 0px 2px black);
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
  
  .terrain-info {
    display: flex;
    flex-direction: column;
    margin-bottom: 1rem;
  }
  
  .terrain-sample {
    width: 100%;
    height: 20px;
    border-radius: 4px;
    margin-top: 0.5rem;
  }
  
  .start-info {
    background-color: rgba(76, 175, 80, 0.2);
    padding: 0.5rem;
    border-radius: 4px;
    margin-top: 0.5rem;
  }
  
  .start-info h5 {
    margin: 0 0 0.5rem 0;
    color: #4CAF50;
  }
  
  .start-info p {
    margin: 0;
    font-size: 0.9rem;
  }
  
  .fog-info {
    background-color: rgba(0, 0, 0, 0.2);
    padding: 0.5rem;
    border-radius: 4px;
    margin-top: 0.5rem;
  }
  
  .fog-info p {
    margin: 0;
    font-size: 0.9rem;
    color: #aaa;
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
  }
  
  .pause-menu {
    background-color: #1a1a1a;
    border: 2px solid #4CAF50;
    border-radius: 10px;
    padding: 2rem;
    width: 400px;
    color: white;
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
  
  .error {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: white;
    text-align: center;
  }
  
  .error button {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .unit-marker {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 15; /* Ensure units appear above terrain */
    transition: transform 0.2s ease; /* Smooth hover effect */
  }
  
  .unit-marker:hover {
    transform: scale(1.2); /* Slightly enlarge on hover */
    z-index: 20; /* Bring to front when hovering */
  }
  
  .unit-marker.selected {
    animation: pulse 1.5s infinite;
    z-index: 25;
  }
  
  .unit-marker.exhausted {
    opacity: 0.6;
    filter: grayscale(70%);
  }
  
  @keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.2); }
    100% { transform: scale(1); }
  }
</style>
