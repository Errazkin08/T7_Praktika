<script>
  import { onMount, onDestroy } from 'svelte';
  import { navigate } from '../router.js';
  import { gameAPI } from '../services/gameAPI.js';
  import { gameState, pauseGame, endGame, currentTurn, currentPlayer } from '../stores/gameState.js';
  import { user } from '../stores/auth.js';
  import '../styles/pages/map.css'; 

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
  let zoomLevel = 1.8; // Increased from 1.0 to make map appear larger initially

  // Información de selección
  let selectedTile = null;
  let selectedUnitInfo = null; // New state variable for unit info display
  let selectedCityInfo = null; // New state variable for city info display

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

  // Add these variables for toast notifications
  let showToast = false;
  let toastMessage = "";
  let toastType = "success"; // Can be "success", "error", "warning"
  let toastTimeout;

  // Add new state variables for city founding
  let showCityFoundingModal = false;
  let newCityName = "";
  let settlerToFoundCity = null;
  let cities = []; // Array to store all cities

  // Function to show a toast notification
  function showToastNotification(message, type = "success", duration = 3000) {
    if (toastTimeout) clearTimeout(toastTimeout);
    toastMessage = message;
    toastType = type;
    showToast = true;
    toastTimeout = setTimeout(() => {
      showToast = false;
    }, duration);
  }

  // Function to display the found city modal
  function showFoundCityDialog(settler) {
    settlerToFoundCity = settler;
    newCityName = `Ciudad ${Math.floor(Math.random() * 1000)}`;
    showCityFoundingModal = true;
  }

  // Function to cancel city founding
  function cancelCityFounding() {
    showCityFoundingModal = false;
    settlerToFoundCity = null;
    newCityName = "";
  }

  // Function to found a city at the current settler's position
  function foundCity() {
    if (!settlerToFoundCity || !newCityName.trim()) {
      showToastNotification("Se requiere un nombre para la ciudad", "error");
      return;
    }

    try {
      const [x, y] = settlerToFoundCity.position;
      if (terrain[y] && terrain[y][x] === TERRAIN_TYPES.WATER) {
        showToastNotification("No se puede fundar una ciudad en el agua", "error");
        return;
      }

      const existingCity = cities.find(city => 
        (city.position.x === x && city.position.y === y) || 
        (Array.isArray(city.position) && city.position[0] === x && city.position[1] === y)
      );

      if (existingCity) {
        showToastNotification("Ya existe una ciudad en esta posición", "error");
        return;
      }

      const requiredResources = { food: 100, gold: 50 };
      const playerResources = gameData?.player?.resources || {};
      
      if (playerResources.food < requiredResources.food || playerResources.gold < requiredResources.gold) {
        showToastNotification(`Recursos insuficientes. Se necesita: ${requiredResources.food} comida, ${requiredResources.gold} oro`, "error");
        return;
      }

      const cityId = `city-${Date.now()}`;
      const newCity = {
        id: cityId,
        name: newCityName,
        position: { x, y },
        population: 0,
        buildings: [],
        production: {
          current_item: null,
          turns_remaining: 0
        }
      };

      cities = [...cities, newCity];

      if (gameData && gameData.player) {
        if (!gameData.player.cities) {
          gameData.player.cities = [];
        }
        gameData.player.cities.push(newCity);

        gameData.player.resources.food -= requiredResources.food;
        gameData.player.resources.gold -= requiredResources.gold;

        const settlerIndex = units.findIndex(u => u === settlerToFoundCity);
        if (settlerIndex !== -1) {
          units.splice(settlerIndex, 1);
          units = [...units];
        }

        if (gameData.player.units) {
          const gameDataSettlerIndex = gameData.player.units.findIndex(u => 
            u.id === settlerToFoundCity.id || 
            (u.position[0] === settlerToFoundCity.position[0] && u.position[1] === settlerToFoundCity.position[1])
          );
          
          if (gameDataSettlerIndex !== -1) {
            gameData.player.units.splice(gameDataSettlerIndex, 1);
          }
        }

        updateFogOfWarAroundPosition(x, y, 3);

        showToastNotification(`¡Ciudad ${newCityName} fundada con éxito!`, "success");
      }

      showCityFoundingModal = false;
      settlerToFoundCity = null;
      selectedUnitInfo = null;
      newCityName = "";

      try {
        gameAPI.updateGameSession(gameData);
      } catch (error) {
        console.error("Error saving game after founding city:", error);
      }
    } catch (error) {
      console.error("Error founding city:", error);
      showToastNotification("Error al fundar la ciudad: " + error.message, "error");
    }
  }

  // Function to get city icon
  function getCityIcon(city) {
    const population = city.population || 0;
    if (population >= 10) return { type: "emoji", value: "🏙️" };
    if (population >= 5) return { type: "emoji", value: "🏢" };
    return { type: "image", value: './ia_assets/city.jpg' };
  }

  // Function to get terrain background URL based on type
  function getTerrainImageUrl(terrainType) {
    switch (terrainType) {
      case TERRAIN_TYPES.WATER: return './ia_assets/ura_tile.jpg';
      case TERRAIN_TYPES.NORMAL: return './ia_assets/belarra_tile.jpg';
      default: return null;
    }
  }

  // Keep original color function as fallback for terrains without images
  function getTerrainColor(terrainType) {
    switch (terrainType) {
      case TERRAIN_TYPES.WATER: return '#3399ff';
      case TERRAIN_TYPES.MINERAL: return '#cc9900';
      case TERRAIN_TYPES.NORMAL: return '#66cc66';
      default: return '#66cc66';
    }
  }

  // Update unit icon function to use images when available
  function getUnitImageUrl(unitType) {
    switch (unitType) {
      case "warrior": return './ia_assets/warrior.png';
      case "settler": return './ia_assets/settler.png';
      default: return null;
    }
  }

  function getUnitIcon(unitType) {
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

  // Add this new function to get resource icons based on terrain type
  function getResourceIcon(terrainType) {
    switch (terrainType) {
      case 2: return "🪙"; // Gold
      case 3: return "⚙️"; // Iron
      case 4: return "🌲"; // Wood
      case 5: return "🪨"; // Stone
      default: return null; // No resource
    }
  }

  // Get the terrain name with updated resource types
  function getTerrainName(terrainType) {
    switch (terrainType) {
      case TERRAIN_TYPES.WATER: return 'Agua';
      case 2: return 'Oro';
      case 3: return 'Hierro';
      case 4: return 'Madera';
      case 5: return 'Piedra';
      case TERRAIN_TYPES.NORMAL: return 'Tierra';
      default: return 'Desconocido';
    }
  }

  function toggleFogOfWar() {
    showFogOfWar = !showFogOfWar;
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

  function selectUnit(unit) {
    selectedUnit = unit;
    validMoveTargets = [];
    
    const totalMovement = unit.movement || 2;
    const remainingMovement = unit.remainingMovement !== undefined ? 
                              unit.remainingMovement : 
                              totalMovement;
    
    if (remainingMovement <= 0) {
      showToastNotification("Esta unidad ya ha agotado sus movimientos este turno.", "warning");
      selectedUnit = null;
      return;
    }
    
    const [unitX, unitY] = unit.position;
    calculateValidMoveTargets(unitX, unitY, remainingMovement);
  }
  
  function calculateValidMoveTargets(startX, startY, movementPoints) {
    validMoveTargets = [];
    const movementRange = 2;
    
    for (let y = Math.max(0, startY - movementRange); y <= Math.min(mapHeight - 1, startY + movementRange); y++) {
      for (let x = Math.max(0, startX - movementRange); x <= Math.min(mapWidth - 1, startX + movementRange); x++) {
        if (x === startX && y === startY) continue;
        const steps = Math.abs(x - startX) + Math.abs(y - startY);
        if (steps > movementRange) continue;
        if (terrain[y] && terrain[y][x] === TERRAIN_TYPES.WATER) continue;
        const occupyingUnit = units.find(u => 
          u !== selectedUnit && 
          u.position && 
          u.position[0] === x && 
          u.position[1] === y
        );
        if (occupyingUnit) continue;
        if (movementPoints >= 1) {
          validMoveTargets.push({ x, y, remainingMovement: movementPoints - 1 });
        }
      }
    }
  }
  
  async function moveUnitToPosition(unit, targetX, targetY) {
    if (movementInProgress) return;
    
    const occupyingUnit = units.find(u => u !== unit && u.position[0] === targetX && u.position[1] === targetY);
    if (occupyingUnit) {
      showToastNotification(`No puedes mover a la casilla (${targetX}, ${targetY}). Está ocupada por otra unidad.`, "error");
      movementInProgress = false;
      return;
    }

    movementInProgress = true;
    
    try {
      const targetInfo = validMoveTargets.find(target => 
        target.x === targetX && target.y === targetY
      );
      
      if (!targetInfo) {
        console.error("Target position not in valid moves");
        return;
      }
      
      const localUnitIndex = units.findIndex(u => u === unit);
      
      if (localUnitIndex !== -1) {
        const originalUnitPosition = [...units[localUnitIndex].position]; 
        const movementCost = 1;
        const totalMovement = units[localUnitIndex].movement || 2;
        
        if (units[localUnitIndex].remainingMovement === undefined) {
          units[localUnitIndex].remainingMovement = totalMovement;
        }
        
        if (movementCost > units[localUnitIndex].remainingMovement) {
          showToastNotification("Movimiento ilegal: no hay suficientes puntos de movimiento", "error");
          movementInProgress = false;
          return;
        }
        
        units[localUnitIndex].remainingMovement -= movementCost;
        units[localUnitIndex].position = [targetX, targetY];
        
        if (units[localUnitIndex].remainingMovement <= 0) {
          units[localUnitIndex].status = 'exhausted';
        } else {
          units[localUnitIndex].status = 'moved';
        }
        
        units = [...units]; 
        updateUnitInfoPanel(localUnitIndex);
        
        if (gameData && gameData.player && Array.isArray(gameData.player.units)) {
          let gameDataUnitIndex = -1;

          if (unit.id) { 
            gameDataUnitIndex = gameData.player.units.findIndex(u => u.id === unit.id);
          }
          
          if (gameDataUnitIndex === -1) {
            gameDataUnitIndex = gameData.player.units.findIndex(u =>
              u.type_id === unit.type_id && 
              u.position && Array.isArray(u.position) &&
              u.position[0] === originalUnitPosition[0] &&
              u.position[1] === originalUnitPosition[1]
            );
          }
          
          if (gameDataUnitIndex !== -1) {
            gameData.player.units[gameDataUnitIndex].position = [targetX, targetY];
            gameData.player.units[gameDataUnitIndex].status = units[localUnitIndex].status;
            gameData.player.units[gameDataUnitIndex].remainingMovement = units[localUnitIndex].remainingMovement;
            
            console.log(`Unit updated in gameData: ID ${unit.id || 'N/A'}, New Pos [${targetX},${targetY}], Status ${units[localUnitIndex].status}, Remaining Movement: ${units[localUnitIndex].remainingMovement}`);
          } else {
            console.warn("Moved unit not found in gameData.player.units. Session not updated for this unit.");
          }
        }
        
        updateFogOfWarAroundPosition(targetX, targetY, 2);
        
        if (units[localUnitIndex].remainingMovement <= 0) {
          selectedUnit = null;
          validMoveTargets = [];
        } else {
          selectUnit(units[localUnitIndex]);
        }
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

  function updateUnitInfoPanel(unitIndex) {
    if (selectedUnitInfo && units[unitIndex]) {
      if (selectedUnitInfo.id === units[unitIndex].id || 
         (selectedUnitInfo.position && units[unitIndex].position && 
          selectedUnitInfo.position[0] === units[unitIndex].position[0] && 
          selectedUnitInfo.position[1] === units[unitIndex].position[1])) {
        selectedUnitInfo = units[unitIndex];
      }
    }
  }

  function handleTileClick(x, y) {
    if (selectedUnit && validMoveTargets.some(target => target.x === x && target.y === y)) {
      moveUnitToPosition(selectedUnit, x, y);
      return;
    }
    
    // Check if there's a city at the clicked position
    const cityAtPosition = cities.find(city => 
      (city.position.x === x && city.position.y === y) || 
      (Array.isArray(city.position) && city.position[0] === x && city.position[1] === y)
    );
    
    if (cityAtPosition) {
      selectedCityInfo = cityAtPosition;
      selectedTile = null;
      selectedUnit = null;
      selectedUnitInfo = null;
      validMoveTargets = [];
      return;
    }
    
    const unitAtPosition = units.find(unit => 
      unit && 
      unit.position && 
      Array.isArray(unit.position) && 
      unit.position[0] === x && 
      unit.position[1] === y
    );
    
    if (unitAtPosition) {
      selectedCityInfo = null; // Clear selected city
      selectedUnitInfo = unitAtPosition;
      selectedTile = null;
      
      if (unitAtPosition.owner === 'ia') {
        showToastNotification("Esta es una unidad enemiga. No puedes controlarla.", "warning");
        selectedUnit = null;
        validMoveTargets = [];
        return;
      }
      
      if (unitAtPosition.status === 'exhausted') {
        showToastNotification("Esta unidad ya ha agotado sus movimientos este turno.", "warning");
        selectedUnit = null;
        validMoveTargets = [];
      } else {
        selectUnit(unitAtPosition);
      }
      return;
    } else {
      selectedUnit = null;
      selectedUnitInfo = null;
      selectedCityInfo = null; // Clear selected city
      validMoveTargets = [];
    }
    
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

  // Add function to enter city management screen
  function enterCity(city) {
    // Store the selected city ID in the game state or use a URL parameter
    if (gameData && city) {
      gameAPI.storeTemporaryData('selectedCityId', city.id);
      navigate('/city');
    }
  }

  async function endTurn() {
    if (!gameData) {
      console.error("Cannot end turn, game data is not loaded.");
      return;
    }

    console.log(`Player ${gameData.current_player} ending turn ${gameData.turn}.`);

    gameData.current_player = "ia";
    currentPlayer.set(gameData.current_player);
    showToastNotification("IA's Turn (Not Implemented - Placeholder)", "info");
    
    await new Promise(resolve => setTimeout(resolve, 1500));

    gameData.current_player = "player";
    gameData.turn = (gameData.turn || 0) + 1;
    currentPlayer.set(gameData.current_player);
    currentTurn.set(gameData.turn);

    const aiUnits = units.filter(unit => unit.owner === 'ia');

    if (gameData.player && Array.isArray(gameData.player.units)) {
      gameData.player.units.forEach((unit, index) => {
        unit.status = "ready";
        unit.remainingMovement = unit.movement || 2;
        
        if (selectedUnitInfo && selectedUnitInfo.id === unit.id) {
          selectedUnitInfo = unit;
        }
      });
      
      let updatedUnits = [...gameData.player.units];
      
      if (aiUnits.length > 0) {
        updatedUnits = [...updatedUnits, ...aiUnits];
      }
      
      units = updatedUnits;
      
      console.log("Units after turn end:", units.length, "- Player:", 
        units.filter(u => u.owner === 'player').length, 
        "AI:", units.filter(u => u.owner === 'ia').length);
    }
    
    selectedUnit = null;
    selectedUnitInfo = null;
    validMoveTargets = [];

    try {
      await gameAPI.updateGameSession(gameData);
      console.log(`Game session updated for Turn ${gameData.turn}.`);
      showToastNotification(`Turno ${gameData.turn} - Tu turno`, "success");
    } catch (error) {
      console.error("Failed to update game session after ending turn:", error);
      showToastNotification("Error saving turn data to server.", "error");
    }
  }

  async function saveAndExit() {
    try {
      if (gameData) {
        console.log("Updating game session before saving and exiting...");
        await gameAPI.updateGameSession(gameData);
        
        console.log("Requesting backend to save current game session to DB...");
        const saveResult = await gameAPI.saveCurrentGameSession();
        console.log("Save result:", saveResult);
        
        if (!saveResult || (saveResult.success === false)) {
          throw new Error(saveResult?.message || "Unknown error saving game");
        }
        
        console.log("Game saved and session persisted.");
        
        showToastNotification("Your game has been saved successfully!");
        
        setTimeout(() => {
          endGame();
          navigate('/home');
        }, 1500);
      } else {
        endGame();
        navigate('/home');
      }
    } catch (error) {
      console.error("Error saving and exiting game:", error);
      
      showToastNotification(`Error saving game: ${error.message}. Trying again...`, "error", 2000);
      
      try {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await gameAPI.saveCurrentGameSession();
        showToastNotification("Game saved successfully on retry!", "success");
        
        setTimeout(() => {
          endGame();
          navigate('/home');
        }, 1500);
      } catch (retryError) {
        showToastNotification(`Unable to save game. Exiting without saving.`, "error", 2000);
        setTimeout(() => {
          endGame();
          navigate('/home');
        }, 2000);
      }
    }
  }

  function exitWithoutSaving() {
    if (confirm("¿Estás seguro de que quieres salir sin guardar? Se perderá todo el progreso.")) {
      endGame();
      navigate('/home');
    }
  }

  onMount(async () => {
    try {
      document.body.classList.add('map-active');
      document.documentElement.classList.add('map-active');

      if (!$user) {
        navigate('/');
        return;
      }

      window.addEventListener('keydown', handleKeyPress);

      selectedMapId = $gameState?.currentScenario?.mapId;
      console.log("Selected map ID:", selectedMapId);

      await initializeGame();

      return () => {
        document.body.classList.remove('map-active');
        document.documentElement.classList.remove('map-active');
        window.removeEventListener('keydown', handleKeyPress);
      };
    } catch (err) {
      console.error("Error mounting Map component:", err);
      loadingError = err.message;
    }
  });

  onDestroy(() => {
    document.body.classList.remove('map-active');
    document.documentElement.classList.remove('map-active');
    window.removeEventListener('keydown', handleKeyPress);
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

      try {
        gameData = await gameAPI.getCurrentGame();
        console.log("Game data from session:", gameData);

        if (gameData) {
          console.log("Using game data from session");

          mapData = gameData.map_data || {};
          console.log("Map data from session game:", mapData);

          mapWidth = gameData.map_size?.width || mapData.width || 30;
          mapHeight = gameData.map_size?.height || mapData.height || 15;
          grid = mapData.grid || [];
          terrain = mapData.terrain || [];
          startPoint = mapData.startPoint || [15, 7];
          difficulty = gameData.difficulty || mapData.difficulty || "medium";

          currentTurn.set(gameData.turn || 1);
          currentPlayer.set(gameData.current_player || "player");

          units = [];
          if (gameData.player && Array.isArray(gameData.player.units)) {
            const playerUnits = gameData.player.units.map(unit => ({
              ...unit,
              owner: 'player'
            }));
            units = [...playerUnits];
            console.log("Player units loaded:", playerUnits.length);
          }
          
          if (gameData.ia && Array.isArray(gameData.ia.units)) {
            const aiUnits = gameData.ia.units.map(unit => ({
              ...unit,
              owner: 'ia'
            }));
            units = [...units, ...aiUnits];
            console.log("AI units loaded:", aiUnits.length);
          }
          
          console.log("Total units loaded:", units.length);

          if (gameData && gameData.player && Array.isArray(gameData.player.cities)) {
            cities = [...gameData.player.cities];
            console.log("Loaded cities:", cities.length);
          } else {
            cities = [];
          }
        }
      } catch (apiError) {
        console.error("Error loading game/map:", apiError);
        mapWidth = 30;
        mapHeight = 15;
        initializeFogOfWar();
        initializeTerrain();
        units = [];
      }

      isLoading = false;

      setTimeout(centerMapOnStartPoint, 200);
    } catch (error) {
      loadingError = error.message || "Error desconocido al iniciar el juego.";
      isLoading = false;
    }
  }

  function initializeFogOfWar() {
    grid = Array(mapHeight).fill().map(() => Array(mapWidth).fill(FOG_OF_WAR.HIDDEN));

    if (startPoint && startPoint.length === 2) {
      const [startX, startY] = startPoint;
      const visibilityRadius = 3;

      for (let y = Math.max(0, startY - visibilityRadius); y <= Math.min(mapHeight - 1, startY + visibilityRadius); y++) {
        for (let x = Math.max(0, startX - visibilityRadius); x <= Math.min(mapWidth - 1, startX + visibilityRadius); x++) {
          const distance = Math.sqrt(Math.pow(x - startX, 2) + Math.pow(y - startY, 2));
          if (distance <= visibilityRadius) {
            grid[y][x] = FOG_OF_WAR.VISIBLE;
          }
        }
      }
    }
  }

  function initializeTerrain() {
    terrain = Array(mapHeight).fill().map(() => Array(mapWidth).fill(TERRAIN_TYPES.NORMAL));

    for (let y = 0; y < mapHeight; y++) {
      for (let x = 0; x < mapWidth; x++) {
        const rnd = Math.random();

        if (rnd < 0.15) {
          terrain[y][x] = TERRAIN_TYPES.WATER;
        } else if (rnd < 0.25) {
          terrain[y][x] = TERRAIN_TYPES.MINERAL;
        } else {
          terrain[y][x] = TERRAIN_TYPES.NORMAL;
        }
      }
    }

    if (startPoint && startPoint.length === 2) {
      const [startX, startY] = startPoint;
      if (startX >= 0 && startX < mapWidth && startY >= 0 && startY < mapHeight) {
        terrain[startY][startX] = TERRAIN_TYPES.NORMAL;

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

  function centerMapOnStartPoint() {
    if (startPoint && startPoint.length === 2) {
      const [startX, startY] = startPoint;
      const containerWidth = window.innerWidth;
      const containerHeight = window.innerHeight;

      offsetX = (containerWidth / 2) - (startX * tileSize * zoomLevel);
      offsetY = (containerHeight / 2) - (startY * tileSize * zoomLevel);
    }
  }

  function updateFogOfWarAroundPosition(centerX, centerY, radius) {
    if (!showFogOfWar) return;
    
    for (let y = Math.max(0, centerY - radius); y <= Math.min(mapHeight - 1, centerY + radius); y++) {
      for (let x = Math.max(0, centerX - radius); x <= Math.min(mapWidth - 1, centerX + radius); x++) {
        const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));
        if (distance <= radius && grid[y] && grid[y][x] !== undefined) {
          grid[y][x] = FOG_OF_WAR.VISIBLE;
        }
      }
    }
    grid = [...grid];
  }
</script>

<svelte:head>
  <title>Map - Civilization Game</title>
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
        <span class="game-info">
          Turno: {$currentTurn} | Jugador: {$currentPlayer} | Mapa: {mapWidth}x{mapHeight} | Dificultad: {difficulty}
        </span>
      </div>
      <div class="right-controls">
        <button class="end-turn-button" on:click={endTurn} title="Finalizar Turno">
          Terminar Turno
        </button>
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
            {@const terrainImageUrl = isVisible ? getTerrainImageUrl(terrainType) : null}
            {@const hasResource = isVisible && (terrainType === 2 || terrainType === 3 || terrainType === 4 || terrainType === 5)}
            
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
                background-color: {isVisible && !terrainImageUrl ? 
                                 (hasResource ? getTerrainColor(TERRAIN_TYPES.NORMAL) : getTerrainColor(terrainType)) : 
                                 '#000'};
                background-image: {terrainImageUrl && !hasResource ? 
                                 `url('${terrainImageUrl}')` : 
                                 (hasResource ? `url('./ia_assets/belarra_tile.jpg')` : 'none')};
                background-size: cover;
              "
              on:click={() => handleTileClick(x, y)}
              class:selected={selectedTile && selectedTile.x === x && selectedTile.y === y}
            >
              {#if x % 10 === 0 && y % 10 === 0 && isVisible}
                <div class="coord-marker">{x},{y}</div>
              {/if}
              
              {#if hasResource && isVisible}
                <div class="resource-marker" title="{getTerrainName(terrainType)}">
                  <span class="resource-icon">{getResourceIcon(terrainType)}</span>
                </div>
              {/if}
              
              {#each cities as city}
                {#if (city.position.x === x && city.position.y === y) || 
                     (Array.isArray(city.position) && city.position[0] === x && city.position[1] === y)}
                  <div 
                    class="city-marker" 
                    title="{city.name} (Población: {city.population || 0})"
                  >
                    <span class="city-icon">
                      {#if getCityIcon(city).type === "emoji"}
                        {getCityIcon(city).value}
                      {:else}
                        <img src={getCityIcon(city).value} alt="City" class="city-image" />
                      {/if}
                    </span>
                  </div>
                {/if}
              {/each}
              
              {#if unitAtPosition && isVisible}
                <div 
                  class="unit-marker" 
                  class:selected={isSelectedUnit}
                  class:exhausted={unitAtPosition.status === 'exhausted'}
                  class:enemy={unitAtPosition.owner === 'ia'}
                  title="{unitAtPosition.name || unitAtPosition.type_id} {unitAtPosition.owner === 'ia' ? '(Enemy)' : ''} {unitAtPosition.status ? '(' + unitAtPosition.status + ')' : ''}"
                >
                  {#if getUnitImageUrl(unitAtPosition.type_id)}
                    <img 
                      src={getUnitImageUrl(unitAtPosition.type_id)} 
                      alt={unitAtPosition.type_id} 
                      class="unit-image"
                    />
                  {:else}
                    <span class="unit-icon">{getUnitIcon(unitAtPosition.type_id)}</span>
                  {/if}
                </div>
              {/if}
            </div>
          {/each}
        {/each}
      </div>
    </div>
    
    {#if selectedTile && !showPauseMenu && !selectedUnitInfo && !selectedCityInfo}
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
    
    {#if selectedUnitInfo && !showPauseMenu}
      <div class="unit-info-overlay">
        <div class="unit-info-card" class:enemy-unit={selectedUnitInfo.owner === 'ia'}>
          <div class="unit-info-header">
            <h4>{selectedUnitInfo.name || selectedUnitInfo.type_id || 'Unidad'}</h4>
            <button class="close-button" on:click={() => { selectedUnitInfo = null; }}>×</button>
          </div>
          
          <div class="unit-details">
            <div class="unit-image-container">
              {#if selectedUnitInfo.type_id && getUnitImageUrl(selectedUnitInfo.type_id)}
                <img src={getUnitImageUrl(selectedUnitInfo.type_id)} alt={selectedUnitInfo.type_id} class="unit-portrait" />
              {:else}
                <div class="unit-icon-large">{selectedUnitInfo.type_id ? getUnitIcon(selectedUnitInfo.type_id) : '❓'}</div>
              {/if}
            </div>
            
            <div class="unit-stats">
              <p><strong>Tipo:</strong> {selectedUnitInfo.type_id || 'Desconocido'}</p>
              <p><strong>Facción:</strong> {selectedUnitInfo.owner === 'ia' ? 'Enemigo' : 'Jugador'}</p>
              <p><strong>Estado:</strong> {selectedUnitInfo.status || 'ready'}</p>
              <p><strong>Movimientos:</strong> {selectedUnitInfo.remainingMovement !== undefined ? selectedUnitInfo.remainingMovement : (selectedUnitInfo.movement || 2)}/{selectedUnitInfo.movement || 2}</p>
              {#if selectedUnitInfo.position && Array.isArray(selectedUnitInfo.position) && selectedUnitInfo.position.length >= 2}
                <p><strong>Posición:</strong> [{selectedUnitInfo.position[0]}, {selectedUnitInfo.position[1]}]</p>
              {/if}
              
              {#if selectedUnitInfo.health !== undefined}
                <p><strong>Salud:</strong> {selectedUnitInfo.health}</p>
              {/if}
              
              {#if selectedUnitInfo.attack !== undefined}
                <p><strong>Ataque:</strong> {selectedUnitInfo.attack}</p>
              {/if}
              
              {#if selectedUnitInfo.defense !== undefined}
                <p><strong>Defensa:</strong> {selectedUnitInfo.defense}</p>
              {/if}
            </div>
          </div>
          
          {#if selectedUnitInfo.owner !== 'ia' && selectedUnitInfo.status !== 'exhausted'}
            <div class="unit-actions">
              <button class="action-button" on:click={() => selectUnit(selectedUnitInfo)}>Mover</button>
              
              {#if selectedUnitInfo.type_id === 'settler'}
                <button class="action-button found-city-button" on:click={() => showFoundCityDialog(selectedUnitInfo)}>
                  Fundar Ciudad
                </button>
              {/if}
            </div>
          {:else if selectedUnitInfo.owner === 'ia'}
            <div class="unit-enemy-message">
              <p>Esta es una unidad enemiga. No puedes controlarla.</p>
            </div>
          {:else}
            <div class="unit-exhausted-message">
              <p>Esta unidad ya ha agotado sus movimientos este turno.</p>
            </div>
          {/if}
        </div>
      </div>
    {/if}
    
    {#if selectedCityInfo && !showPauseMenu}
      <div class="city-info-overlay">
        <div class="city-info-card">
          <div class="city-info-header">
            <h4>{selectedCityInfo.name || 'Ciudad'}</h4>
            <button class="close-button" on:click={() => { selectedCityInfo = null; }}>×</button>
          </div>
          
          <div class="city-details">
            <div class="city-image-container">
              <div class="city-icon-large">
                {#if getCityIcon(selectedCityInfo).type === "emoji"}
                  {getCityIcon(selectedCityInfo).value}
                {:else}
                  <img src={getCityIcon(selectedCityInfo).value} alt="City" class="city-portrait" />
                {/if}
              </div>
            </div>
            
            <div class="city-stats">
              <p><strong>Población:</strong> {selectedCityInfo.population || 0}</p>
              {#if selectedCityInfo.position}
                <p><strong>Posición:</strong> {Array.isArray(selectedCityInfo.position) ? 
                  `[${selectedCityInfo.position[0]}, ${selectedCityInfo.position[1]}]` : 
                  `[${selectedCityInfo.position.x}, ${selectedCityInfo.position.y}]`}</p>
              {/if}
              
              {#if selectedCityInfo.buildings && selectedCityInfo.buildings.length > 0}
                <p><strong>Edificios:</strong> {selectedCityInfo.buildings.length}</p>
              {/if}
              
              {#if selectedCityInfo.production && selectedCityInfo.production.current_item}
                <p><strong>Producción actual:</strong> {selectedCityInfo.production.current_item}</p>
                <p><strong>Turnos restantes:</strong> {selectedCityInfo.production.turns_remaining}</p>
              {/if}
            </div>
          </div>
          
          <div class="city-actions">
            <button class="action-button enter-city-button" on:click={() => enterCity(selectedCityInfo)}>
              Entrar a la Ciudad
            </button>
          </div>
        </div>
      </div>
    {/if}
    
    {#if showCityFoundingModal}
      <div class="modal-overlay">
        <div class="modal-content">
          <h3>Fundar Nueva Ciudad</h3>
          <p>Vas a fundar una nueva ciudad en la posición [{settlerToFoundCity?.position[0] || 0}, {settlerToFoundCity?.position[1] || 0}].</p>
          
          <div class="form-group">
            <label for="city-name">Nombre de la Ciudad:</label>
            <input 
              type="text" 
              id="city-name" 
              bind:value={newCityName} 
              placeholder="Introduce un nombre para tu ciudad"
            />
          </div>
          
          <div class="resource-requirements">
            <h4>Recursos necesarios:</h4>
            <div class="resource food">
              <div class="resource-icon">🌾</div>
              <div class="resource-value">100</div>
            </div>
            <div class="resource gold">
              <div class="resource-icon">💰</div>
              <div class="resource-value">50</div>
            </div>
          </div>
          
          <div class="modal-actions">
            <button class="cancel-button" on:click={cancelCityFounding}>Cancelar</button>
            <button class="confirm-button" on:click={foundCity}>Fundar Ciudad</button>
          </div>
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

  <!-- Add resources bar at the bottom of the screen -->
  {#if !isLoading && !loadingError && gameData && gameData.player && gameData.player.resources}
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
      <!-- Add iron resource -->
      <div class="resource iron">
        <div class="resource-icon">⚙️</div>
        <div class="resource-value">{gameData.player.resources.iron || 0}</div>
      </div>
      <!-- Add stone resource -->
      <div class="resource stone">
        <div class="resource-icon">🪨</div>
        <div class="resource-value">{gameData.player.resources.stone || 0}</div>
      </div>
    </div>
  {/if}

  {#if showToast}
    <div class="toast-container">
      <div class="toast-notification {toastType}">
        <span class="toast-message">{toastMessage}</span>
      </div>
    </div>
  {/if}
</div>

<style>
  /* ...existing styles... */
  
  .city-image {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }
</style>

