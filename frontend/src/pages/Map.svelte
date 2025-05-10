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

  // Function to show a toast notification
  function showToastNotification(message, type = "success", duration = 3000) {
    // Clear any existing timeout to prevent multiple toasts
    if (toastTimeout) clearTimeout(toastTimeout);
    
    // Set toast properties
    toastMessage = message;
    toastType = type;
    showToast = true;
    
    // Hide toast after duration
    toastTimeout = setTimeout(() => {
      showToast = false;
    }, duration);
  }

  // Function to get terrain background URL based on type
  function getTerrainImageUrl(terrainType) {
    switch (terrainType) {
      case TERRAIN_TYPES.WATER: return './ia_assets/ura_tile.jpg'; // Try with ./ prefix
      case TERRAIN_TYPES.NORMAL: return './ia_assets/belarra_tile.jpg'; // Try with ./ prefix
      default: return null; // For other types, we'll fall back to color
    }
  }

  // Keep original color function as fallback for terrains without images
  function getTerrainColor(terrainType) {
    switch (terrainType) {
      case TERRAIN_TYPES.WATER: return '#3399ff'; // Azul para agua
      case TERRAIN_TYPES.MINERAL: return '#cc9900'; // Dorado para minerales
      case TERRAIN_TYPES.NORMAL: return '#66cc66'; // Verde para tierra normal
      default: return '#66cc66'; // Verde por defecto
    }
  }

  // Update unit icon function to use images when available
  function getUnitImageUrl(unitType) {
    switch (unitType) {
      case "warrior": return './ia_assets/warrior.png'; // Updated to match format
      case "settler": return './ia_assets/settler.png'; // Updated to match format
      default: return null; // For other unit types, we'll fall back to emoji
    }
  }

  function getUnitIcon(unitType) {
    // Return an appropriate icon for each unit type as fallback
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
      case 5: return "🪨"; // Stone (new)
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

  onMount(async () => {
    try {
      // Add map-active class to body when map is mounted
      document.body.classList.add('map-active');
      document.documentElement.classList.add('map-active');

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

      // Inicializar el juego. This function will set gameData, 
      // and from it, the currentTurn and currentPlayer Svelte stores.
      await initializeGame();

      return () => {
        // Remove map-active class when map is unmounted
        document.body.classList.remove('map-active');
        document.documentElement.classList.remove('map-active');
        window.removeEventListener('keydown', handleKeyPress);
      };
    } catch (err) {
      console.error("Error mounting Map component:", err);
      loadingError = err.message;
    }
  });
  
  // Add explicit onDestroy to ensure cleanup happens
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

          // Initialize turn and player Svelte stores from loaded gameData
          currentTurn.set(gameData.turn || 1);
          currentPlayer.set(gameData.current_player || "player");

          // Load both player and AI units
          units = [];
          if (gameData.player && Array.isArray(gameData.player.units)) {
            // Add player's units with owner property
            const playerUnits = gameData.player.units.map(unit => ({
              ...unit,
              owner: 'player'
            }));
            units = [...playerUnits];
            console.log("Player units loaded:", playerUnits.length);
          }
          
          // Add AI units if they exist
          if (gameData.ia && Array.isArray(gameData.ia.units)) {
            const aiUnits = gameData.ia.units.map(unit => ({
              ...unit,
              owner: 'ia'
            }));
            units = [...units, ...aiUnits];
            console.log("AI units loaded:", aiUnits.length);
          }
          
          console.log("Total units loaded:", units.length);
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

            // Initialize gameData structure for a new game
            gameData = {
              name: "New Game",
              difficulty: difficulty,
              turn: 1, // Source of truth for turn number
              current_player: "player", // Source of truth for current player
              map_id: selectedMapId || mapData.map_id || mapData._id,
              map_size: { width: mapWidth, height: mapHeight },
              map_data: mapData,
              player: {
                units: [],
                cities: [],
                resources: { food: 100, gold: 50, wood: 20 } 
              },
              ia: { units: [], cities: [] },
              created_at: new Date().toISOString(),
              last_saved: new Date().toISOString()
            };

            // Set Svelte stores from the newly initialized gameData
            currentTurn.set(gameData.turn);
            currentPlayer.set(gameData.current_player);

            // If starting units are defined (e.g. settler, warrior at startPoint)
            const settlerType = { type_id: "settler", movement: 2, name: "Settler" }; // Example
            const warriorType = { type_id: "warrior", movement: 2, name: "Warrior" }; // Example
            
            let initialUnits = [];
            if (startPoint) {
                const settler = { ...settlerType, id: `settler-${Date.now()}`, position: [...startPoint], status: 'ready', owner: 'player' };
                initialUnits.push(settler);

                let warriorPos = [...startPoint];
                if (startPoint[0] + 1 < mapWidth) warriorPos[0] += 1;
                else if (startPoint[1] + 1 < mapHeight) warriorPos[1] += 1;
                else if (startPoint[0] - 1 >= 0) warriorPos[0] -= 1;
                else warriorPos[1] -=1; // Basic placement

                const warrior = { ...warriorType, id: `warrior-${Date.now()}`, position: warriorPos, status: 'ready', owner: 'player' };
                initialUnits.push(warrior);
            }
            gameData.player.units = initialUnits;
            units = [...initialUnits]; // Sync local units
            
            // EXAMPLE: Add AI units for testing (in a real game, the backend would provide these)
            if (!gameData.ia) {
              gameData.ia = { units: [], cities: [] };
            }
            // Add an example AI warrior at a distance from the player's start point
            let aiStartX = startPoint[0] + 5;
            let aiStartY = startPoint[1] + 5;
            if (aiStartX >= mapWidth) aiStartX = mapWidth - 2;
            if (aiStartY >= mapHeight) aiStartY = mapHeight - 2;
            
            const aiWarrior = { 
              ...warriorType, 
              id: `ai-warrior-${Date.now()}`, 
              position: [aiStartX, aiStartY], 
              status: 'ready', 
              owner: 'ia' 
            };
            gameData.ia.units = [aiWarrior];
            units = [...units, ...gameData.ia.units]; // Add AI units to local units array
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

  // Select a unit and calculate its possible move targets
  function selectUnit(unit) {
    selectedUnit = unit;
    validMoveTargets = [];
    
    // Get unit's available movement points, accounting for already used movement
    const totalMovement = unit.movement || 2;
    const remainingMovement = unit.remainingMovement !== undefined ? 
                              unit.remainingMovement : 
                              totalMovement;
    
    if (remainingMovement <= 0) {
      showToastNotification("Esta unidad ya ha agotado sus movimientos este turno.", "warning");
      selectedUnit = null;
      return;
    }
    
    // Get current position
    const [unitX, unitY] = unit.position;
    
    // Calculate valid targets based on remaining movement
    calculateValidMoveTargets(unitX, unitY, remainingMovement);
  }
  
  // Calculate valid movement targets based on unit's position and movement points
  function calculateValidMoveTargets(startX, startY, movementPoints) {
    validMoveTargets = [];
    
    // Set a consistent movement range of 2 tiles in all directions
    const movementRange = 2;
    
    // Check all tiles within our fixed movement range
    for (let y = Math.max(0, startY - movementRange); y <= Math.min(mapHeight - 1, startY + movementRange); y++) {
      for (let x = Math.max(0, startX - movementRange); x <= Math.min(mapWidth - 1, startX + movementRange); x++) {
        // Skip the starting position
        if (x === startX && y === startY) continue;
        
        // Calculate Manhattan distance (steps needed) to reach this tile
        const steps = Math.abs(x - startX) + Math.abs(y - startY);
        
        // Skip if beyond our movement range
        if (steps > movementRange) continue;
        
        // Skip if this is water terrain (units can't move on water)
        if (terrain[y] && terrain[y][x] === TERRAIN_TYPES.WATER) continue;
        
        // Check if another unit occupies this tile
        const occupyingUnit = units.find(u => 
          u !== selectedUnit && 
          u.position && 
          u.position[0] === x && 
          u.position[1] === y
        );
        
        if (occupyingUnit) continue; // Tile is occupied by another unit
        
        // Add to valid targets if the unit has at least 1 movement point left
        if (movementPoints >= 1) {
          validMoveTargets.push({ x, y, remainingMovement: movementPoints - 1 });
        }
      }
    }
  }
  
  // Move the selected unit to a target position
  async function moveUnitToPosition(unit, targetX, targetY) {
    if (movementInProgress) return;
    
    // Check if the target tile is occupied by another unit
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
        
        // CHANGED: Each position change costs 1 movement point regardless of distance
        const movementCost = 1;
        
        // Get total movement allowance for this unit
        const totalMovement = units[localUnitIndex].movement || 2;
        
        // Initialize remainingMovement if not present
        if (units[localUnitIndex].remainingMovement === undefined) {
          units[localUnitIndex].remainingMovement = totalMovement;
        }
        
        // Ensure we can't move more than we have movement points for
        if (movementCost > units[localUnitIndex].remainingMovement) {
          showToastNotification("Movimiento ilegal: no hay suficientes puntos de movimiento", "error");
          movementInProgress = false;
          return;
        }
        
        // Deduct the cost of this move from remaining movement
        units[localUnitIndex].remainingMovement -= movementCost;
        
        // Update position
        units[localUnitIndex].position = [targetX, targetY];
        
        // Update status based on remaining movement
        if (units[localUnitIndex].remainingMovement <= 0) {
          units[localUnitIndex].status = 'exhausted';
        } else {
          units[localUnitIndex].status = 'moved';
        }
        
        // Force Svelte to update by creating a new array reference
        units = [...units]; 
        
        // NEW: Update the selected unit info to reflect the changes
        updateUnitInfoPanel(localUnitIndex);
        
        // Also update the game data for session persistence
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
        
        // If the unit still has movement points, don't deselect it to allow chains of movement
        if (units[localUnitIndex].remainingMovement <= 0) {
          selectedUnit = null;
          validMoveTargets = [];
        } else {
          // Reselect the unit to update valid moves from the new position
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

  // NEW: Function to update the unit info panel when unit data changes
  function updateUnitInfoPanel(unitIndex) {
    if (selectedUnitInfo && units[unitIndex]) {
      // Check if the current selectedUnitInfo matches the unit being updated
      if (selectedUnitInfo.id === units[unitIndex].id || 
         (selectedUnitInfo.position && units[unitIndex].position && 
          selectedUnitInfo.position[0] === units[unitIndex].position[0] && 
          selectedUnitInfo.position[1] === units[unitIndex].position[1])) {
        // Update the selectedUnitInfo reference to point to the updated unit
        selectedUnitInfo = units[unitIndex];
      }
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

  async function endTurn() {
    if (!gameData) {
      console.error("Cannot end turn, game data is not loaded.");
      return;
    }

    console.log(`Player ${gameData.current_player} ending turn ${gameData.turn}.`);

    // AI's turn (placeholder)
    gameData.current_player = "ia";
    currentPlayer.set(gameData.current_player); // Update Svelte store from gameData
    showToastNotification("IA's Turn (Not Implemented - Placeholder)", "info");
    
    // Short delay before continuing to next player turn
    await new Promise(resolve => setTimeout(resolve, 1500));

    // Switch back to player and increment turn
    gameData.current_player = "player";
    gameData.turn = (gameData.turn || 0) + 1;
    currentPlayer.set(gameData.current_player); // Update Svelte store from gameData
    currentTurn.set(gameData.turn); // Update Svelte store from gameData

    // Save current AI units before updating the units array
    const aiUnits = units.filter(unit => unit.owner === 'ia');

    // Reset player unit statuses and movement points
    if (gameData.player && Array.isArray(gameData.player.units)) {
      gameData.player.units.forEach((unit, index) => {
        unit.status = "ready"; // Reset status
        unit.remainingMovement = unit.movement || 2; // Reset movement points to full
        
        // Update the info panel if this is the currently selected unit
        if (selectedUnitInfo && selectedUnitInfo.id === unit.id) {
          selectedUnitInfo = unit; // Update reference to show refreshed stats
        }
      });
      
      // Update the local 'units' array with BOTH player AND AI units
      // First add the player units with refreshed status
      let updatedUnits = [...gameData.player.units];
      
      // Then add the AI units back
      if (aiUnits.length > 0) {
        updatedUnits = [...updatedUnits, ...aiUnits];
      }
      
      // Update the units array
      units = updatedUnits;
      
      console.log("Units after turn end:", units.length, "- Player:", 
        units.filter(u => u.owner === 'player').length, 
        "AI:", units.filter(u => u.owner === 'ia').length);
    }
    
    // Deselect any selected unit
    selectedUnit = null;
    selectedUnitInfo = null;
    validMoveTargets = [];

    // Save the updated game state to the session
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
        // Step 1: Ensure the latest gameData (with all local changes) is in the backend session
        console.log("Updating game session before saving and exiting...");
        await gameAPI.updateGameSession(gameData);
        
        // Step 2: Tell the backend to persist the session's game to the database
        console.log("Requesting backend to save current game session to DB...");
        const saveResult = await gameAPI.saveCurrentGameSession();
        console.log("Save result:", saveResult);
        
        if (!saveResult || (saveResult.success === false)) {
          throw new Error(saveResult?.message || "Unknown error saving game");
        }
        
        console.log("Game saved and session persisted.");
        
        // Replace alert with toast notification
        showToastNotification("Your game has been saved successfully!");
        
        // Short delay before navigating to give users a chance to see the notification
        setTimeout(() => {
          endGame(); // This should clear local stores (like $gameState)
          navigate('/home');
        }, 1500);
      } else {
        endGame();
        navigate('/home');
      }
    } catch (error) {
      console.error("Error saving and exiting game:", error);
      
      // Show error toast instead of confirm dialog
      showToastNotification(`Error saving game: ${error.message}. Trying again...`, "error", 2000);
      
      // Automatic retry without requiring user interaction
      try {
        // Wait a moment before retrying
        await new Promise(resolve => setTimeout(resolve, 1000));
        // One more attempt directly
        await gameAPI.saveCurrentGameSession();
        showToastNotification("Game saved successfully on retry!", "success");
        
        // Short delay before navigating
        setTimeout(() => {
          endGame();
          navigate('/home');
        }, 1500);
      } catch (retryError) {
        showToastNotification(`Unable to save game. Exiting without saving.`, "error", 2000);
        // Short delay before navigating
        setTimeout(() => {
          endGame();
          navigate('/home');
        }, 2000);
      }
    }
  }

  // Improved handleTileClick to better handle unit selection
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
    
    // If we found a unit, store its info and check if it's a player unit
    if (unitAtPosition) {
      // Set selected unit info for display regardless of owner
      selectedUnitInfo = unitAtPosition;
      selectedTile = null; // Clear tile selection when unit is selected
      
      // Only allow player units to be selected for movement
      if (unitAtPosition.owner === 'ia') {
        showToastNotification("Esta es una unidad enemiga. No puedes controlarla.", "warning");
        selectedUnit = null;
        validMoveTargets = [];
        return;
      }
      
      if (unitAtPosition.status === 'exhausted') {
        // If unit is exhausted, show a message
        showToastNotification("Esta unidad ya ha agotado sus movimientos este turno.", "warning");
        selectedUnit = null;
        validMoveTargets = [];
      } else {
        // Otherwise select it for movement
        selectUnit(unitAtPosition);
      }
      return;
    } else {
      // No unit found, clear unit selection and info
      selectedUnit = null;
      selectedUnitInfo = null;
      validMoveTargets = [];
    }
    
    // Handle regular tile info display (original behavior)
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

  function exitWithoutSaving() {
    if (confirm("¿Estás seguro de que quieres salir sin guardar? Se perderá todo el progreso.")) {
      endGame();
      navigate('/home');
    }
  }
</script>

<svelte:head>
  <!-- This was empty but needs to contain styles -->
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
              
              <!-- Add resource marker if the tile has a resource -->
              {#if hasResource && isVisible}
                <div class="resource-marker" title="{getTerrainName(terrainType)}">
                  <span class="resource-icon">{getResourceIcon(terrainType)}</span>
                </div>
              {/if}
              
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
    
    {#if selectedTile && !showPauseMenu && !selectedUnitInfo}
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
