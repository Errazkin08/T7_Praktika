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

  // Add AI turn visualization variables
  let processingAITurn = false;
  let aiActions = [];
  let currentAIAction = null;
  let aiActionIndex = 0;
  let showAIActionCard = false;
  let aiActionDescription = "";
  let aiTurnReasoning = "";

  // Add this new state variables for unit placement
  let newlyProducedUnit = null;
  let awaitingUnitPlacement = false;
  let producingCity = null;

  // Add this new state variable to track city area tiles
  let cityAreaTiles = [];

  // Keep the debug variable
  let debugAIMovement = true; // Enable debugging

  // Add enemy detection state
  let nearbyEnemies = [];
  let showAttackOptions = false;
  let attackTargets = [];
  let attackingUnit = null;

  // Function to show a toast notification
  function showToastNotification(message, type = "success", duration = 3000) {
    if (toastTimeout) clearTimeout(toastTimeout);
    toastMessage = message;
    toastType = type;
    showToast = true;
    
    console.log(`[TOAST] ${type}: ${message}`);
    
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
        area: 5,
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

  function checkForAttackTargets(unit) {
    if (!unit || unit.owner !== 'player' || unit.status === 'exhausted') {
      attackTargets = [];
      return;
    }
    
    attackTargets = [];
    attackingUnit = unit;
    
    // Get unit position
    const [unitX, unitY] = unit.position;
    
    // Check for enemies within attack range (default is 3 tiles for all units)
    let attackRange = 3;
    
    // Check each potential target within range
    for (let y = Math.max(0, unitY - attackRange); y <= Math.min(mapHeight - 1, unitY + attackRange); y++) {
      for (let x = Math.max(0, unitX - attackRange); x <= Math.min(mapWidth - 1, unitX + attackRange); x++) {
        // Skip water tiles
        if (terrain[y] && terrain[y][x] === TERRAIN_TYPES.WATER) continue;
        
        // Skip the current tile
        if (x === unitX && y === unitY) continue;
        
        // Check if this tile is visible (not in fog of war)
        // If fog of war is enabled, we can only attack visible enemies
        if (showFogOfWar && (!grid[y] || grid[y][x] !== FOG_OF_WAR.VISIBLE)) {
          continue; // Skip tiles that are in the fog of war
        }
        
        // Calculate Manhattan distance (number of steps)
        const manhattanDistance = Math.abs(x - unitX) + Math.abs(y - unitY);
        
        // If beyond attack range, skip
        if (manhattanDistance > attackRange) continue;
        
        // Check if there's an enemy unit at this position
        const enemyUnit = units.find(u => 
          u.owner === 'ia' && 
          u.position && 
          Array.isArray(u.position) && 
          u.position[0] === x && 
          u.position[1] === y
        );
        
        if (enemyUnit) {
          console.log(`Found enemy target at [${x},${y}]: ${enemyUnit.type_id}`);
          attackTargets.push(enemyUnit);
        }
      }
    }
    
    console.log(`Found ${attackTargets.length} potential attack targets`);
    showAttackOptions = attackTargets.length > 0;
    
    // If we have attack targets, show a notification
    if (attackTargets.length > 0) {
      showToastNotification(`${attackTargets.length} unidades enemigas al alcance`, "info", 2000);
    }
  }

  function canAttack(unit) {
    if (!unit || unit.owner !== 'player' || unit.status === 'exhausted') {
      return false;
    }
    
    // Get unit position
    const [unitX, unitY] = unit.position;
    
    // Check for enemies within attack range (3 tiles)
    const attackRange = 3;
    
    // Quick check for nearby enemies
    for (const enemy of units) {
      if (enemy.owner !== 'ia' || !enemy.position || !Array.isArray(enemy.position)) continue;
      
      const [enemyX, enemyY] = enemy.position;
      
      // Calculate Manhattan distance (number of steps)
      const manhattanDistance = Math.abs(enemyX - unitX) + Math.abs(enemyY - unitY);
      
      // Check if the enemy is within attack range
      if (manhattanDistance <= attackRange) {
        // Check if enemy is visible (not in fog of war)
        if (showFogOfWar) {
          if (grid[enemyY] && grid[enemyY][enemyX] === FOG_OF_WAR.VISIBLE) {
            return true;
          }
        } else {
          // If fog of war is disabled, all enemies in range can be attacked
          return true;
        }
      }
    }
    
    return false;
  }

  function initiateAttack(defender) {
    if (!attackingUnit || !defender) return;
    
    // Make a copy of the attacking unit to avoid reference issues
    const attackerCopy = { ...attackingUnit };
    const defenderCopy = { ...defender };
    
    // Make sure health is a number
    attackerCopy.health = attackerCopy.health || 100;
    defenderCopy.health = defenderCopy.health || 100;
    
    // Set up battle data
    const battleData = {
      attacker: attackerCopy,
      defender: defenderCopy,
      gameData: gameData
    };
    
    // Store battle data for the battle page
    gameAPI.storeTemporaryData('battleData', battleData);
    
    // Navigate to battle page
    navigate('/battle');
  }

  async function processAIActions(actions, reasoning) {
    if (!actions || actions.length === 0) return;
    
    processingAITurn = true;
    aiActions = actions;
    aiActionIndex = 0;
    aiTurnReasoning = reasoning || "La IA está realizando movimientos estratégicos";
    
    showToastNotification("Observando el turno de la IA...", "info", 2000);
    
    // Save current fog of war state and disable it for AI turn
    const previousFogState = showFogOfWar;
    showFogOfWar = false;
    
    // Save current zoom level to restore later
    const previousZoomLevel = zoomLevel;
    // Set a fixed zoom level for better visibility of AI actions
    zoomLevel = 1.5;
    
    // Ensure AI units exist in the units array
    ensureAIUnitsExist();
    
    console.log(`Processing ${actions.length} AI actions`);
    
    for (let i = 0; i < aiActions.length; i++) {
      aiActionIndex = i;
      currentAIAction = aiActions[i];
      
      console.log(`Processing AI action ${i+1}/${actions.length}:`, currentAIAction);
      
      // Center map on the action location
      if (currentAIAction.position && Array.isArray(currentAIAction.position)) {
        if (currentAIAction.type === "movement" && currentAIAction.target_position) {
          // For movement actions, center between positions
          const [startX, startY] = currentAIAction.position;
          const [endX, endY] = currentAIAction.target_position;
          
          // Calculate midpoint and force immediate camera update
          const midX = (startX + endX) / 2;
          const midY = (startY + endY) / 2;
          console.log(`Centering camera on movement midpoint: [${midX}, ${midY}]`);
          
          offsetX = (window.innerWidth / 2) - (midX * tileSize * zoomLevel);
          offsetY = (window.innerHeight / 2) - (midY * tileSize * zoomLevel);
        } else {
          // For other actions, center directly on position
          const [posX, posY] = currentAIAction.position;
          console.log(`Centering camera on position: [${posX}, ${posY}]`);
          
          offsetX = (window.innerWidth / 2) - (posX * tileSize * zoomLevel);
          offsetY = (window.innerHeight / 2) - (posY * tileSize * zoomLevel);
        }
        
        // Wait for camera to adjust
        await new Promise(resolve => setTimeout(resolve, 800));
      }
      
      // Display action card
      aiActionDescription = getActionDescription(currentAIAction);
      showAIActionCard = true;
      
      // Process action visually
      await visualizeAIAction(currentAIAction);
      
      // Keep card visible for a moment
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Hide card between actions
      showAIActionCard = false;
      await new Promise(resolve => setTimeout(resolve, 300));
    }
    
    // Update game state
    updateGameStateAfterAITurn();
    
    // Save changes to session
    try {
      await gameAPI.updateGameSession(gameData);
      console.log("AI turn changes saved to session");
    } catch (error) {
      console.error("Error saving AI turn changes:", error);
    }
    
    // Restore fog of war to previous state - IMPORTANT: Always ensure it's restored
    showFogOfWar = previousFogState; 
    
    // Find a player unit or city to center on
    await centerOnPlayerPosition();
    
    // Restore zoom level
    zoomLevel = previousZoomLevel;
    
    processingAITurn = false;
    currentAIAction = null;
    showToastNotification("La IA ha completado su turno", "success");
  }

  async function centerOnPlayerPosition() {
    let centerPosition = null;
    
    // First try to find the player's capital city
    const playerCity = cities.find(c => !c.owner || c.owner === 'player');
    if (playerCity) {
      if (Array.isArray(playerCity.position)) {
        centerPosition = playerCity.position;
      } else if (playerCity.position) {
        centerPosition = [playerCity.position.x, playerCity.position.y];
      }
    }
    
    // If no city found, try to find a player unit
    if (!centerPosition) {
      const playerUnit = units.find(u => u.owner === 'player');
      if (playerUnit && Array.isArray(playerUnit.position)) {
        centerPosition = playerUnit.position;
      }
    }
    
    // If no player units or cities, use the start point
    if (!centerPosition) {
      centerPosition = startPoint;
    }
    
    // Center map and wait for animation
    if (centerPosition) {
      centerMapOnPosition(centerPosition[0], centerPosition[1]);
      await new Promise(resolve => setTimeout(resolve, 800));
    }
  }

  async function visualizeAIAction(action) {
    try {
      switch (action.type) {
        case "movement": {
          // Find the unit to move - first try by ID, then by position if ID is missing
          let unitIndex = -1;
          
          if (action.unit_id) {
            // Find by ID if available
            unitIndex = units.findIndex(u => u.id === action.unit_id);
          }
          
          if (unitIndex === -1 && action.position && Array.isArray(action.position)) {
            // If not found by ID or ID is null/undefined, try by position
            const [posX, posY] = action.position;
            unitIndex = units.findIndex(u => 
              u.position && 
              Array.isArray(u.position) && 
              u.position[0] === posX && 
              u.position[1] === posY &&
              u.owner === 'ia'
            );
            
            // If found by position but unit has no ID, assign one
            if (unitIndex !== -1 && (!units[unitIndex].id || units[unitIndex].id === null)) {
              units[unitIndex].id = `unit-${posX}-${posY}`;
              console.log(`Assigned ID ${units[unitIndex].id} to unit at position [${posX},${posY}]`);
            }
          }
          
          if (unitIndex === -1) {
            console.warn(`Unit for movement not found: ${action.unit_id || JSON.stringify(action.position)}. Creating temporary unit for visualization.`);
            
            // Create a temporary unit if none exists
            const tempUnit = {
              id: action.unit_id || `unit-${action.position[0]}-${action.position[1]}`,
              position: [...action.position],
              type_id: action.unit_type || "warrior",
              owner: 'ia',
              status: 'ready',
              remainingMovement: 2
            };
            
            units = [...units, tempUnit];
            unitIndex = units.length - 1;
          }
          
          // Rest of the movement logic remains unchanged
          const unitToMove = units[unitIndex];
          
          // Check if target position is water (invalid move)
          const [targetX, targetY] = action.target_position;
          if (terrain[targetY] && terrain[targetY][targetX] === TERRAIN_TYPES.WATER) {
            console.warn(`AI attempted invalid move to water tile at [${targetX}, ${targetY}]. Movement ignored.`);
            break;
          }
          
          // Make unit visually active
          unitToMove.moving = true;
          units = [...units]; // Update reactivity
          
          // Wait for animation visibility
          await new Promise(resolve => setTimeout(resolve, 1200));
          
          // Move unit to target position
          unitToMove.position = [...action.target_position];
          unitToMove.remainingMovement = action.state_after.remainingMovement;
          unitToMove.status = action.state_after.status;
          unitToMove.moving = false;
          units = [...units]; // Update reactivity
          
          // Wait for transition to complete
          await new Promise(resolve => setTimeout(resolve, 500));
          
          // Update fog of war
          updateFogOfWarAroundPosition(action.target_position[0], action.target_position[1], 2);
          break;
        }
        
        // Attack and construction cases - similar changes for looking up units by position
        case "attack": {
          // Find attacking unit - first by ID, then by position
          let attackerIndex = -1;
          
          if (action.unit_id) {
            attackerIndex = units.findIndex(u => u.id === action.unit_id);
          }
          
          if (attackerIndex === -1 && action.position && Array.isArray(action.position)) {
            // If not found by ID or ID is null, try by position
            const [posX, posY] = action.position;
            attackerIndex = units.findIndex(u => 
              u.position && 
              Array.isArray(u.position) && 
              u.position[0] === posX && 
              u.position[1] === posY &&
              u.owner === 'ia'
            );
            
            // Assign ID if found but missing
            if (attackerIndex !== -1 && (!units[attackerIndex].id || units[attackerIndex].id === null)) {
              units[attackerIndex].id = `unit-${posX}-${posY}`;
            }
          }
          
          // Find target unit
          let targetIndex = -1;
          
          if (action.target_unit_id) {
            targetIndex = units.findIndex(u => u.id === action.target_unit_id);
          }
          
          if (targetIndex === -1 && action.target_position && Array.isArray(action.target_position)) {
            // Try to find by position if ID fails
            const [targetX, targetY] = action.target_position;
            targetIndex = units.findIndex(u => 
              u.position && 
              Array.isArray(u.position) && 
              u.position[0] === targetX && 
              u.position[1] === targetY &&
              u.owner === 'player'
            );
          }
          
          // Rest of the attack logic remains the same
          if (attackerIndex !== -1) {
            // Animate attack
            const attacker = units[attackerIndex];
            attacker.attacking = true;
            units = [...units]; // Update reactivity
            
            await new Promise(resolve => setTimeout(resolve, 800));
            
            // Update attacker state
            attacker.status = action.state_after.status;
            attacker.remainingMovement = action.state_after.remainingMovement;
            attacker.health = action.state_after.health;
            attacker.attacking = false;
            
            // Update target health if target exists
            if (targetIndex !== -1) {
              const target = units[targetIndex];
              if (action.target_state_after) {
                target.health = action.target_state_after.health;
                
                // Check if target is destroyed
                if (action.target_state_after.health <= 0) {
                  // Remove destroyed unit
                  units.splice(targetIndex, 1);
                }
              }
            }
            
            units = [...units]; // Update reactivity
          }
          break;
        }
        
        case "construction": {
          // Find the unit - first by ID, then by position
          let builderIndex = -1;
          
          if (action.unit_id) {
            builderIndex = units.findIndex(u => u.id === action.unit_id);
          }
          
          if (builderIndex === -1 && action.position && Array.isArray(action.position)) {
            // If not found by ID, try by position
            const [posX, posY] = action.position;
            builderIndex = units.findIndex(u => 
              u.position && 
              Array.isArray(u.position) && 
              u.position[0] === posX && 
              u.position[1] === posY &&
              u.owner === 'ia'
            );
            
            // Assign ID if found but missing
            if (builderIndex !== -1 && (!units[builderIndex].id || units[builderIndex].id === null)) {
              units[builderIndex].id = `unit-${posX}-${posY}`;
            }
          }
          
          // Rest of the construction logic remains the same
          if (builderIndex !== -1) {
            const builder = units[builderIndex];
            
            if (action.building === "city") {
              // Create new city
              const newCity = {
                id: `city_${Date.now()}`,
                name: action.city_name || `IA City ${Date.now()}`,
                position: [...action.position],
                owner: 'ia',
                population: 1
              };
              
              // Add city
              cities = [...cities, newCity];
              
              // Remove settler
              units.splice(builderIndex, 1);
              units = [...units];
              
              // Update fog of war for city
              updateFogOfWarAroundPosition(action.position[0], action.position[1], 3);
            } else {
              // Update builder state
              builder.status = action.state_after.status;
              builder.remainingMovement = action.state_after.remainingMovement;
              units = [...units]; // Update reactivity
            }
          }
          break;
        }
        
        default:
          console.log("Unhandled action type:", action.type);
      }
    } catch (error) {
      console.error("Error visualizing AI action:", error);
    }
    
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  function getActionDescription(action) {
    // Get a unit description based on type, id, or position
    function getUnitDescription(unitId, position) {
      // If we have a valid ID that's not position-based, use it
      if (unitId && 
          unitId !== "null" && 
          unitId !== "undefined" && 
          !unitId.startsWith("unit-")) {
        return unitId.replace(/_/g, ' ');
      }
      
      // Otherwise, try to find what unit is at this position and use its type
      if (position && Array.isArray(position) && position.length >= 2) {
        const unitAtPosition = units.find(u => 
          u.position && 
          Array.isArray(u.position) && 
          u.position[0] === position[0] && 
          u.position[1] === position[1] &&
          u.owner === 'ia'
        );
        
        if (unitAtPosition) {
          // Prioritize showing the unit type in the UI
          const unitType = unitAtPosition.type_id || "desconocida";
          
          // Return a user-friendly name based on unit type
          switch(unitType.toLowerCase()) {
            case "warrior": return "guerrero";
            case "archer": return "arquero";
            case "settler": return "colono";
            case "cavalry": return "caballería";
            case "builder": return "constructor";
            default: return unitType;
          }
        }
        
        // Fallback to generic description without showing coordinates
        return "unidad";
      }
      
      return "unidad desconocida";
    }
    
    switch (action.type) {
      case "movement":
        const unitName = getUnitDescription(action.unit_id, action.position);
        return `La ${unitName} se mueve de [${action.position[0]},${action.position[1]}] a [${action.target_position[0]},${action.target_position[1]}]`;
        
      case "attack":
        const attackerName = getUnitDescription(action.unit_id, action.position);
        const targetName = getUnitDescription(action.target_unit_id, action.target_position);
        return `La ${attackerName} ataca a tu unidad ${targetName}`;
        
      case "construction":
        if (action.building === "city") {
          const builderName = getUnitDescription(action.unit_id, action.position);
          return `El colono funda una nueva ciudad${action.city_name ? ': ' + action.city_name : ''}`;
        }
        return `La IA construye ${action.building || "una estructura"}`;
        
      default:
        return `La IA realiza una acción: ${action.type}`;
    }
  }

  function ensureAIUnitsExist() {
    if (!gameData || !gameData.ia || !Array.isArray(gameData.ia.units)) return;
    
    // Get current AI units by ID
    const currentAIUnitIds = units.filter(u => u.owner === 'ia').map(u => u.id);
    
    // Add any missing AI units
    for (const iaUnit of gameData.ia.units) {
      if (!currentAIUnitIds.includes(iaUnit.id)) {
        console.log(`Adding missing AI unit to display: ${iaUnit.id}`);
        
        const newUnit = {
          ...iaUnit,
          owner: 'ia'
        };
        
        units = [...units, newUnit];
      }
    }
  }

  function updateGameStateAfterAITurn() {
    if (!gameData || !gameData.ia) return;
    
    // Update gameData with the changes to units
    const aiUnits = units.filter(u => u.owner === 'ia');
    gameData.ia.units = aiUnits;
    
    // Update gameData with the changes to cities
    const aiCities = cities.filter(c => c.owner === 'ia');
    gameData.ia.cities = aiCities || [];
    
    console.log(`AI state updated: ${aiUnits.length} units and ${aiCities.length} cities`);
  }

  function centerMapOnPosition(x, y) {
    const containerWidth = window.innerWidth;
    const containerHeight = window.innerHeight;

    offsetX = (containerWidth / 2) - (x * tileSize * zoomLevel);
    offsetY = (containerHeight / 2) - (y * tileSize * zoomLevel);
  }

  async function endTurn() {
    // Block if processing is already in progress
    if (processingAITurn) {
      console.log("Turn processing already in progress, ignoring request");
      return;
    }

    if (!gameData) {
      console.error("Cannot end turn, game data is not loaded.");
      return;
    }

    // Block turn end if there's a unit awaiting placement
    if (awaitingUnitPlacement && newlyProducedUnit) {
      showToastNotification("Debes colocar tu unidad antes de finalizar el turno", "warning", 5000);
      
      // Re-center on the producing city to help player locate where to place the unit
      if (producingCity) {
        const cityPos = Array.isArray(producingCity.position) ? 
          producingCity.position : [producingCity.position.x, producingCity.position.y];
        centerMapOnPosition(cityPos[0], cityPos[1]);
        
        // Recalculate city area to make it visible
        calculateCityArea(producingCity);
      }
      return;
    }

    // Set processing flag to true at the beginning of the turn
    processingAITurn = true;
    
    try {
      console.log(`Player ${gameData.current_player} ending turn ${gameData.turn}.`);

      // Handle player city production before switching to AI turn
      const completedProductions = await processCityProduction();
      
      // If we just completed a production that requires unit placement, block turn end
      if (awaitingUnitPlacement && newlyProducedUnit) {
        showToastNotification("Nueva unidad producida. Debes colocarla antes de finalizar el turno", "success", 5000);
        processingAITurn = false; // Reset processing flag
        return;
      }

      // Show notifications for completed productions (that don't require placement)
      if (completedProductions && completedProductions.length > 0) {
        // Show notifications sequentially with a slight delay between them
        for (let i = 0; i < completedProductions.length; i++) {
          const production = completedProductions[i];
          // Use a timeout to stagger notifications
          setTimeout(() => {
            showToastNotification(production.message, "success", 4000);
          }, i * 1000); // 1 second between notifications
        }
        
        // Wait a moment for the player to see notifications before proceeding to AI turn
        await new Promise(resolve => setTimeout(resolve, 1500));
      }

      // Generate and distribute resources for player cities before ending player turn
      const playerResources = await calculateAndDistributeResources('player');
      if (playerResources && Object.values(playerResources).some(val => val > 0)) {
        showResourceGenerationNotification(playerResources, 'player');
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      gameData.current_player = "ia";
      currentPlayer.set(gameData.current_player);
      showToastNotification("IA's Turn - Processing...", "info");
      
      // Process AI city production before AI actions
      const aiCompletedProductions = await processAICityProduction();
      
      try {
        console.log("Requesting AI action...");
        const aiResponse = await gameAPI.getAIAction(gameData);
        console.log("AI Response:", aiResponse);
        
        if (aiResponse && aiResponse.actions && aiResponse.actions.length > 0) {
          // Show AI production notifications if there were any
          if (aiCompletedProductions && aiCompletedProductions.length > 0) {
            showToastNotification(`La IA ha completado ${aiCompletedProductions.length} producciones`, "info", 3000);
          }
          
          await processAIActions(aiResponse.actions, aiResponse.reasoning);
        } else {
          showToastNotification("La IA ha completado su turno (sin acciones)", "info");
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      } catch (error) {
        console.error("Error getting AI action:", error);
        showToastNotification("Error processing AI turn", "error");
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      // Generate and distribute resources for AI cities after AI turn
      const aiResources = await calculateAndDistributeResources('ia');
      if (aiResources && Object.values(aiResources).some(val => val > 0)) {
        // Optional: Show notification about AI resources (or keep it hidden)
        console.log("AI resources generated:", aiResources);
      }
      
      await new Promise(resolve => setTimeout(resolve, 500));

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
    } catch (error) {
      console.error("Unexpected error during end turn:", error);
      showToastNotification("Error inesperado al finalizar turno", "error");
    } finally {
      // Always re-enable the button when done, regardless of whether there was an error
      processingAITurn = false;
    }
  }

  async function processCityProduction() {
    if (!gameData || !gameData.player || !gameData.player.cities) {
      return [];
    }
    
    // Array to track completed productions for notification purposes
    let completedProductions = [];
    
    // Process each city's production
    for (const city of gameData.player.cities) {
      if (city.production && city.production.current_item && city.production.turns_remaining > 0) {
        // Decrease turns remaining
        city.production.turns_remaining--;
        
        // If production is complete
        if (city.production.turns_remaining <= 0) {
          try {
            const itemId = city.production.current_item;
            const itemType = city.production.itemType || "troop"; // Default to "troop" for backward compatibility
            
            // Get the city position
            const cityPosition = Array.isArray(city.position) ? 
              [...city.position] : 
              [city.position.x, city.position.y];
            
            // Handle different item types differently
            if (itemType === "troop") {
              // Get complete troop info from API
              let troopInfo = null;
              try {
                // Get full troop details from API
                const allTroopTypes = await gameAPI.getTroopTypes();
                troopInfo = allTroopTypes.find(t => t.type_id === itemId || t.id === itemId);
                
                if (!troopInfo) {
                  // Fallback to direct API call if not found in list
                  troopInfo = await gameAPI.getTroopType(itemId);
                }
              } catch (e) {
                console.warn("Could not get troop info from API, using defaults", e);
                troopInfo = {
                  name: itemId,
                  type_id: itemId,
                  movement: 2,
                  health: 100,
                  attack: 10,
                  defense: 5
                };
              }
              
              // Create a unique ID for the new unit
              const unitId = `unit-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
              
              // Create a complete unit with ALL properties from the troop type
              const tempUnit = {
                // Copy all properties from the API model
                ...troopInfo,
                // Override/add runtime-specific properties
                id: unitId,
                type_id: itemId,
                owner: 'player',
                status: 'ready',
                // Ensure these critical properties exist
                movement: troopInfo.movement || 2,
                remainingMovement: troopInfo.movement || 2,
                health: troopInfo.health || 100,
                attack: troopInfo.attack || 10,
                defense: troopInfo.defense || 5
              };
              
              // Set up the placement mode
              newlyProducedUnit = tempUnit;
              producingCity = city;
              awaitingUnitPlacement = true;
              
              // Calculate city area for placement UI
              calculateCityArea(city);
              
              // Show very prominent notification
              const notificationMessage = `${city.name} ha completado la producción de ${tempUnit.name || itemId}. ¡Coloca la unidad en el mapa!`;
              showToastNotification(notificationMessage, "success", 8000);
              
              // Center map on city to help player see where to place unit
              centerMapOnPosition(cityPosition[0], cityPosition[1]);
              
              // Add to completed productions for reference
              completedProductions.push({
                type: 'troop',
                name: tempUnit.name || itemId,
                city: city.name,
                requiresPlacement: true,
                message: notificationMessage
              });
              
              // Break out of the loop - handle one production at a time
              break;
              
            } else if (itemType === "building") {
              // Get complete building details
              let buildingDetails;
              try {
                buildingDetails = await gameAPI.getBuildingType(itemId);
              } catch (apiError) {
                console.error(`API Error getting building type ${itemId}:`, apiError);
                buildingDetails = {
                  type_id: itemId,
                  name: `Building ${itemId}`
                };
              }
              
              // Create a new building object with ALL properties from the API
              const newBuilding = {
                // Copy all properties from the building type
                ...buildingDetails,
                // Add runtime-specific properties
                id: `${itemId}_${Date.now()}`,
                type_id: itemId,
                constructed_at: gameData.turn
              };
              
              // Add building directly to the city
              if (!city.buildings) {
                city.buildings = [];
              }
              city.buildings.push(newBuilding);
              
              // Show prominent notification for building completion
              const notificationMessage = `${city.name} ha completado la construcción de ${buildingDetails.name || itemId}.`;
              showToastNotification(notificationMessage, "success", 6000);
              
              // Add to completed productions
              completedProductions.push({
                type: 'building',
                name: buildingDetails.name || itemId,
                city: city.name,
                requiresPlacement: false,
                message: notificationMessage
              });
              
              // Update game state immediately
              await gameAPI.updateGameSession(gameData);
              
              // Clear the city's production
              city.production.current_item = null;
              city.production.turns_remaining = 0;
              city.production.itemType = null;
            }
          } catch (error) {
            console.error(`Error completing production in city ${city.name}:`, error);
            // In case of error, still clear the production
            city.production.current_item = null;
            city.production.turns_remaining = 0;
            city.production.itemType = null;
          }
        }
      }
    }
    
    return completedProductions;
  }

  async function processAICityProduction() {
    if (!gameData || !gameData.ia || !gameData.ia.cities) {
      return [];
    }
    
    let completedProductions = [];
    
    // Process each AI city's production
    for (const city of gameData.ia.cities) {
      if (city.production && city.production.current_item && city.production.turns_remaining > 0) {
        // Decrease turns remaining
        city.production.turns_remaining--;
        
        // If production is complete
        if (city.production.turns_remaining <= 0) {
          try {
            const itemId = city.production.current_item;
            const itemType = city.production.itemType || "troop";
            
            // Get the city position
            const cityPosition = Array.isArray(city.position) ? 
              [...city.position] : [city.position.x, city.position.y];
            
            if (itemType === "troop") {
              // Get complete troop info from API
              let troopInfo;
              try {
                // Find valid position around the city for AI unit
                const validPos = findValidPositionNearCity(cityPosition);
                
                // Get full details from API with position
                troopInfo = await gameAPI.getTroopType(itemId, validPos);
                
                // If API call fails to return all properties, get them from troop types list
                if (!troopInfo.abilities || !troopInfo.description) {
                  const allTroopTypes = await gameAPI.getTroopTypes();
                  const fullTroopType = allTroopTypes.find(t => t.type_id === itemId);
                  if (fullTroopType) {
                    // Merge the properties, keeping the position from the first call
                    troopInfo = { ...fullTroopType, position: troopInfo.position || validPos };
                  }
                }
              } catch (e) {
                console.warn("AI couldn't get troop details, using defaults", e);
                troopInfo = {
                  name: itemId,
                  type_id: itemId,
                  movement: 2,
                  health: 100,
                  attack: 10,
                  defense: 5
                };
              }
              
              // Create a unique ID for the new unit
              const unitId = `ia-unit-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`;
              
              // Create the unit with ALL properties from the troop type
              const newUnit = {
                // Copy all properties from the API model
                ...troopInfo,
                // Override/add runtime-specific properties
                id: unitId,
                type_id: itemId,
                position: troopInfo.position || findValidPositionNearCity(cityPosition),
                owner: 'ia',
                status: 'ready',
                // Ensure these critical properties exist
                movement: troopInfo.movement || 2,
                remainingMovement: troopInfo.movement || 2,
                health: troopInfo.health || 100,
                attack: troopInfo.attack || 10,
                defense: troopInfo.defense || 5
              };
              
              // Add to game data and units array
              if (!gameData.ia.units) {
                gameData.ia.units = [];
              }
              
              gameData.ia.units.push(newUnit);
              units = [...units, newUnit];
              
              // Add to completed productions
              completedProductions.push({
                type: 'troop',
                name: troopInfo.name || itemId,
                city: city.name,
                message: `La ciudad ${city.name} de la IA ha producido ${troopInfo.name || itemId}`
              });
              
            } else if (itemType === "building") {
              // Get complete building details
              let buildingDetails;
              try {
                buildingDetails = await gameAPI.getBuildingType(itemId);
              } catch (apiError) {
                buildingDetails = {
                  type_id: itemId,
                  name: `Building ${itemId}`
                };
              }
              
              // Create a new building with ALL properties from the API
              const newBuilding = {
                // Copy all properties from the building type
                ...buildingDetails,
                // Add runtime-specific properties
                id: `${itemId}_${Date.now()}`,
                type_id: itemId,
                constructed_at: gameData.turn
              };
              
              // Add building to city
              if (!city.buildings) {
                city.buildings = [];
              }
              city.buildings.push(newBuilding);
              
              // Add to completed productions
              completedProductions.push({
                type: 'building',
                name: buildingDetails.name || itemId,
                city: city.name,
                message: `La ciudad ${city.name} de la IA ha construido ${buildingDetails.name || itemId}`
              });
            }
            
            // Clear the city's production regardless of type
            city.production.current_item = null;
            city.production.turns_remaining = 0;
            city.production.itemType = null;
            
          } catch (error) {
            console.error(`Error completing production in AI city ${city.name}:`, error);
            city.production.current_item = null;
            city.production.turns_remaining = 0;
            city.production.itemType = null;
          }
        }
      }
    }
    
    return completedProductions;
  }

  // New function to show resource generation notification
  function showResourceGenerationNotification(resources, playerType) {
    if (!resources) return;
    
    // Only show notifications for the human player
    if (playerType !== 'player') return;
    
    let resourceMessage = "Recursos generados: ";
    let hasResources = false;
    
    if (resources.food > 0) {
      resourceMessage += `🌾 ${resources.food} `;
      hasResources = true;
    }
    if (resources.gold > 0) {
      resourceMessage += `💰 ${resources.gold} `;
      hasResources = true;
    }
    if (resources.wood > 0) {
      resourceMessage += `🌲 ${resources.wood} `;
      hasResources = true;
    }
    if (resources.iron > 0) {
      resourceMessage += `⚙️ ${resources.iron} `;
      hasResources = true;
    }
    if (resources.stone > 0) {
      resourceMessage += `🪨 ${resources.stone} `;
      hasResources = true;
    }
    
    if (hasResources) {
      showToastNotification(resourceMessage, "success", 5000);
    }
  }

  // Helper function to calculate resource generation based on buildings and resource counts
  function calculateResourceGeneration(city, resourceCounts) {
    const generatedResources = {
      food: 0,
      gold: 0,
      wood: 0,
      iron: 0,
      stone: 0
    };
    
    // Base resource generation for cities
    generatedResources.food += 1; // Each city generates 1 food by default
    
    // If no buildings, return base generation only
    if (!city.buildings || city.buildings.length === 0) {
      return generatedResources;
    }
    
    // Process each building
    for (const building of city.buildings) {
      // Get default outcome based on building type if not specified
      const outcome = building.output || getDefaultBuildingOutcome(building.type_id);
      
      // Apply resource generation based on building type and available resources
      switch (building.type_id) {
        case "farm":
        case "granary":
          // Each farm/granary building multiplies its food outcome by the number of food tiles
          if (outcome.food && resourceCounts.food > 0) {
            const foodGenerated = outcome.food * resourceCounts.food;
            generatedResources.food += foodGenerated;
            console.log(`${city.name}: ${building.type_id} generated ${foodGenerated} food from ${resourceCounts.food} food tiles`);
          }
          break;
        case "mine":
        case "Gold_mine":
          // Each mine building multiplies its gold outcome by the number of gold tiles
          if (outcome.gold && resourceCounts.gold > 0) {
            const goldGenerated = outcome.gold * resourceCounts.gold;
            generatedResources.gold += goldGenerated;
            console.log(`${city.name}: ${building.type_id} generated ${goldGenerated} gold from ${resourceCounts.gold} gold tiles`);
          }
          break;
        case "Sawmill":
        case "lumber_mill":
          // Each sawmill building multiplies its wood outcome by the number of wood tiles
          if (outcome.wood && resourceCounts.wood > 0) {
            const woodGenerated = outcome.wood * resourceCounts.wood;
            generatedResources.wood += woodGenerated;
            console.log(`${city.name}: ${building.type_id} generated ${woodGenerated} wood from ${resourceCounts.wood} wood tiles`);
          }
          break;
        case "forge":
        case "Iron_mine":
          // Each forge/iron mine building multiplies its iron outcome by the number of iron tiles
          if (outcome.iron && resourceCounts.iron > 0) {
            const ironGenerated = outcome.iron * resourceCounts.iron;
            generatedResources.iron += ironGenerated;
            console.log(`${city.name}: ${building.type_id} generated ${ironGenerated} iron from ${resourceCounts.iron} iron tiles`);
          }
          break;
        case "Quarry":
          // Each quarry building multiplies its stone outcome by the number of stone tiles
          if (outcome.stone && resourceCounts.stone > 0) {
            const stoneGenerated = outcome.stone * resourceCounts.stone;
            generatedResources.stone += stoneGenerated;
            console.log(`${city.name}: ${building.type_id} generated ${stoneGenerated} stone from ${resourceCounts.stone} stone tiles`);
          }
          break;
        // Add other building types as needed
      }
    }
    
    return generatedResources;
  }

  // Helper function to get default outcomes for buildings when outcome property is missing
  function getDefaultBuildingOutcome(buildingType) {
    switch (buildingType) {
      case "farm":
        return { food: 2 };
      case "granary":
        return { food: 3 };
      case "mine":
      case "gold_mine":
        return { gold: 2 };
      case "sawmill":
      case "lumber_mill":
        return { wood: 2 };
      case "forge":
      case "iron_mine":
        return { iron: 2 };
      case "quarry":
      case "stone_mine":
        return { stone: 2 };
      default:
        return {}; // No outcome for unknown buildings
    }
  }

  async function calculateAndDistributeResources(playerType) {
    if (!gameData) return null;
    
    const resourcesGenerated = {
      food: 0,
      gold: 0,
      wood: 0,
      iron: 0,
      stone: 0
    };
    
    const player = playerType === 'ia' ? gameData.ia : gameData.player;
    
    if (!player || !player.cities || player.cities.length === 0) {
      return null;
    }
    
    console.log(`Calculating resources for ${playerType}'s cities (${player.cities.length} cities)`);
    
    // Process each city for the current player
    for (const city of player.cities) {
      console.log(`Processing city: ${city.name}`);
      const cityResources = countResourcesInCityArea(city);
      console.log(`${city.name} has resources in area:`, cityResources);
      
      const cityBuildings = city.buildings || [];
      console.log(`${city.name} has ${cityBuildings.length} buildings`);
      
      const cityGeneration = calculateResourceGeneration(city, cityResources);
      console.log(`${city.name} generated resources:`, cityGeneration);
      
      // Add to total generated resources
      resourcesGenerated.food += cityGeneration.food;
      resourcesGenerated.gold += cityGeneration.gold;
      resourcesGenerated.wood += cityGeneration.wood;
      resourcesGenerated.iron += cityGeneration.iron;
      resourcesGenerated.stone += cityGeneration.stone;
    }
    
    console.log(`Total resources generated for ${playerType}:`, resourcesGenerated);
    
    // Add resources to player
    if (!player.resources) {
      player.resources = { food: 0, gold: 0, wood: 0, iron: 0, stone: 0 };
    }
    
    player.resources.food = (player.resources.food || 0) + resourcesGenerated.food;
    player.resources.gold = (player.resources.gold || 0) + resourcesGenerated.gold;
    player.resources.wood = (player.resources.wood || 0) + resourcesGenerated.wood;
    player.resources.iron = (player.resources.iron || 0) + resourcesGenerated.iron;
    player.resources.stone = (player.resources.stone || 0) + resourcesGenerated.stone;
    
    // Return the resources generated for notification
    return resourcesGenerated;
  }

  // Helper function to count resources in a city's area
  function countResourcesInCityArea(city) {
    const resourceCounts = {
      food: 0,
      gold: 0,
      wood: 0,
      iron: 0,
      stone: 0
    };
    
    if (!city || !city.area) {
      return resourceCounts;
    }
    
    // Get city position
    const cityPosX = Array.isArray(city.position) ? city.position[0] : city.position.x;
    const cityPosY = Array.isArray(city.position) ? city.position[1] : city.position.y;
    
    // Calculate area radius (half the side length)
    const radius = Math.floor(city.area / 2);
    
    // Calculate the starting positions (top-left corner of the square)
    const startX = cityPosX - radius;
    const startY = cityPosY - radius;
    
    // Check each tile in the city area
    for (let y = 0; y < city.area; y++) {
      for (let x = 0; x < city.area; x++) {
        const tileX = startX + x;
        const tileY = startY + y;
        
        // Check if the tile is within map bounds
        if (tileX >= 0 && tileX < mapWidth && tileY >= 0 && tileY < mapHeight) {
          // Get terrain type for this tile
          const terrainType = terrain[tileY] && terrain[tileX];
          
          // Count resource based on terrain type
          switch (terrainType) {
            case 2: // Gold
              resourceCounts.gold++;
              break;
            case 3: // Iron
              resourceCounts.iron++;
              break;
            case 4: // Wood
              resourceCounts.wood++;
              break;
            case 5: // Stone
              resourceCounts.stone++;
              break;
          }
        }
      }
    }
    
    return resourceCounts;
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

  function calculateValidMoveTargets(startX, startY, movementPoints) {
    validMoveTargets = [];
    const movementRange = Math.min(movementPoints, 2); // Limit movement range to 2 tiles per turn
    
    // Check each tile within the movement range
    for (let y = Math.max(0, startY - movementRange); y <= Math.min(mapHeight - 1, startY + movementRange); y++) {
      for (let x = Math.max(0, startX - movementRange); x <= Math.min(mapWidth - 1, startX + movementRange); x++) {
        // Skip the current tile
        if (x === startX && y === startY) continue;
        
        // Calculate Manhattan distance (number of steps)
        const steps = Math.abs(x - startX) + Math.abs(y - startY);
        
        // If beyond movement range, skip
        if (steps > movementRange) continue;
        
        // Skip water tiles
        if (terrain[y] && terrain[y][x] === TERRAIN_TYPES.WATER) continue;
        
        // Check if the tile is already occupied by another unit
        const occupyingUnit = units.find(u => 
          u !== selectedUnit && 
          u.position && 
          Array.isArray(u.position) && 
          u.position[0] === x && 
          u.position[1] === y
        );
        
        // Skip if occupied
        if (occupyingUnit) continue;
        
        // Check if the tile has a city
        const cityAtPosition = cities.find(city => 
          (city.position.x === x && city.position.y === y) || 
          (Array.isArray(city.position) && city.position[0] === x && city.position[1] === y)
        );
        
        // Skip if there's a city
        if (cityAtPosition) continue;
        
        // Check if we have enough movement points to reach this tile
        if (movementPoints >= steps) {
          // Add valid target with remaining movement after this move
          validMoveTargets.push({ 
            x, 
            y, 
            remainingMovement: movementPoints - steps 
          });
        }
      }
    }
  }

  function moveUnitToPosition(unit, targetX, targetY) {
    if (movementInProgress) return;
    
    const occupyingUnit = units.find(u => 
      u !== unit && 
      u.position && 
      Array.isArray(u.position) && 
      u.position[0] === targetX && 
      u.position[1] === targetY
    );
    
    if (occupyingUnit) {
      showToastNotification(`No puedes mover a la casilla (${targetX}, ${targetY}). Está ocupada por otra unidad.`, "error");
      return;
    }
    
    // Add check for city at target position
    const cityAtPosition = cities.find(city => 
      (city.position.x === targetX && city.position.y === targetY) || 
      (Array.isArray(city.position) && city.position[0] === targetX && city.position[1] === targetY)
    );
    
    if (cityAtPosition) {
      showToastNotification(`No puedes mover a la casilla (${targetX}, ${targetY}). Hay una ciudad en esa posición.`, "error");
      return;
    }
    
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
            // Find the unit by ID first, and by position as fallback to make sure
      // we're modifying the correct unit
      let unitIndex = -1;
      
      if (unit.id) {
        // Find by ID (most reliable)
        unitIndex = units.findIndex(u => u.id === unit.id);
      }
      
      // If unit was not found by ID, find it by original position
      if (unitIndex === -1 && Array.isArray(unit.position)) {
        const [unitX, unitY] = unit.position;
        unitIndex = units.findIndex(u => 
          u === unit || 
          (u.position && 
           Array.isArray(u.position) && 
           u.position[0] === unitX && 
           u.position[1] === unitY && 
           u.owner === unit.owner &&
           u.type_id === unit.type_id)
        );
      }
      
      // Make absolutely sure we have the right unit before moving it
      if (unitIndex !== -1) {
        const unitToMove = units[unitIndex];
        const originalPosition = [...unitToMove.position];
        
        console.log(`Moving unit ${unitToMove.type_id} (${unitToMove.id}) from [${originalPosition}] to [${targetX},${targetY}]`);
        
        // Calculate the movement cost
        const movementCost = Math.abs(targetX - originalPosition[0]) + Math.abs(targetY - originalPosition[1]);
        
        if (unitToMove.remainingMovement === undefined) {
          unitToMove.remainingMovement = unitToMove.movement || 2;
        }
        
        if (unitToMove.remainingMovement < movementCost) {
          showToastNotification("Movimiento ilegal: no hay suficientes puntos de movimiento", "error");
          movementInProgress = false;
          return;
        }
        
        // Create a copy of the unit object to avoid reference issues
        const updatedUnit = { ...unitToMove };
        
        // Update unit position and movement points
        updatedUnit.position = [targetX, targetY];
        updatedUnit.remainingMovement -= movementCost;
        
        // Update unit status based on remaining movement
        if (updatedUnit.remainingMovement <= 0) {
          updatedUnit.status = 'exhausted';
        } else {
          updatedUnit.status = 'moved';
        }
        
        // Update the unit in the array with our updated copy
        units[unitIndex] = updatedUnit;
        
        // Ensure reactivity by creating a new array
        units = [...units];
        
        // Update unit info panel if it's showing this unit
        if (selectedUnitInfo && (selectedUnitInfo.id === updatedUnit.id || selectedUnitInfo === unit)) {
          selectedUnitInfo = updatedUnit;
        }
        
        // Update game data 
        if (gameData && gameData.player && Array.isArray(gameData.player.units)) {
          const gameDataUnitIndex = gameData.player.units.findIndex(u => 
            (u.id && u.id === updatedUnit.id) || 
            (u.position && 
             Array.isArray(u.position) && 
             u.position[0] === originalPosition[0] && 
             u.position[1] === originalPosition[1] &&
             u.type_id === updatedUnit.type_id)
          );
          
          if (gameDataUnitIndex !== -1) {
            gameData.player.units[gameDataUnitIndex].position = [targetX, targetY];
            gameData.player.units[gameDataUnitIndex].status = updatedUnit.status;
            gameData.player.units[gameDataUnitIndex].remainingMovement = updatedUnit.remainingMovement;
          }
        }
        
        // Update fog of war around new position
        updateFogOfWarAroundPosition(targetX, targetY, 2);
        
        // Update selected unit reference to the updated unit
        selectedUnit = updatedUnit;
        
        // If unit has remaining movement, show updated valid moves
        if (updatedUnit.remainingMovement > 0) {
          selectUnit(updatedUnit);
        } else {
          // Clear selection if no more movement
          selectedUnit = null;
          validMoveTargets = [];
        }
      } else {
        console.error("Could not find unit to move in the units array");
        showToastNotification("Error al mover la unidad: unidad no encontrada", "error");
      }
    } catch (error) {
      console.error("Error moving unit:", error);
      showToastNotification("Error al mover la unidad", "error");
    } finally {
      movementInProgress = false;
    }
  }

  function handleTileClick(x, y) {
    // First check if we're in unit placement mode
    if (awaitingUnitPlacement && newlyProducedUnit) {
      placeNewUnit(x, y);
      return;
    }
    
    // Check if the clicked position is an attack target
    if (attackingUnit && showAttackOptions) {
      const targetUnit = units.find(u => 
        u.owner === 'ia' && 
        u.position && 
        Array.isArray(u.position) && 
        u.position[0] === x && 
        u.position[1] === y
      );
      
      if (targetUnit && attackTargets.some(target => target === targetUnit)) {
        initiateAttack(targetUnit);
        return;
      }
    }
    
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
      
      // Calculate and display the city area
      calculateCityArea(cityAtPosition);
      return;
    }
    
    // When clicking somewhere else, clear the city area
    cityAreaTiles = [];
    
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

  function calculateCityArea(city) {
    cityAreaTiles = [];
    
    if (!city || !city.area) {
      return;
    }
    
    // Get city position
    const cityPosX = Array.isArray(city.position) ? city.position[0] : city.position.x;
    const cityPosY = Array.isArray(city.position) ? city.position[1] : city.position.y;
    
    // Calculate area radius (half the side length)
    const radius = Math.floor(city.area / 2);
    
    // Calculate the starting positions (top-left corner of the square)
    const startX = cityPosX - radius;
    const startY = cityPosY - radius;
    
    // Generate all tiles in the city area
    for (let y = 0; y < city.area; y++) {
      for (let x = 0; x < city.area; x++) {
        const tileX = startX + x;
        const tileY = startY + y;
        
        // Check if the tile is within map bounds
        if (tileX >= 0 && tileX < mapWidth && tileY >= 0 && tileY < mapHeight) {
          // Add the tile to city area tiles
          cityAreaTiles.push({ x: tileX, y: tileY });
        }
      }
    }
  }

  function clearSelections() {
    selectedUnit = null;
    selectedUnitInfo = null;
    selectedCityInfo = null;
    selectedTile = null;
    validMoveTargets = [];
    cityAreaTiles = [];
  }

  async function placeNewUnit(x, y) {
    try {
      // Check if the target position is valid
      if (!isValidPlacementPosition(x, y)) {
        showToastNotification("No puedes colocar la unidad en esa posición. Elige otra casilla dentro del área de la ciudad.", "error");
        return;
      }
      
      // Now that we have a valid position, get the FULL troop details with position
      try {
        // Here's where we call getTroopType with the position the player chose
        const position = [x, y];
        const troopDetails = await gameAPI.getTroopType(newlyProducedUnit.type_id, position);
        
        // Update the unit with complete details from the API
        newlyProducedUnit.position = position;
        newlyProducedUnit.movement = troopDetails.movement || newlyProducedUnit.movement;
        newlyProducedUnit.remainingMovement = troopDetails.movement || newlyProducedUnit.movement;
        newlyProducedUnit.health = troopDetails.health || newlyProducedUnit.health;
        newlyProducedUnit.attack = troopDetails.attack || newlyProducedUnit.attack;
        newlyProducedUnit.defense = troopDetails.defense || newlyProducedUnit.defense;
        
        // Set full name in case it was updated
        if (troopDetails.name) {
          newlyProducedUnit.name = troopDetails.name;
        }
      } catch (error) {
        console.error("Error getting full troop details:", error);
        // Still place the unit with basic details if API fails
        newlyProducedUnit.position = [x, y];
        newlyProducedUnit.remainingMovement = newlyProducedUnit.movement || 2;
      }
      
      // Add the unit to the player's units
      units = [...units, newlyProducedUnit];
      
      if (!gameData.player.units) {
        gameData.player.units = [];
      }
      
      gameData.player.units.push(newlyProducedUnit);
      
      // Update fog of war around the new unit
      updateFogOfWarAroundPosition(x, y, 2);
      
      // Clear the production for the city that produced this unit
      if (producingCity && producingCity.production) {
        producingCity.production.current_item = null;
        producingCity.production.turns_remaining = 0;
        producingCity.production.itemType = null;
      }
      
      // Update the game state
      await gameAPI.updateGameSession(gameData);
      
      // Show a success notification
      showToastNotification(`¡${newlyProducedUnit.name} colocado con éxito!`, "success", 4000);
      
      // Clear the placement mode and city area highlighting
      awaitingUnitPlacement = false;
      newlyProducedUnit = null;
      producingCity = null;
      cityAreaTiles = [];
      
    } catch (error) {
      console.error("Error placing new unit:", error);
      showToastNotification("Error al colocar la unidad", "error");
    }
  }

  function isValidPlacementPosition(x, y) {
    if (!producingCity) return false;
    
    // Check if position is within the city area tiles
    const isInCityArea = cityAreaTiles.some(tile => tile.x === x && tile.y === y);
    if (!isInCityArea) {
      return false;
    }
    
    // Check if position is water
    if (terrain[y] && terrain[y][x] === TERRAIN_TYPES.WATER) {
      return false;
    }
    
    // Check if position is occupied by another unit
    const isOccupied = units.some(unit => 
      unit.position && 
      Array.isArray(unit.position) && 
      unit.position[0] === x && 
      unit.position[1] === y
    );
    
    // NEW: Check if position has a city
    const hasCityAtPosition = cities.some(city => 
      (city.position.x === x && city.position.y === y) || 
      (Array.isArray(city.position) && city.position[0] === x && city.position[1] === y)
    );
    
    return !isOccupied && !hasCityAtPosition;
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
      case TERRAIN_TYPES.NORMAL: return "#8B4513";
      case TERRAIN_TYPES.WATER: return "#1E90FF";
      case TERRAIN_TYPES.MINERAL: return "#808080";
      default: return "#000";
    }
  }

  // Function to get resource icons based on terrain type
  function getResourceIcon(terrainType) {
    switch (terrainType) {
      case 2: return { type: "image", value: "./ia_assets/oro.png" }; // Gold - changed to image
      case 3: return { type: "image", value: "./ia_assets/metala.png" }; // Iron/Metal
      case 4: return { type: "image", value: "./ia_assets/zuhaitza.png" }; // Wood/Tree
      case 5: return { type: "image", value: "./ia_assets/harria.png" }; // Stone
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
    
    // Check for attack targets
    checkForAttackTargets(unit);
  }

  function handleUnitClick(unit) {
    if (unit.owner !== 'player') {
      showToastNotification("Esta es una unidad enemiga. No puedes controlarla.", "warning");
      return;
    }
    
    selectedUnitInfo = unit;
    
    // If the unit can attack, highlight this information
    if (canAttack(unit)) {
      showToastNotification("¡Esta unidad puede atacar a enemigos cercanos!", "info");
    }
    
    if (unit.status === 'exhausted') {
      showToastNotification("Esta unidad ya ha agotado sus movimientos este turno.", "warning");
      selectedUnit = null;
      validMoveTargets = [];
    } else {
      selectUnit(unit);
    }
  }

  // Update the enterCity function to be more reliable
  async function enterCity(city) {
    if (!gameData || !city) {
      showToastNotification("Error al acceder a la ciudad", "error");
      return;
    }
    
    try {
      // Save current game state to session before navigating
      console.log("Guardando estado del juego en sesión antes de entrar a la ciudad");
      await gameAPI.updateGameSession(gameData);
      
      // Store the city ID in both in-memory storage and localStorage
      const cityId = city.id;
      
      // Make sure cityId is valid
      if (!cityId) {
        showToastNotification("ID de ciudad no válido", "error");
        return;
      }
      
      console.log("Entering city with ID:", cityId);
      
      // Store the ID before navigating
      gameAPI.storeTemporaryData('selectedCityId', cityId);
      
      // Navigate to city page
      navigate('/city');
    } catch (error) {
      console.error("Error entering city:", error);
      showToastNotification("Error al acceder a la ciudad: " + error.message, "error");
    }
  }

  // Function to get unit icon depending on type
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

  // Update unit icon function to use images when available
  function getUnitImageUrl(unitType) {
    switch (unitType) {
      case "warrior": return './ia_assets/warrior.png';
      case "settler": return './ia_assets/settler.png';
      case "cavalry": return './ia_assets/cavalry.png';
      case "archer": return './ia_assets/archer.png'; // Add this case for archer image
      default: return null;
    }
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
        <button 
          class="end-turn-button" 
          on:click={endTurn} 
          title="{processingAITurn ? 'Procesando turno de la IA...' : 'Finalizar Turno'}"
          disabled={processingAITurn}
          class:processing={processingAITurn}
        >
          {processingAITurn ? 'IA pensando...' : 'Terminar Turno'}
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
      role="application" 
      aria-label="Game map"
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
              class:city-area-tile={cityAreaTiles.some(tile => tile.x === x && tile.y === y)}
              class:city-center-tile={selectedCityInfo && 
                ((Array.isArray(selectedCityInfo.position) && selectedCityInfo.position[0] === x && selectedCityInfo.position[1] === y) ||
                (selectedCityInfo.position.x === x && selectedCityInfo.position.y === y))}
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
              on:keydown={(e) => e.key === 'Enter' && handleTileClick(x, y)}
              role="button"
              tabindex="0"
              class:selected={selectedTile && selectedTile.x === x && selectedTile.y === y}
              aria-label="Map tile at position {x},{y}"
            >
              {#if x % 10 === 0 && y % 10 === 0 && isVisible}
                <div class="coord-marker">{x},{y}</div>
              {/if}
              
              {#if hasResource && isVisible}
                <div class="resource-marker" title="{getTerrainName(terrainType)}">
                  {#if getResourceIcon(terrainType).type === "emoji"}
                    <span class="resource-icon">{getResourceIcon(terrainType).value}</span>
                  {:else}
                    <img src={getResourceIcon(terrainType).value} alt="{getTerrainName(terrainType)}" class="resource-image" />
                  {/if}
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
              
              <!-- New attack button that only shows when there are enemies nearby -->
              {#if attackTargets.length > 0}
                <button class="action-button attack-button" on:click={() => showAttackOptions = true}>
                  Atacar
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
      <!-- Add iron resource -->
      <div class="resource iron">
        <div class="resource-icon">
          <img src="./ia_assets/lingote_hierro.png" alt="Iron" class="resource-bar-icon" />
        </div>
        <div class="resource-value">{gameData.player.resources.iron || 0}</div>
      </div>
      <!-- Add stone resource -->
      <div class="resource stone">
        <div class="resource-icon">
          <img src="./ia_assets/harria.png" alt="Stone" class="resource-bar-icon" />
        </div>
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

  <!-- Add AI Action Card Display -->
  {#if processingAITurn && showAIActionCard && currentAIAction}
    <div class="ai-action-overlay">
      <div class="ai-action-card">
        <div class="ai-action-header">
          <h4>Acción de la IA {aiActionIndex + 1}/{aiActions.length}</h4>
        </div>
        
        <div class="ai-action-content">
          <div class="ai-action-icon">
            {#if currentAIAction.type === 'movement'}
              <span class="action-icon">🚶</span>
            {:else if currentAIAction.type === 'attack'}
              <span class="action-icon">⚔️</span>
            {:else if currentAIAction.type === 'construction'}
              <span class="action-icon">🏗️</span>
            {:else}
              <span class="action-icon">🔄</span>
            {/if}
          </div>
          
          <div class="ai-action-description">
            <p>{aiActionDescription}</p>
            {#if currentAIAction.type === 'attack'}
              <div class="combat-indicator">
                <span class="combat-animation">⚔️</span>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  {/if}

  {#if processingAITurn && aiActionIndex === aiActions.length - 1 && aiTurnReasoning}
    <div class="ai-reasoning-overlay">
      <div class="ai-reasoning-card">
        <h4>Estrategia de la IA</h4>
        <p>{aiTurnReasoning}</p>
      </div>
    </div>
  {/if}

  <!-- Add attack targets overlay -->
  {#if showAttackOptions && attackTargets.length > 0 && !showPauseMenu}
    <div class="attack-targets-overlay">
      <div class="attack-targets-card">
        <div class="attack-targets-header">
          <h4>Selecciona objetivo a atacar</h4>
          <button class="close-button" on:click={() => showAttackOptions = false}>×</button>
        </div>
        
        <div class="attack-targets-list">
          {#each attackTargets as target}
            <div class="attack-target" on:click={() => initiateAttack(target)}>
              <div class="target-icon">
                {#if getUnitImageUrl(target.type_id)}
                  <img src={getUnitImageUrl(target.type_id)} alt={target.type_id} />
                {:else}
                  <span class="unit-icon">{getUnitIcon(target.type_id)}</span>
                {/if}
              </div>
              <div class="target-info">
                <h5>{target.name || target.type_id}</h5>
                <p>Salud: {target.health || 100}</p>
                <p>Posición: [{target.position[0]}, {target.position[1]}]</p>
              </div>
              <button class="attack-button">Atacar</button>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}
</div>


