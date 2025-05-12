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

  // Add a variable to track and display movement paths
  let activeMovementPath = null;
  let debugAIMovement = true; // Enable debugging

  // Add this new state variables for unit placement
  let newlyProducedUnit = null;
  let awaitingUnitPlacement = false;
  let producingCity = null;

  // Add this new state variable to track city area tiles
  let cityAreaTiles = [];

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
    
    // Restore fog of war to previous state
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
          // Find the unit to move
          let unitIndex = units.findIndex(u => u.id === action.unit_id);
          
          if (unitIndex === -1) {
            // If not found by ID, try by position
            const [posX, posY] = action.position;
            unitIndex = units.findIndex(u => 
              u.position && 
              Array.isArray(u.position) && 
              u.position[0] === posX && 
              u.position[1] === posY &&
              u.owner === 'ia'
            );
          }
          
          if (unitIndex === -1) {
            console.warn(`Unit for movement not found: ${action.unit_id}. Creating temporary unit for visualization.`);
            
            // Create a temporary unit if none exists
            const tempUnit = {
              id: action.unit_id,
              position: [...action.position],
              type_id: action.unit_type || "warrior",
              owner: 'ia',
              status: 'ready',
              remainingMovement: 2
            };
            
            units = [...units, tempUnit];
            unitIndex = units.length - 1;
          }
          
          const unitToMove = units[unitIndex];
          
          // Check if target position is water (invalid move)
          const [targetX, targetY] = action.target_position;
          if (terrain[targetY] && terrain[targetY][targetX] === TERRAIN_TYPES.WATER) {
            console.warn(`AI attempted invalid move to water tile at [${targetX}, ${targetY}]. Movement ignored.`);
            break;
          }
          
          // Show path
          activeMovementPath = {
            fromX: action.position[0],
            fromY: action.position[1],
            toX: action.target_position[0],
            toY: action.target_position[1]
          };
          
          // Make sure the unit is visible
          unitToMove.moving = true;
          units = [...units]; // Update reactivity
          
          // Wait for animation
          await new Promise(resolve => setTimeout(resolve, 1200));
          
          // Move unit to target position
          unitToMove.position = [...action.target_position];
          unitToMove.remainingMovement = action.state_after.remainingMovement;
          unitToMove.status = action.state_after.status;
          unitToMove.moving = false;
          units = [...units]; // Update reactivity
          
          // Clear path after a moment
          await new Promise(resolve => setTimeout(resolve, 500));
          activeMovementPath = null;
          
          // Update fog of war
          updateFogOfWarAroundPosition(action.target_position[0], action.target_position[1], 2);
          break;
        }
        
        case "attack": {
          // Find attacking unit
          let attackerIndex = units.findIndex(u => u.id === action.unit_id);
          
          if (attackerIndex === -1) {
            // If not found by ID, try by position
            const [posX, posY] = action.position;
            attackerIndex = units.findIndex(u => 
              u.position && 
              Array.isArray(u.position) && 
              u.position[0] === posX && 
              u.position[1] === posY &&
              u.owner === 'ia'
            );
          }
          
          // Find target unit
          let targetIndex = units.findIndex(u => u.id === action.target_unit_id);
          
          if (targetIndex === -1) {
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
          // Find the unit
          let builderIndex = units.findIndex(u => u.id === action.unit_id);
          
          if (builderIndex === -1) {
            // If not found by ID, try by position
            const [posX, posY] = action.position;
            builderIndex = units.findIndex(u => 
              u.position && 
              Array.isArray(u.position) && 
              u.position[0] === posX && 
              u.position[1] === posY &&
              u.owner === 'ia'
            );
          }
          
          if (builderIndex !== -1) {
            const builder = units[builderIndex];
            
            if (action.building === "city") {
              // Create new city
              const newCity = {
                id: `city_${Date.now()}`,
                name: action.city_name,
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
    switch (action.type) {
      case "movement":
        return `La unidad ${action.unit_id.replace(/_/g, ' ')} se mueve de [${action.position[0]},${action.position[1]}] a [${action.target_position[0]},${action.target_position[1]}]`;
      case "attack":
        return `La unidad ${action.unit_id.replace(/_/g, ' ')} ataca a tu unidad ${action.target_unit_id.replace(/_/g, ' ')}`;
      case "construction":
        if (action.building === "city") {
          return `La IA funda una nueva ciudad: ${action.city_name}`;
        }
        return `La IA construye ${action.building}`;
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
    if (!gameData) {
      console.error("Cannot end turn, game data is not loaded.");
      return;
    }

    console.log(`Player ${gameData.current_player} ending turn ${gameData.turn}.`);

    // Handle city production before switching to AI turn
    await processCityProduction();

    gameData.current_player = "ia";
    currentPlayer.set(gameData.current_player);
    showToastNotification("IA's Turn - Processing...", "info");
    
    try {
      console.log("Requesting AI action...");
      const aiResponse = await gameAPI.getAIAction(gameData);
      console.log("AI Response:", aiResponse);
      
      if (aiResponse && aiResponse.actions && aiResponse.actions.length > 0) {
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
  }

  async function processCityProduction() {
    if (!gameData || !gameData.player || !gameData.player.cities) {
      return;
    }
    
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
              // Add extra error handling around the API call
              let troopDetails;
              try {
                // This is where the error occurs - wrap in a try/catch
                troopDetails = await gameAPI.getTroopType(itemId);
              } catch (apiError) {
                console.error(`API Error getting troop type ${itemId}:`, apiError);
                // Provide fallback data if the API call fails
                troopDetails = {
                  name: `Troop ${itemId}`,
                  movement: 2,
                  health: 100,
                  attack: 10,
                  defense: 5
                };
              }
              
              // Create a new unit object
              const newUnit = {
                id: `${itemId}_${Date.now()}`,
                type_id: itemId,
                position: [...cityPosition], // Initially at the city's position
                status: 'ready',
                movement: troopDetails.movement || 2,
                remainingMovement: troopDetails.movement || 2,
                health: troopDetails.health || 100,
                attack: troopDetails.attack,
                defense: troopDetails.defense,
                owner: 'player',
                name: troopDetails.name || itemId
              };
              
              // Store the newly created unit and city for placement
              newlyProducedUnit = newUnit;
              producingCity = city;
              awaitingUnitPlacement = true;
              
              // Calculate city area for placement
              calculateCityArea(city);
              
              // Show a notification to the player
              showToastNotification(`${city.name} ha completado la producción de ${troopDetails.name || itemId}. Elige dónde colocar la unidad.`, "success", 5000);
              
              // Center the map on the city position
              centerMapOnPosition(cityPosition[0], cityPosition[1]);
              
            } else if (itemType === "building") {
              // Add extra error handling for building API call too
              let buildingDetails;
              try {
                buildingDetails = await gameAPI.getBuildingType(itemId);
              } catch (apiError) {
                console.error(`API Error getting building type ${itemId}:`, apiError);
                // Provide fallback data
                buildingDetails = {
                  name: `Building ${itemId}`
                };
              }
              
              // Create a new building object
              const newBuilding = {
                id: `${itemId}_${Date.now()}`,
                type_id: itemId,
                name: buildingDetails.name || itemId,
                constructed_at: gameData.turn
              };
              
              // Add building directly to the city (no placement needed)
              if (!city.buildings) {
                city.buildings = [];
              }
              city.buildings.push(newBuilding);
              
              // Show a notification to the player
              showToastNotification(`${city.name} ha completado la construcción de ${buildingDetails.name || itemId}.`, "success");
              
              // No need for placement - update game state immediately
              await gameAPI.updateGameSession(gameData);
            }
            
            // Clear the city's production
            city.production.current_item = null;
            city.production.turns_remaining = 0;
            city.production.itemType = null;
            
            // Exit the loop after handling one completed production
            break;
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
      
      // Update the unit position
      newlyProducedUnit.position = [x, y];
      
      // Add the unit to the player's units
      units = [...units, newlyProducedUnit];
      
      if (!gameData.player.units) {
        gameData.player.units = [];
      }
      
      gameData.player.units.push(newlyProducedUnit);
      
      // Update the game state
      await gameAPI.updateGameSession(gameData);
      
      // Show a success notification
      showToastNotification(`¡${newlyProducedUnit.name} colocado con éxito!`, "success");
      
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
    
    return !isOccupied;
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

  <!-- Add movement path visualization -->
  {#if activeMovementPath}
    <div 
      class="movement-path-indicator" 
      style="
        left: {activeMovementPath.fromX * tileSize * zoomLevel + offsetX}px;
        top: {activeMovementPath.fromY * tileSize * zoomLevel + offsetY}px;
        width: {tileSize * zoomLevel}px;
        height: {tileSize * zoomLevel}px;
      "
    ></div>
    <div 
      class="movement-path-indicator target" 
      style="
        left: {activeMovementPath.toX * tileSize * zoomLevel + offsetX}px;
        top: {activeMovementPath.toY * tileSize * zoomLevel + offsetY}px;
        width: {tileSize * zoomLevel}px;
        height: {tileSize * zoomLevel}px;
      "
    ></div>
    <div 
      class="movement-path-line"
      style="
        left: {Math.min(activeMovementPath.fromX, activeMovementPath.toX) * tileSize * zoomLevel + offsetX + (tileSize * zoomLevel / 2)}px;
        top: {Math.min(activeMovementPath.fromY, activeMovementPath.toY) * tileSize * zoomLevel + offsetY + (tileSize * zoomLevel / 2)}px;
        width: {Math.abs(activeMovementPath.toX - activeMovementPath.fromX) * tileSize * zoomLevel}px;
        height: {Math.abs(activeMovementPath.toY - activeMovementPath.fromY) * tileSize * zoomLevel}px;
      "
    ></div>
  {/if}

  <!-- Add a UI indicator for unit placement mode -->
  {#if awaitingUnitPlacement && newlyProducedUnit}
    <div class="unit-placement-overlay">
      <div class="unit-placement-card">
        <h3>Colocar Unidad</h3>
        <p>Selecciona una casilla para colocar tu nueva unidad: {newlyProducedUnit.name}</p>
        <div class="unit-preview">
          {#if getUnitImageUrl(newlyProducedUnit.type_id)}
            <img src={getUnitImageUrl(newlyProducedUnit.type_id)} alt={newlyProducedUnit.name} class="unit-placement-image" />
          {:else}
            <span class="unit-placement-icon">{getUnitIcon(newlyProducedUnit.type_id)}</span>
          {/if}
        </div>
        <p class="placement-instruction">Haz clic en una casilla adyacente a la ciudad para colocar la unidad.</p>
      </div>
    </div>
  {/if}
</div>


