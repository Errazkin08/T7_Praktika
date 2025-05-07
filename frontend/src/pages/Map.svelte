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

  function handleTileClick(x, y) {
    // Si el tile no es visible y el fog of war está activado, no mostramos información
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
      // Implementación básica: solo volvemos al inicio
      endGame();
      navigate('/home');
    } catch (error) {
      console.error("Error saving game:", error);
      if (confirm("Error al guardar la partida. ¿Deseas salir de todas formas?")) {
        endGame();
        navigate('/home');
      }
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
            
            <div 
              class="map-tile"
              class:fog={showFogOfWar && !isVisible}
              class:water={isVisible && terrainType === TERRAIN_TYPES.WATER}
              class:mineral={isVisible && terrainType === TERRAIN_TYPES.MINERAL}
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
              
              <!-- Display units on map - only showing one unit per tile -->
              {#if units && units.length > 0 && isVisible}
                {@const unitAtPosition = units.find(unit => 
                  unit && 
                  unit.position && 
                  Array.isArray(unit.position) && 
                  unit.position.length >= 2 && 
                  unit.position[0] === x && 
                  unit.position[1] === y
                )}
                
                {#if unitAtPosition}
                  <div class="unit-marker" title={unitAtPosition.name || unitAtPosition.type_id}>
                    <span class="unit-icon">{getUnitIcon(unitAtPosition.type_id)}</span>
                  </div>
                {/if}
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
  
  .unit-icon {
    font-size: 1.6rem; /* Larger icon */
    filter: drop-shadow(0px 0px 3px rgba(0,0,0,0.9));
    text-shadow: 1px 1px 2px black;
  }
</style>
