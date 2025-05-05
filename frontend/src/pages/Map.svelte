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
  let grid = []; // Grid del mapa
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
  
  // Constantes para tipos de terreno
  const TERRAIN = {
    DEEP_WATER: 0,
    PLAINS: 1,
    FOREST: 2,
    MOUNTAINS: 3,
    HILLS: 4,
    DESERT: 5,
    SHALLOW_WATER: 6,
    GRASS: 7,
    SNOW: 8,
    JUNGLE: 9
  };

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
      
      // Intentar obtener el mapa del backend
      try {
        if (selectedMapId) {
          // Si tenemos un ID específico, intentamos cargarlo
          mapData = await gameAPI.getMapById(selectedMapId);
        } else {
          // De lo contrario, cargamos el primer mapa disponible
          mapData = await gameAPI.getFirstMap();
        }
        
        if (mapData) {
          console.log("Loaded map data:", mapData);
          
          // Configurar propiedades del mapa
          mapWidth = mapData.width || 30;
          mapHeight = mapData.height || 15;
          grid = mapData.grid || [];
          startPoint = mapData.startPoint || [15, 7];
          difficulty = mapData.difficulty || "medium";
          
          // Si no tenemos grid, creamos uno
          if (!grid || !grid.length || grid.length !== mapHeight) {
            initializeGrid();
          }
        } else {
          // Si no hay datos, inicializar con valores predeterminados
          mapWidth = 30;
          mapHeight = 15;
          initializeGrid();
        }
      } catch (apiError) {
        console.error("Error loading map:", apiError);
        // En caso de error, inicializar con valores predeterminados
        mapWidth = 30;
        mapHeight = 15;
        initializeGrid();
      }
      
      isLoading = false;
      
      // Centrar el mapa
      setTimeout(centerMapOnStartPoint, 200);
    } catch (error) {
      loadingError = error.message || "Error desconocido al iniciar el juego.";
      isLoading = false;
    }
  }
  
  function initializeGrid() {
    grid = Array(mapHeight).fill().map(() => Array(mapWidth).fill(TERRAIN.GRASS));
    
    // Generar un terreno aleatorio básico
    for (let y = 0; y < mapHeight; y++) {
      for (let x = 0; x < mapWidth; x++) {
        const rnd = Math.random();
        
        if (rnd < 0.05) grid[y][x] = TERRAIN.DEEP_WATER;
        else if (rnd < 0.1) grid[y][x] = TERRAIN.SHALLOW_WATER;
        else if (rnd < 0.3) grid[y][x] = TERRAIN.PLAINS;
        else if (rnd < 0.5) grid[y][x] = TERRAIN.GRASS;
        else if (rnd < 0.7) grid[y][x] = TERRAIN.FOREST;
        else if (rnd < 0.85) grid[y][x] = TERRAIN.HILLS;
        else if (rnd < 0.9) grid[y][x] = TERRAIN.MOUNTAINS;
        else if (rnd < 0.95) grid[y][x] = TERRAIN.DESERT;
        else grid[y][x] = TERRAIN.JUNGLE;
      }
    }
    
    // Asegurar que el punto de inicio sea terreno adecuado
    if (startPoint && startPoint.length === 2) {
      const [startX, startY] = startPoint;
      if (startX >= 0 && startX < mapWidth && startY >= 0 && startY < mapHeight) {
        grid[startY][startX] = TERRAIN.GRASS;
        
        // También hacer el área alrededor adecuada para empezar
        for (let y = Math.max(0, startY - 1); y <= Math.min(mapHeight - 1, startY + 1); y++) {
          for (let x = Math.max(0, startX - 1); x <= Math.min(mapWidth - 1, startX + 1); x++) {
            if (grid[y][x] === TERRAIN.DEEP_WATER || grid[y][x] === TERRAIN.MOUNTAINS) {
              grid[y][x] = TERRAIN.GRASS;
            }
          }
        }
      }
    }
  }

  function centerMapOnStartPoint() {
    if (startPoint && startPoint.length === 2) {
      const [startX, startY] = startPoint;
      const containerWidth = document.querySelector('.map-container')?.clientWidth || 800;
      const containerHeight = document.querySelector('.map-container')?.clientHeight || 600;

      offsetX = containerWidth / 2 - startX * tileSize * zoomLevel;
      offsetY = containerHeight / 2 - startY * tileSize * zoomLevel;
    }
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
      default: return '#66cc66'; // Grass as default
    }
  }
  
  function getTerrainName(terrainType) {
    switch (terrainType) {
      case TERRAIN.DEEP_WATER: return 'Aguas profundas';
      case TERRAIN.SHALLOW_WATER: return 'Aguas poco profundas';
      case TERRAIN.DESERT: return 'Desierto';
      case TERRAIN.GRASS: return 'Pradera';
      case TERRAIN.FOREST: return 'Bosque';
      case TERRAIN.PLAINS: return 'Llanuras';
      case TERRAIN.HILLS: return 'Colinas';
      case TERRAIN.MOUNTAINS: return 'Montañas';
      case TERRAIN.SNOW: return 'Nieve';
      case TERRAIN.JUNGLE: return 'Jungla';
      default: return 'Desconocido';
    }
  }
  
  function handleTileClick(x, y) {
    const terrain = grid[y] ? grid[y][x] : TERRAIN.GRASS;
    
    selectedTile = {
      x, y,
      terrain,
      terrainName: getTerrainName(terrain)
    };
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
            {@const terrain = grid[y] ? grid[y][x] : TERRAIN.GRASS}
            
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
              {#if x % 10 === 0 && y % 10 === 0}
                <div class="coord-marker">{x},{y}</div>
              {/if}
              
              {#if startPoint && startPoint[0] === x && startPoint[1] === y}
                <div class="start-marker">
                  <span class="start-icon">🏠</span>
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
            <div class="terrain-sample" style="background-color: {getTerrainColor(selectedTile.terrain)};"></div>
          </div>
          
          {#if startPoint && startPoint[0] === selectedTile.x && startPoint[1] === selectedTile.y}
            <div class="start-info">
              <h5>Punto de inicio del mapa</h5>
              <p>Esta es la posición inicial recomendada para comenzar la partida.</p>
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
</style>
