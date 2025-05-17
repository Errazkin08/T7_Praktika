<script>
  import { onMount, onDestroy } from "svelte";
  import { navigate } from "../router.js";
  import { gameAPI } from "../services/gameAPI.js";
  import {
    gameState,
    pauseGame,
    endGame,
    currentTurn,
    currentPlayer,
  } from "../stores/gameState.js";
  import { user } from "../stores/auth.js";
  import "../styles/pages/map.css";
  import CheatConsole from "../components/CheatConsole.svelte";
  import NegotiationModal from "../components/NegotiationModal.svelte";
  import AudioPlayer from "../components/AudioPlayer.svelte";

  let audioPlayer;

  function handleFirstInteraction() {
    if (audioPlayer) {
      audioPlayer.initializeAudio();
      // Eliminar event listeners después de inicialización
      document.removeEventListener("click", handleFirstInteraction);
      document.removeEventListener("keydown", handleFirstInteraction);
    }
  }

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
    WATER: 1, // Agua
    MINERAL: 2, // Mineral
  };

  // Constantes para fog of war
  const FOG_OF_WAR = {
    HIDDEN: 0, // No visible
    VISIBLE: 1, // Visible
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

  // Add these variables for cheat console
  let showCheatConsole = false;
  let cheatResult = null;
  let cheatResultType = "info"; // can be "success", "error", "info"

  // Add this variable to track if unlimited movements cheat is active
  let unlimitedMovementsActive = false;

  // Add negotiation modal state variables
  let showNegotiationModal = false;
  let negotiationUnit = null;
  let negotiationResult = null;

  // --- NUEVO: Control de alto el fuego (ceasefire) ---
  let ceasefireTurns = 0;
  let ceasefireActive = false;

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
    newCityName = `Hiria ${Math.floor(Math.random() * 1000)}`;
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
      showToastNotification("Hiriaren izena beharrezkoa da", "error");
      return;
    }

    try {
      const [x, y] = settlerToFoundCity.position;
      if (terrain[y] && terrain[y][x] === TERRAIN_TYPES.WATER) {
        showToastNotification("Ezin da hiria sortu ur gainean", "error");
        return;
      }

      const existingCity = cities.find(
        (city) =>
          (city.position.x === x && city.position.y === y) ||
          (Array.isArray(city.position) &&
            city.position[0] === x &&
            city.position[1] === y),
      );

      if (existingCity) {
        showToastNotification("Hiri bat dago jada posizio honetan", "error");
        return;
      }

      // MODIFICADO: Nuevos requisitos de recursos
      const requiredResources = { wood: 20, stone: 15 };
      const playerResources = gameData?.player?.resources || {};

      if (
        playerResources.wood < requiredResources.wood ||
        playerResources.stone < requiredResources.stone
      ) {
        showToastNotification(
          `Baliabideak ez dira nahikoak. Beharrezkoa: ${requiredResources.wood} egur, ${requiredResources.stone} harria`,
          "error",
        );
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
          turns_remaining: 0,
        },
      };

      cities = [...cities, newCity];

      if (gameData && gameData.player) {
        if (!gameData.player.cities) {
          gameData.player.cities = [];
        }
        gameData.player.cities.push(newCity);

        // MODIFICADO: Actualizar los recursos correctos
        gameData.player.resources.wood -= requiredResources.wood;
        gameData.player.resources.stone -= requiredResources.stone;

        const settlerIndex = units.findIndex((u) => u === settlerToFoundCity);
        if (settlerIndex !== -1) {
          units.splice(settlerIndex, 1);
          units = [...units];
        }

        if (gameData.player.units) {
          const gameDataSettlerIndex = gameData.player.units.findIndex(
            (u) =>
              u.id === settlerToFoundCity.id ||
              (u.position[0] === settlerToFoundCity.position[0] &&
                u.position[1] === settlerToFoundCity.position[1]),
          );

          if (gameDataSettlerIndex !== -1) {
            gameData.player.units.splice(gameDataSettlerIndex, 1);
          }
        }

        updateFogOfWarAroundPosition(x, y, 3);

        showToastNotification(
          `¡${newCityName} hiria sortu da arrakastaz!`,
          "success",
        );
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
      showToastNotification(
        "Errorea hiria sortzean: " + error.message,
        "error",
      );
    }
  }

  function checkForAttackTargets(unit) {
    if (!unit || unit.owner !== "player") {
      attackTargets = [];
      return;
    }

    // Modificación: permitir atacar si tiene movimientos restantes
    if (
      unit.status === "exhausted" ||
      (unit.remainingMovement !== undefined && unit.remainingMovement <= 0)
    ) {
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
    for (
      let y = Math.max(0, unitY - attackRange);
      y <= Math.min(mapHeight - 1, unitY + attackRange);
      y++
    ) {
      for (
        let x = Math.max(0, unitX - attackRange);
        x <= Math.min(mapWidth - 1, unitX + attackRange);
        x++
      ) {
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
        const enemyUnit = units.find(
          (u) =>
            u.owner === "ia" &&
            u.position &&
            Array.isArray(u.position) &&
            u.position[0] === x &&
            u.position[1] === y,
        );

        if (enemyUnit) {
          attackTargets.push(enemyUnit);
        }
      }
    }

    showAttackOptions = attackTargets.length > 0;

    // If we have attack targets, show a notification
    if (attackTargets.length > 0) {
      showToastNotification(
        `${attackTargets.length} etsai unitate eraso barrutian`,
        "info",
        2000,
      );
    }
  }

  function canAttack(unit) {
    if (ceasefireActive && ceasefireTurns > 0) {
      return false;
    }

    if (!unit || unit.owner !== "player") {
      return false;
    }

    // Cambio: permitir atacar si la unidad tiene movimientos restantes
    if (
      unit.status === "exhausted" ||
      (unit.remainingMovement !== undefined && unit.remainingMovement <= 0)
    ) {
      return false;
    }

    // Get unit position
    const [unitX, unitY] = unit.position;

    // Check for enemies within attack range (3 tiles)
    const attackRange = 3;

    // Quick check for nearby enemies
    for (const enemy of units) {
      if (
        enemy.owner !== "ia" ||
        !enemy.position ||
        !Array.isArray(enemy.position)
      )
        continue;

      const [enemyX, enemyY] = enemy.position;

      // Calculate Manhattan distance (number of steps)
      const manhattanDistance =
        Math.abs(enemyX - unitX) + Math.abs(enemyY - unitY);

      // Check if the enemy is within attack range
      if (manhattanDistance <= attackRange) {
        // Check if enemy is visible (not in fog of war)
        if (showFogOfWar) {
          if (grid[enemyY] && grid[enemyX] === FOG_OF_WAR.VISIBLE) {
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

    // Marcar la unidad como agotada después de atacar
    attackerCopy.status = "exhausted";
    attackerCopy.remainingMovement = 0;

    // Actualizar la unidad original en el arreglo units
    const unitIndex = units.findIndex((u) => u.id === attackingUnit.id);
    if (unitIndex !== -1) {
      units[unitIndex].status = "exhausted";
      units[unitIndex].remainingMovement = 0;
      units = [...units]; // Actualizar para reactividad
    }

    // Actualizar en gameData
    if (gameData && gameData.player && gameData.player.units) {
      const gameDataUnitIndex = gameData.player.units.findIndex(
        (u) => u.id === attackingUnit.id,
      );
      if (gameDataUnitIndex !== -1) {
        gameData.player.units[gameDataUnitIndex].status = "exhausted";
        gameData.player.units[gameDataUnitIndex].remainingMovement = 0;
      }
    }

    // Set up battle data
    const battleData = {
      attacker: attackerCopy,
      defender: defenderCopy,
      gameData: gameData,
    };

    // Store battle data for the battle page
    gameAPI.storeTemporaryData("battleData", battleData);

    // Navigate to battle page
    navigate("/battle");
  }

  function tryAttackFromCard(unit) {
    if (ceasefireActive && ceasefireTurns > 0) {
      showToastNotification(
        `Ezin duzu eraso su-etenean zehar (${ceasefireTurns} txanda geratzen).`,
        "warning",
      );
      return;
    }

    // Modificación: permitir atacar si no está exhausta y tiene movimientos
    if (!unit || unit.owner !== "player") {
      showToastNotification("Unitate honek ezin du orain eraso.", "warning");
      return;
    }

    // Verificar si tiene movimientos restantes
    if (
      unit.status === "exhausted" ||
      (unit.remainingMovement !== undefined && unit.remainingMovement <= 0)
    ) {
      showToastNotification(
        "Unitate honek ez du nahiko mugimendu puntu eraso egiteko.",
        "warning",
      );
      return;
    }

    // Buscar enemigos en rango
    checkForAttackTargets(unit);
    if (attackTargets.length === 0) {
      showToastNotification("Ez dago erasotzeko helburuak barrutian.", "info");
      showAttackOptions = false;
    } else {
      showAttackOptions = true;
    }
  }

  // Update function to check if a unit can negotiate with enemies
  function canNegotiate(unit) {
    if (!unit || unit.owner !== "player") {
      return false;
    }

    // Already exhausted units can't negotiate
    if (
      unit.status === "exhausted" ||
      (unit.remainingMovement !== undefined && unit.remainingMovement <= 0)
    ) {
      return false;
    }

    // Get unit position
    const [unitX, unitY] = unit.position;

    // Check for enemies within negotiation range (2 tiles)
    const negotiationRange = 2;

    // Quick check for nearby enemies
    for (const enemy of units) {
      if (
        enemy.owner !== "ia" ||
        !enemy.position ||
        !Array.isArray(enemy.position)
      )
        continue;

      const [enemyX, enemyY] = enemy.position;

      // Calculate Manhattan distance (number of steps)
      const manhattanDistance =
        Math.abs(enemyX - unitX) + Math.abs(enemyY - unitY);

      // Check if the enemy is within negotiation range
      if (manhattanDistance <= negotiationRange) {
        // If fog of war is disabled, all enemies in range can be negotiated with
        if (!showFogOfWar) {
          return true;
        }

        // Check if enemy is visible (not in fog of war)
        if (grid[enemyY] && grid[enemyY][enemyX] === FOG_OF_WAR.VISIBLE) {
          return true;
        }
      }
    }

    return false;
  }

  function openNegotiation(unit) {
    if (!canNegotiate(unit)) {
      showToastNotification(
        "Etsai unitate batetik 2 laukira egon behar zara negoziatzeko.",
        "warning",
      );
      return;
    }

    negotiationUnit = unit;
    showNegotiationModal = true;
    negotiationResult = null;
  }

  function closeNegotiation() {
    showNegotiationModal = false;
    negotiationUnit = null;
    negotiationResult = null;
  }

  function handleNegotiationResult(event) {
    negotiationResult = event.detail;
    if (negotiationResult && negotiationResult.accepted) {
      // Actualiza recursos y alto el fuego desde la sesión (el backend ya lo hizo)
      gameAPI.getCurrentGame().then((updatedGame) => {
        if (updatedGame) {
          gameData = updatedGame;
          ceasefireTurns = updatedGame.ceasefire_turns || 0;
          ceasefireActive =
            !!updatedGame.ceasefire_active && ceasefireTurns > 0;
          showToastNotification(
            `¡Negoziaketa arrakastatsua! Su-etena ${ceasefireTurns} txanda zehar.`,
            "success",
          );
        }
      });
      showNegotiationModal = false;
    }
  }

  async function processAIActions(actions, reasoning) {
    if (!actions || actions.length === 0) return;

    processingAITurn = true;
    aiActions = actions;
    aiActionIndex = 0;
    aiTurnReasoning = reasoning || "IA mugimendu estrategikoak egiten ari da";

    showToastNotification("IA txanda ikusten...", "info", 2000);

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

      console.log(
        `Processing AI action ${i + 1}/${actions.length}:`,
        currentAIAction,
      );

      // Center map on the action location
      if (currentAIAction.position && Array.isArray(currentAIAction.position)) {
        if (
          currentAIAction.type === "movement" &&
          currentAIAction.target_position
        ) {
          // For movement actions, center between positions
          const [startX, startY] = currentAIAction.position;
          const [endX, endY] = currentAIAction.target_position;

          // Calculate midpoint and force immediate camera update
          const midX = (startX + endX) / 2;
          const midY = (startY + endY) / 2;
          console.log(
            `Centering camera on movement midpoint: [${midX}, ${midY}]`,
          );

          offsetX = window.innerWidth / 2 - midX * tileSize * zoomLevel;
          offsetY = window.innerHeight / 2 - midY * tileSize * zoomLevel;
        } else {
          // For other actions, center directly on position
          const [posX, posY] = currentAIAction.position;
          console.log(`Centering camera on position: [${posX}, ${posY}]`);

          offsetX = window.innerWidth / 2 - posX * tileSize * zoomLevel;
          offsetY = window.innerHeight / 2 - posY * tileSize * zoomLevel;
        }

        // Wait for camera to adjust
        await new Promise((resolve) => setTimeout(resolve, 800));
      }

      // Display action card
      aiActionDescription = getActionDescription(currentAIAction);
      showAIActionCard = true;

      // Process action visually
      await visualizeAIAction(currentAIAction);

      // Keep card visible for a moment
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Hide card between actions
      showAIActionCard = false;
      await new Promise((resolve) => setTimeout(resolve, 300));
    }

    try {
      await gameAPI.updateGameSession(gameData);
      console.log("AI turn changes saved to session");
      // --- NUEVO: Guardar el JSON del game en la sesión bajo la clave 'game' ---

      // --- FIN NUEVO ---
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
    showToastNotification("IAk bere txanda amaitu du", "success");
  }

  async function centerOnPlayerPosition() {
    let centerPosition = null;

    // First try to find the player's capital city
    const playerCity = cities.find((c) => !c.owner || c.owner === "player");
    if (playerCity) {
      if (Array.isArray(playerCity.position)) {
        centerPosition = playerCity.position;
      } else if (playerCity.position) {
        centerPosition = [playerCity.position.x, playerCity.position.y];
      }
    }

    // If no city found, try to find a player unit
    if (!centerPosition) {
      const playerUnit = units.find((u) => u.owner === "player");
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
      await new Promise((resolve) => setTimeout(resolve, 800));
    }
  }

  async function visualizeAIAction(action) {
    try {
      // Validar tipo de acción
      if (!action || !action.type) {
        console.warn("AI action missing type:", action);
        showToastNotification(
          "IA ekintza baliogabea (mota gabe)",
          "warning",
          1500,
        );
        return;
      }

      // Normalizar campos comunes
      const safeArray = (arr) =>
        Array.isArray(arr) && arr.length >= 2 ? arr : [0, 0];

      switch (action.type) {
        case "movement": {
          // Buscar unidad por ID, posición, o tipo+posición
          let unitIndex = -1;
          let unitCandidates = [];

          if (action.unit_id) {
            unitIndex = units.findIndex((u) => u.id === action.unit_id);
          }
          if (
            unitIndex === -1 &&
            action.position &&
            Array.isArray(action.position)
          ) {
            const [posX, posY] = safeArray(action.position);
            // Buscar por posición y owner
            unitCandidates = units.filter(
              (u) =>
                u.owner === "ia" &&
                u.position &&
                Array.isArray(u.position) &&
                u.position[0] === posX &&
                u.position[1] === posY,
            );
            if (unitCandidates.length === 1) {
              unitIndex = units.indexOf(unitCandidates[0]);
            } else if (unitCandidates.length > 1 && action.unit_id) {
              // Si hay varias, priorizar por tipo_id
              unitIndex = units.findIndex(
                (u) =>
                  u.owner === "ia" &&
                  u.position &&
                  Array.isArray(u.position) &&
                  u.position[0] === posX &&
                  u.position[1] === posY &&
                  (u.type_id === action.unit_id || u.name === action.unit_id),
              );
            }
          }

          if (unitIndex === -1) {
            console.warn(
              `[AI] Mugitzeko unitatea ez da aurkitu: id=${action.unit_id}, pos=${JSON.stringify(
                action.position,
              )}`,
            );
            showToastNotification(
              "IAk ez dagoen unitate bat mugitu nahi izan du",
              "info",
              1500,
            );
            return;
          }

          const unitToMove = units[unitIndex];

          // Validar target_position
          if (
            !action.target_position ||
            !Array.isArray(action.target_position) ||
            action.target_position.length < 2
          ) {
            console.warn(
              "[AI] Mugimendua target_position baliogabearekin:",
              action,
            );
            showToastNotification(
              "IAk unitate bat mugitu nahi izan du posizio baliogabe batera",
              "warning",
              1500,
            );
            return;
          }

          const [targetX, targetY] = safeArray(action.target_position);

          // Validar límites del mapa
          if (
            targetX < 0 ||
            targetY < 0 ||
            targetX >= mapWidth ||
            targetY >= mapHeight
          ) {
            console.warn(
              `[AI] Mugimendua mugatik kanpo: [${targetX},${targetY}]`,
            );
            showToastNotification(
              "IAk unitate bat mugitu nahi izan du mapatik kanpo",
              "warning",
              1500,
            );
            return;
          }

          // Validar agua
          if (
            terrain[targetY] &&
            terrain[targetY][targetX] === TERRAIN_TYPES.WATER
          ) {
            console.warn(`[AI] Mugimendua ur laukira: [${targetX},${targetY}]`);
            showToastNotification(
              "IAk unitate bat mugitu nahi izan du ur gainean",
              "info",
              1500,
            );
            return;
          }

          // Validar ocupación por otra unidad
          const occupied = units.some(
            (u, idx) =>
              idx !== unitIndex &&
              u.position &&
              Array.isArray(u.position) &&
              u.position[0] === targetX &&
              u.position[1] === targetY,
          );
          if (occupied) {
            console.warn(
              `[AI] Mugimendua okupatutako laukira: [${targetX},${targetY}]`,
            );
            showToastNotification(
              "IAk unitate bat mugitu nahi izan du laukira okupatu batera",
              "info",
              1500,
            );
            return;
          }

          // Validar ciudad en destino
          const cityAtTarget = cities.find(
            (city) =>
              (Array.isArray(city.position) &&
                city.position[0] === targetX &&
                city.position[1] === targetY) ||
              (city.position.x === targetX && city.position.y === targetY),
          );
          if (cityAtTarget) {
            console.warn(
              `[AI] Mugimendua hiria duen laukira: [${targetX},${targetY}]`,
            );
            showToastNotification(
              "IAk unitate bat mugitu nahi izan du hiria duen laukira",
              "info",
              1500,
            );
            return;
          }

          // Realizar movimiento
          unitToMove.position = [targetX, targetY];
          unitToMove.remainingMovement =
            action.state_after?.remainingMovement ?? unitToMove.movement ?? 2;
          unitToMove.status = action.state_after?.status ?? "moved";
          units[unitIndex] = unitToMove;
          console.warn("EPAAAAAAAAA")
          const iaUnitIndex = gameData.ia.units.findIndex(
            (u) =>
              Array.isArray(u.position) &&
              Array.isArray(action.state_before.position) &&
              u.position[0] === action.state_before.position[0] &&
              u.position[1] === action.state_before.position[1],
          );

          if (iaUnitIndex !== -1) {
            gameData.ia.units[iaUnitIndex].position = [targetX, targetY];
            gameData.ia.units[iaUnitIndex].remainingMovement =
              unitToMove.remainingMovement;
            gameData.ia.units[iaUnitIndex].status = unitToMove.status;
          } else {
            console.warn(
              "Could not find AI unit to update in gameData.ia.units",
            );
          }

          console.log("IAren txanda, hemen dago gameData:", gameData);

          updateFogOfWarAroundPosition(targetX, targetY, 2);
          refreshSelectedUnitInfo();
          break;
        }

        case "attack": {
          // Buscar atacante y objetivo igual que en movement
          let attackerIndex = -1;
          if (action.unit_id) {
            attackerIndex = units.findIndex((u) => u.id === action.unit_id);
          }
          if (
            attackerIndex === -1 &&
            action.position &&
            Array.isArray(action.position)
          ) {
            const [posX, posY] = safeArray(action.position);
            attackerIndex = units.findIndex(
              (u) =>
                u.owner === "ia" &&
                u.position &&
                Array.isArray(u.position) &&
                u.position[0] === posX &&
                u.position[1] === posY,
            );
          }

          let targetIndex = -1;
          if (action.target_unit_id) {
            targetIndex = units.findIndex(
              (u) => u.id === action.target_unit_id,
            );
          }
          if (
            targetIndex === -1 &&
            action.target_position &&
            Array.isArray(action.target_position)
          ) {
            const [targetX, targetY] = safeArray(action.target_position);
            targetIndex = units.findIndex(
              (u) =>
                u.owner === "player" &&
                u.position &&
                Array.isArray(u.position) &&
                u.position[0] === targetX &&
                u.position[1] === targetY,
            );
          }

          if (attackerIndex === -1 || targetIndex === -1) {
            console.warn(
              `[AI] Erasotzaile edo defendatzailea ez da aurkitu erasoan:`,
              action,
            );
            showToastNotification(
              "IAk eraso egin nahi izan du baina unitatea ez da aurkitu",
              "info",
              1500,
            );
            return;
          }

          // Simular ataque (puedes mejorar lógica según tu juego)
          const attacker = units[attackerIndex];
          const defender = units[targetIndex];

          attacker.status = action.state_after?.status ?? "exhausted";
          attacker.remainingMovement =
            action.state_after?.remainingMovement ?? 0;
          attacker.health = action.state_after?.health ?? attacker.health;

          // Aplicar daño al defensor si viene en la acción
          if (
            action.target_state_after &&
            action.target_state_after.health !== undefined
          ) {
            defender.health = action.target_state_after.health;
            if (defender.health <= 0) {
              units.splice(targetIndex, 1);
              showToastNotification("Zure unitatea suntsitu da!", "error");
            } else {
              showToastNotification(
                `Zure unitatea erasotu da! Osasun geratzen: ${defender.health}`,
                "warning",
              );
            }
          } else {
            showToastNotification("IAk erasotu du!", "warning");
          }

          units = [...units];
          refreshSelectedUnitInfo();
          break;
        }

        case "construction": {
          // Buscar colono por ID o posición
          let builderIndex = -1;
          if (action.unit_id) {
            builderIndex = units.findIndex((u) => u.id === action.unit_id);
          }
          if (
            builderIndex === -1 &&
            action.position &&
            Array.isArray(action.position)
          ) {
            const [posX, posY] = safeArray(action.position);
            builderIndex = units.findIndex(
              (u) =>
                u.owner === "ia" &&
                u.position &&
                Array.isArray(u.position) &&
                u.position[0] === posX &&
                u.position[1] === posY &&
                (u.type_id === "settler" ||
                  u.name?.toLowerCase() === "settler"),
            );
          }
          if (builderIndex === -1) {
            console.warn("[AI] Ez da aurkitu hiria sortzeko kolonoa:", action);
            showToastNotification(
              "IAk hiria sortu nahi izan du kolono gabe",
              "info",
              1500,
            );
            return;
          }

          // Validar que no haya ciudad ya en esa posición
          const [cityX, cityY] = safeArray(action.position);
          const cityExists = cities.some(
            (c) =>
              (Array.isArray(c.position) &&
                c.position[0] === cityX &&
                c.position[1] === cityY) ||
              (c.position.x === cityX && c.position.y === cityY),
          );
          if (cityExists) {
            console.warn(
              "[AI] Jada hiria dago posizio horretan:",
              action.position,
            );
            showToastNotification(
              "IAk hiria sortu nahi izan du jada hiria dagoen lekuan",
              "info",
              1500,
            );
            return;
          }

          // Crear ciudad
          const newCity = {
            id: `city_${Date.now()}`,
            name: action.city_name || `IA Hiria ${Date.now()}`,
            position: [cityX, cityY],
            owner: "ia",
            population: 1,
          };
          cities = [...cities, newCity];
          units.splice(builderIndex, 1);
          units = [...units];
          updateFogOfWarAroundPosition(cityX, cityY, 3);
          if (gameData.ia && Array.isArray(gameData.ia.cities)) {
            gameData.ia.cities = [...gameData.ia.cities, newCity];
          }
          showToastNotification(`IAk hiria sortu du: ${newCity.name}`, "info");
          break;
        }

        case "city_production": {
          // Robustez: verificar campos mínimos
          if (!action.city_id || !action.action || !action.item_id) {
            console.warn("[AI] Ekintza city_production osatu gabe:", action);
            showToastNotification(
              "IAk hiriko ekoizpen osatu gabea bidali du",
              "info",
              1500,
            );
            return;
          }
          // Buscar ciudad por ID o posición
          let city = cities.find(
            (c) =>
              c.owner === "ia" &&
              (c.id === action.city_id ||
                (Array.isArray(c.position) &&
                  action.position &&
                  c.position[0] === action.position[0] &&
                  c.position[1] === action.position[1])),
          );
          if (!city) {
            console.warn("[AI] IA hiria ez da aurkitu ekoizpenerako:", action);
            showToastNotification(
              "IAk ekoiztu nahi izan du existitzen ez den hirian",
              "info",
              1500,
            );
            return;
          }
          let turns_remaining = 0;
          if (action.action == "train") {
            turns_remaining = gameAPI.getTroopType(action.item_id).turns;
          } else if (action.action == "build") {
            turns_remaining = gameAPI.getBuildingCost(action.item_id).turns;
          } else if (action.action == "research") {
            turns_remaining = gameAPI.getTechnologyCost(action.item_id).turns;
          } else {
            console.warn(
              "[AI] Ekoizpen ekintza ez da onartzen:",
              action.action,
            );
            showToastNotification(
              "IAk ekoizpen ekintza ez onartua egin nahi izan du",
              "info",
              1500,
            );
            return;
          }
          city.production = {
            current_item: action.item_id,
            turns_remaining: turns_remaining || 3,
          };
          cities = cities.filter((c) => c.id !== city.id);
          cities = [...cities, city];
          gameData.ia.cities = gameData.ia.cities.filter(
            (c) => c.id !== city.id,
          );
          gameData.ia.cities = [...gameData.ia.cities, city];
          gameAPI.updateGameSession(gameData);
          console.log("Hiriaren ekoizpena eguneratua:", city);
          break;
        }

        default:
          console.warn("[AI] Ekintza ez da onartzen:", action.type, action);
          showToastNotification(
            `IAk ekintza ezezaguna egin du: ${action.type}`,
            "info",
            1500,
          );
      }
    } catch (error) {
      console.error("Error visualizing AI action:", error, action);
      showToastNotification("Errorea IA ekintza prozesatzean", "error", 2000);
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  function getActionDescription(action) {
    // Get a unit description based on type, id, or position
    function getUnitDescription(unitId, position) {
      // If we have a valid ID that's not position-based, use it
      if (
        unitId &&
        unitId !== "null" &&
        unitId !== "undefined" &&
        !unitId.startsWith("unit-")
      ) {
        return unitId.replace(/_/g, " ");
      }

      // Otherwise, try to find what unit is at this position and use its type
      if (position && Array.isArray(position) && position.length >= 2) {
        const unitAtPosition = units.find(
          (u) =>
            u.position &&
            Array.isArray(u.position) &&
            u.position[0] === position[0] &&
            u.position[1] === position[1] &&
            u.owner === "ia",
        );

        if (unitAtPosition) {
          // Prioritize showing the unit type in the UI
          const unitType = unitAtPosition.type_id || "ezezaguna";

          // Return a user-friendly name based on unit type
          switch (unitType.toLowerCase()) {
            case "warrior":
              return "gerraria";
            case "archer":
              return "arkularia";
            case "settler":
              return "kolonoa";
            case "cavalry":
              return "zaldizkoa";
            case "builder":
              return "eraikitzailea";
            default:
              return unitType;
          }
        }

        // Fallback to generic description without showing coordinates
        return "unitatea";
      }

      return "unitate ezezaguna";
    }

    switch (action.type) {
      case "movement":
        const unitName = getUnitDescription(action.unit_id, action.position);
        return `La ${unitName} se mueve de [${action.position[0]},${action.position[1]}] a [${action.target_position[0]},${action.target_position[1]}]`;

      case "attack":
        const attackerName = getUnitDescription(
          action.unit_id,
          action.position,
        );
        const targetName = getUnitDescription(
          action.target_unit_id,
          action.target_position,
        );
        return `La ${attackerName} ataca a tu unidad ${targetName}`;

      case "construction":
        if (action.building === "city") {
          const builderName = getUnitDescription(
            action.unit_id,
            action.position,
          );
          return `El colono funda una nueva ciudad${action.city_name ? ": " + action.city_name : ""}`;
        }
        return `La IA construye ${action.building || "una estructura"}`;

      default:
        return `La IA realiza una acción: ${action.type}`;
    }
  }

  function ensureAIUnitsExist() {
    if (!gameData || !gameData.ia || !Array.isArray(gameData.ia.units)) return;

    // Get current AI units by ID
    const currentAIUnitIds = units
      .filter((u) => u.owner === "ia")
      .map((u) => u.id);

    // Add any missing AI units
    for (const iaUnit of gameData.ia.units) {
      if (!currentAIUnitIds.includes(iaUnit.id)) {
        console.log(`Adding missing AI unit to display: ${iaUnit.id}`);

        const newUnit = {
          ...iaUnit,
          owner: "ia",
        };

        units = [...units, newUnit];
      }
    }
  }

  function centerMapOnPosition(x, y) {
    const containerWidth = window.innerWidth;
    const containerHeight = window.innerHeight;

    offsetX = containerWidth / 2 - x * tileSize * zoomLevel;
    offsetY = containerHeight / 2 - y * tileSize * zoomLevel;
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
      showToastNotification(
        "Unitatea kokatu behar duzu txanda amaitu aurretik",
        "warning",
        5000,
      );

      // Re-center on the producing city to help player locate where to place the unit
      if (producingCity) {
        const cityPos = Array.isArray(producingCity.position)
          ? producingCity.position
          : [producingCity.position.x, producingCity.position.y];
        centerMapOnPosition(cityPos[0], cityPos[1]);

        // Recalculate city area to make it visible
        calculateCityArea(producingCity);
      }
      return;
    }

    // Set processing flag to true at the beginning of the turn
    processingAITurn = true;

    try {
      console.log(
        `Player ${gameData.current_player} ending turn ${gameData.turn}.`,
      );

      // Handle player city production before switching to AI turn
      const completedProductions = await processCityProduction();

      // If we just completed a production that requires unit placement, block turn end
      if (awaitingUnitPlacement && newlyProducedUnit) {
        showToastNotification(
          "Unitate berria ekoiztu da. Kokatu behar duzu txanda amaitu aurretik",
          "success",
          5000,
        );
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
        await new Promise((resolve) => setTimeout(resolve, 1500));
      }

      // Generate and distribute resources for player cities before ending player turn
      const playerResources = await calculateAndDistributeResources("player");
      if (
        playerResources &&
        Object.values(playerResources).some((val) => val > 0)
      ) {
        showResourceGenerationNotification(playerResources, "player");
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }
      gameData.player = gameAPI.increaseCityPopulation(gameData.player);
      cities = [...gameData.player.cities, ...gameData.ia.cities];

      // --- NUEVO: Decrementar alto el fuego ---
      if (ceasefireActive && ceasefireTurns > 0) {
        ceasefireTurns--;
        if (ceasefireTurns <= 0) {
          ceasefireActive = false;
          ceasefireTurns = 0;
          if (gameData) {
            gameData.ceasefire_turns = 0;
            gameData.ceasefire_active = false;
          }
          showToastNotification("Bakea amaitu da.", "info");
        } else {
          if (gameData) {
            gameData.ceasefire_turns = ceasefireTurns;
            gameData.ceasefire_active = true;
          }
          showToastNotification(
            `Bakea geratzen ${ceasefireTurns} txanda.`,
            "info",
          );
        }
      }

      gameData.current_player = "ia";
      currentPlayer.set(gameData.current_player);
      gameAPI.updateGameSession(gameData);
      showToastNotification("IA Txanda - Prozesatzen...", "info");

      // Process AI city production before AI actions
      const aiCompletedProductions = await processAICityProduction();

      try {
        console.log("Requesting AI action...");
        const aiResponse = await gameAPI.getAIAction(gameData);
        console.log("AI Response:", aiResponse);

        if (aiResponse && aiResponse.actions && aiResponse.actions.length > 0) {
          // Show AI production notifications if there were any
          if (aiCompletedProductions && aiCompletedProductions.length > 0) {
            showToastNotification(
              `IAk ${aiCompletedProductions.length} ekoizpen amaitu ditu`,
              "info",
              3000,
            );
          }

          await processAIActions(aiResponse.actions, aiResponse.reasoning);
        } else {
          showToastNotification(
            "IAk bere txanda amaitu du (ekintzarik gabe)",
            "info",
          );
          await new Promise((resolve) => setTimeout(resolve, 1000));
        }
      } catch (error) {
        console.error("Error getting AI action:", error);
        showToastNotification("Errorea IA txanda prozesatzean", "error");
        await new Promise((resolve) => setTimeout(resolve, 1000));
      }

      // Generate and distribute resources for AI cities after AI turn
      const aiResources = await calculateAndDistributeResources("ia");
      if (aiResources && Object.values(aiResources).some((val) => val > 0)) {
        // Optional: Show notification about AI resources (or keep it hidden)
        console.log("AI resources generated:", aiResources);
      }

      // --- NUEVO: Incrementar población de ciudades de la IA ---
      gameData.ia = gameAPI.increaseCityPopulation(gameData.ia);

      await new Promise((resolve) => setTimeout(resolve, 500));

      gameData.current_player = "player";
      gameData.turn = (gameData.turn || 0) + 1;
      currentPlayer.set(gameData.current_player);
      currentTurn.set(gameData.turn);

      const aiUnits = units.filter((unit) => unit.owner === "ia");

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

        console.log(
          "Units after turn end:",
          units.length,
          "- Player:",
          units.filter((u) => u.owner === "player").length,
          "AI:",
          units.filter((u) => u.owner === "ia").length,
        );
      }

      selectedUnit = null;
      selectedUnitInfo = null;
      validMoveTargets = [];

      // If unlimited movements cheat is active, refresh all player units' movement at the end of AI turn
      if (
        unlimitedMovementsActive &&
        gameData &&
        gameData.player &&
        Array.isArray(gameData.player.units)
      ) {
        gameData.player.units.forEach((unit, index) => {
          unit.status = "ready";
          unit.remainingMovement = unit.movement || 2;
        });
      }

      try {
        await gameAPI.updateGameSession(gameData);
        console.log(`Game session updated for Turn ${gameData.turn}.`);
        showToastNotification(
          `Txanda ${gameData.turn} - Zure txanda`,
          "success",
        );
      } catch (error) {
        console.error(
          "Failed to update game session after ending turn:",
          error,
        );
        showToastNotification(
          "Errorea txanda datuak zerbitzarian gordetzean.",
          "error",
        );
      }
    } catch (error) {
      console.error("Unexpected error during end turn:", error);
      showToastNotification("Errore ezustekoa txanda amaitzean", "error");
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
      // Process normal city production
      if (
        city.production &&
        city.production.current_item &&
        city.production.turns_remaining > 0
      ) {
        // Decrease turns remaining
        city.production.turns_remaining--;

        // If production is complete
        if (city.production.turns_remaining <= 0) {
          try {
            const itemId = city.production.current_item;
            const itemType = city.production.itemType || "troop"; // Default to "troop" for backward compatibility

            // Get the city position
            const cityPosition = Array.isArray(city.position)
              ? [...city.position]
              : [city.position.x, city.position.y];

            // Handle different item types differently
            if (itemType === "troop") {
              // Get complete troop info from API
              let troopInfo = null;
              try {
                // Get full troop details from API
                const allTroopTypes = await gameAPI.getTroopTypes();
                troopInfo = allTroopTypes.find(
                  (t) => t.type_id === itemId || t.id === itemId,
                );

                if (!troopInfo) {
                  // Fallback to direct API call if not found in list
                  troopInfo = await gameAPI.getTroopType(itemId);
                }
              } catch (e) {
                console.warn(
                  "Could not get troop info from API, using defaults",
                  e,
                );
                troopInfo = {
                  name: itemId,
                  type_id: itemId,
                  movement: 2,
                  health: 100,
                  attack: 10,
                  defense: 5,
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
                owner: "player",
                status: "ready",
                // Ensure these critical properties exist
                movement: troopInfo.movement || 2,
                remainingMovement: troopInfo.movement || 2,
                health: troopInfo.health || 100,
                attack: troopInfo.attack || 10,
                defense: troopInfo.defense || 5,
              };

              // Set up the placement mode
              newlyProducedUnit = tempUnit;
              producingCity = city;
              awaitingUnitPlacement = true;

              // Calculate city area for placement UI
              calculateCityArea(city);

              // Show very prominent notification
              const notificationMessage = `${city.name} unitatearen ekoizpena amaitu du ${tempUnit.name || itemId}. Kokatu unitatea mapan!`;
              showToastNotification(notificationMessage, "success", 8000);

              // Center map on city to help player see where to place unit
              centerMapOnPosition(cityPosition[0], cityPosition[1]);

              // Add to completed productions for reference
              completedProductions.push({
                type: "troop",
                name: tempUnit.name || itemId,
                city: city.name,
                requiresPlacement: true,
                message: notificationMessage,
              });

              // Break out of the loop - handle one production at a time
              break;
            } else if (itemType === "building") {
              // Get the production type to determine if we're building or upgrading
              const productionType = city.production.production_type || "build";

              // Get complete building details
              let buildingDetails;
              try {
                buildingDetails = await gameAPI.getBuildingType(itemId);
              } catch (apiError) {
                console.error(
                  `API Error getting building type ${itemId}:`,
                  apiError,
                );
                buildingDetails = {
                  type_id: itemId,
                  name: `Building ${itemId}`,
                };
              }

              if (productionType === "build" || productionType === 1) {
                // Create a new building object with ALL properties from the API
                const newBuilding = {
                  // Copy all properties from the building type
                  ...buildingDetails,
                  // Add runtime-specific properties
                  id: `${itemId}_${Date.now()}`,
                  type_id: itemId,
                  constructed_at: gameData.turn,
                  level: 1, // Ensure new buildings start at level 1
                };

                // Add building directly to the city
                if (!city.buildings) {
                  city.buildings = [];
                }
                city.buildings.push(newBuilding);

                // Show prominent notification for building completion
                const notificationMessage = `${city.name} eraikinaren ekoizpena amaitu du ${buildingDetails.name || itemId}.`;
                showToastNotification(notificationMessage, "success", 6000);

                // Add to completed productions
                completedProductions.push({
                  type: "building",
                  name: buildingDetails.name || itemId,
                  city: city.name,
                  requiresPlacement: false,
                  message: notificationMessage,
                });
              } else if (productionType === "upgrade" || productionType === 2) {
                // UPGRADE EXISTING BUILDING

                // Find the existing building in the city
                let existingBuilding = null;
                let buildingIndex = -1;

                if (city.buildings && city.buildings.length > 0) {
                  buildingIndex = city.buildings.findIndex(
                    (building) =>
                      building.type_id === itemId ||
                      building.id === itemId ||
                      building.name?.toLowerCase() ===
                        buildingDetails.name?.toLowerCase() ||
                      building.type?.toLowerCase() ===
                        buildingDetails.type?.toLowerCase(),
                  );

                  if (buildingIndex !== -1) {
                    existingBuilding = city.buildings[buildingIndex];
                  }
                }

                if (!existingBuilding) {
                  console.error(
                    `Could not find a building of type ${itemId} to upgrade in city ${city.name}`,
                  );
                  showToastNotification(
                    `Errorea: Eraikin bat ez da aurkitu ${city.name} hobetzeko`,
                    "error",
                  );
                } else {
                  // Make a copy of the building to ensure reactivity
                  const upgradedBuilding = { ...existingBuilding };

                  // Increment the level
                  upgradedBuilding.level = (upgradedBuilding.level || 1) + 1;

                  // Get the level_upgrade amount
                  const levelUpgradeAmount = buildingDetails.level_upgrade || 1;

                  // Update output resources if they exist
                  if (upgradedBuilding.output) {
                    for (const resource in upgradedBuilding.output) {
                      upgradedBuilding.output[resource] += levelUpgradeAmount;
                    }
                  } else if (buildingDetails.output) {
                    // Initialize output if it doesn't exist
                    upgradedBuilding.output = { ...buildingDetails.output };
                  }

                  // Update the building in the city
                  city.buildings[buildingIndex] = upgradedBuilding;

                  // Show a prominent notification
                  const notificationMessage = `¡${city.name} eraikinaren hobekuntza amaitu du ${upgradedBuilding.name}!`;
                  showToastNotification(notificationMessage, "success", 8000);

                  // Add to completed productions for reference
                  completedProductions.push({
                    type: "building",
                    name: upgradedBuilding.name,
                    city: city.name,
                    message: notificationMessage,
                  });
                }

                // Clear the city's production
                city.production = {
                  current_item: null,
                  turns_remaining: 0,
                  itemType: null,
                  production_type: null,
                };
              }
            }
          } catch (error) {
            console.error(
              `Error completing production in ${city.name}:`,
              error,
            );
            // In case of error, still clear the production
            city.production = {
              current_item: null,
              turns_remaining: 0,
              itemType: null,
              production_type: null,
            };
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
      if (
        city.production &&
        city.production.current_item &&
        city.production.turns_remaining > 0
      ) {
        // Decrease turns remaining
        city.production.turns_remaining--;

        // If production is complete
        if (city.production.turns_remaining <= 0) {
          try {
            const itemId = city.production.current_item;
            const itemType = city.production.itemType || "troop";

            // Get the city position
            const cityPosition = Array.isArray(city.position)
              ? [...city.position]
              : [city.position.x, city.position.y];

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
                  const fullTroopType = allTroopTypes.find(
                    (t) => t.type_id === itemId,
                  );
                  if (fullTroopType) {
                    // Merge the properties, keeping the position from the first call
                    troopInfo = {
                      ...fullTroopType,
                      position: troopInfo.position || validPos,
                    };
                  }
                }
              } catch (e) {
                console.warn(
                  "AI couldn't get troop details, using defaults",
                  e,
                );
                troopInfo = {
                  name: itemId,
                  type_id: itemId,
                  movement: 2,
                  health: 100,
                  attack: 10,
                  defense: 5,
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
                position:
                  troopInfo.position || findValidPositionNearCity(cityPosition),
                owner: "ia",
                status: "ready",
                // Ensure these critical properties exist
                movement: troopInfo.movement || 2,
                remainingMovement: troopInfo.movement || 2,
                health: troopInfo.health || 100,
                attack: troopInfo.attack || 10,
                defense: troopInfo.defense || 5,
              };

              // Add to game data and units array
              if (!gameData.ia.units) {
                gameData.ia.units = [];
              }

              gameData.ia.units.push(newUnit);
              units = [...units, newUnit];

              // Add to completed productions
              completedProductions.push({
                type: "troop",
                name: troopInfo.name || itemId,
                city: city.name,
                message: `IA hiriak unitatearen ekoizpena amaitu du ${troopInfo.name || itemId}`,
              });
            } else if (itemType === "building") {
              // Get complete building details
              let buildingDetails;
              try {
                buildingDetails = await gameAPI.getBuildingType(itemId);
              } catch (apiError) {
                buildingDetails = {
                  type_id: itemId,
                  name: `Building ${itemId}`,
                };
              }

              // Create a new building with ALL properties from the API
              const newBuilding = {
                // Copy all properties from the building type
                ...buildingDetails,
                // Add runtime-specific properties
                id: `${itemId}_${Date.now()}`,
                type_id: itemId,
                constructed_at: gameData.turn,
              };

              // Add building to city
              if (!city.buildings) {
                city.buildings = [];
              }
              city.buildings.push(newBuilding);

              // Add to completed productions
              completedProductions.push({
                type: "building",
                name: buildingDetails.name || itemId,
                city: city.name,
                message: `IA hiriak eraikinaren ekoizpena amaitu du ${buildingDetails.name || itemId}`,
              });
            }

            // Clear the city's production regardless of type
            city.production.current_item = null;
            city.production.turns_remaining = 0;
            city.production.itemType = null;
          } catch (error) {
            console.error(
              `Error completing production in AI city ${city.name}:`,
              error,
            );
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
    if (playerType !== "player") return;

    let resourceMessage = "Sortutako baliabideak: ";
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
      stone: 0,
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
      const outcome =
        building.output || getDefaultBuildingOutcome(building.type_id);

      // Apply resource generation based on building type and available resources
      switch (building.type_id) {
        case "farm":
        case "granary":
          // Each farm/granary building multiplies its food outcome by the number of food tiles
          if (outcome.food && resourceCounts.food > 0) {
            const foodGenerated = outcome.food * resourceCounts.food;
            generatedResources.food += foodGenerated;
            console.log(
              `${city.name}: ${building.type_id} generated ${foodGenerated} food from ${resourceCounts.food} food tiles`,
            );
          }
          break;
        case "Gold mine":
          // Each mine building multiplies its gold outcome by the number of gold tiles
          if (outcome.gold && resourceCounts.gold > 0) {
            const goldGenerated = outcome.gold * resourceCounts.gold;
            generatedResources.gold += goldGenerated;
            console.log(
              `${city.name}: ${building.type_id} generated ${goldGenerated} gold from ${resourceCounts.gold} gold tiles`,
            );
          }
          break;
        case "Sawmill":
          // Each sawmill building multiplies its wood outcome by the number of wood tiles
          if (outcome.wood && resourceCounts.wood > 0) {
            const woodGenerated = outcome.wood * resourceCounts.wood;
            generatedResources.wood += woodGenerated;
            console.log(
              `${city.name}: ${building.type_id} generated ${woodGenerated} wood from ${resourceCounts.wood} wood tiles`,
            );
          }
          break;
        case "Iron mine":
          // Each forge/iron mine building multiplies its iron outcome by the number of iron tiles
          if (outcome.iron && resourceCounts.iron > 0) {
            const ironGenerated = outcome.iron * resourceCounts.iron;
            generatedResources.iron += ironGenerated;
            console.log(
              `${city.name}: ${building.type_id} generated ${ironGenerated} iron from ${resourceCounts.iron} iron tiles`,
            );
          }
          break;
        case "Quarry":
          // Each quarry building multiplies its stone outcome by the number of stone tiles
          if (outcome.stone && resourceCounts.stone > 0) {
            const stoneGenerated = outcome.stone * resourceCounts.stone;
            generatedResources.stone += stoneGenerated;
            console.log(
              `${city.name}: ${building.type_id} generated ${stoneGenerated} stone from ${resourceCounts.stone} stone tiles`,
            );
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
      stone: 0,
    };

    const player = playerType === "ia" ? gameData.ia : gameData.player;

    if (!player || !player.cities || player.cities.length === 0) {
      return null;
    }

    console.log(
      `Calculating resources for ${playerType}'s cities (${player.cities.length} cities)`,
    );

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

    console.log(
      `Total resources generated for ${playerType}:`,
      resourcesGenerated,
    );

    // Add resources to player
    if (!player.resources) {
      player.resources = { food: 0, gold: 0, wood: 0, iron: 0, stone: 0 };
    }

    player.resources.food =
      (player.resources.food || 0) + resourcesGenerated.food;
    player.resources.gold =
      (player.resources.gold || 0) + resourcesGenerated.gold;
    player.resources.wood =
      (player.resources.wood || 0) + resourcesGenerated.wood;
    player.resources.iron =
      (player.resources.iron || 0) + resourcesGenerated.iron;
    player.resources.stone =
      (player.resources.stone || 0) + resourcesGenerated.stone;

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
      stone: 0,
    };

    if (!city || !city.area) {
      return resourceCounts;
    }

    // Get city position
    const cityPosX = Array.isArray(city.position)
      ? city.position[0]
      : city.position.x;
    const cityPosY = Array.isArray(city.position)
      ? city.position[1]
      : city.position.y;

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
          // Get terrain type for this tile - FIX: Use proper array indexing
          const terrainType = terrain[tileY] && terrain[tileY][tileX];

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

        if (!saveResult || saveResult.success === false) {
          throw new Error(saveResult?.message || "Unknown error saving game");
        }

        console.log("Game saved and session persisted.");

        showToastNotification("Zure jokoa arrakastaz gorde da!");

        setTimeout(() => {
          endGame();
          navigate("/home");
        }, 1500);
      } else {
        endGame();
        navigate("/home");
      }
    } catch (error) {
      console.error("Error saving and exiting game:", error);

      showToastNotification(
        `Errorea jokoa gordetzean: ${error.message}. Berriro saiatzen...`,
        "error",
        2000,
      );

      try {
        await new Promise((resolve) => setTimeout(resolve, 1000));
        await gameAPI.saveCurrentGameSession();
        showToastNotification(
          "Jokoa arrakastaz gorde da berriro saiatzean!",
          "success",
        );

        setTimeout(() => {
          endGame();
          navigate("/home");
        }, 1500);
      } catch (retryError) {
        showToastNotification(
          `Ezin da jokoa gorde. Irten gabe gordetzean.`,
          "error",
          2000,
        );
        setTimeout(() => {
          endGame();
          navigate("/home");
        }, 2000);
      }
    }
  }

  function exitWithoutSaving() {
    if (
      confirm(
        "Ziur zaude gorde gabe irten nahi duzula? Aurrerapen guztia galduko da.",
      )
    ) {
      endGame();
      navigate("/home");
    }
  }

  function calculateValidMoveTargets(startX, startY, movementPoints) {
    validMoveTargets = [];

    // If unlimited movements cheat is active, use a high movement range
    const movementRange = unlimitedMovementsActive
      ? 8 // Large value but not too large to avoid performance issues
      : Math.min(movementPoints, 2); // Normal limited movement

    // Check each tile within the movement range
    for (
      let y = Math.max(0, startY - movementRange);
      y <= Math.min(mapHeight - 1, startY + movementRange);
      y++
    ) {
      for (
        let x = Math.max(0, startX - movementRange);
        x <= Math.min(mapWidth - 1, startX + movementRange);
        x++
      ) {
        // Skip the current tile
        if (x === startX && y === startY) continue;

        // Calculate Manhattan distance (number of steps)
        const steps = Math.abs(x - startX) + Math.abs(y - startY);

        // If beyond movement range, skip
        if (steps > movementRange) continue;

        // Skip water tiles
        if (terrain[y] && terrain[y][x] === TERRAIN_TYPES.WATER) continue;

        // Check if the tile is already occupied by another unit
        const occupyingUnit = units.find(
          (u) =>
            u !== selectedUnit &&
            u.position &&
            Array.isArray(u.position) &&
            u.position[0] === x &&
            u.position[1] === y,
        );

        // Skip if occupied
        if (occupyingUnit) continue;

        // Check if the tile has a city
        const cityAtPosition = cities.find(
          (city) =>
            (city.position.x === x && city.position.y === y) ||
            (Array.isArray(city.position) &&
              city.position[0] === x &&
              city.position[1] === y),
        );

        // Skip if there's a city
        if (cityAtPosition) continue;

        // For unlimited movements, we don't need to check points
        if (unlimitedMovementsActive || movementPoints >= steps) {
          // Add valid target with special handling for unlimited movements
          validMoveTargets.push({
            x,
            y,
            remainingMovement: unlimitedMovementsActive
              ? movementPoints
              : movementPoints - steps,
          });
        }
      }
    }
  }

  async function moveUnitToPosition(unit, targetX, targetY) {
    if (movementInProgress) return;

    const occupyingUnit = units.find(
      (u) =>
        u !== unit &&
        u.position &&
        Array.isArray(u.position) &&
        u.position[0] === targetX &&
        u.position[1] === targetY,
    );

    if (occupyingUnit) {
      showToastNotification(
        `Ezin duzu unitatea mugitu laukira (${targetX}, ${targetY}). Beste unitate batek okupatzen du.`,
        "error",
      );
      return;
    }

    // Add check for city at target position
    const cityAtPosition = cities.find(
      (city) =>
        (city.position.x === targetX && city.position.y === targetY) ||
        (Array.isArray(city.position) &&
          city.position[0] === targetX &&
          city.position[1] === targetY),
    );

    if (cityAtPosition) {
      showToastNotification(
        `Ezin duzu unitatea mugitu laukira (${targetX}, ${targetY}). Hiri bat dago posizio horretan.`,
        "error",
      );
      return;
    }

    movementInProgress = true;

    try {
      const targetInfo = validMoveTargets.find(
        (target) => target.x === targetX && target.y === targetY,
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
        unitIndex = units.findIndex((u) => u.id === unit.id);
      }

      // If unit was not found by ID, find it by original position
      if (unitIndex === -1 && Array.isArray(unit.position)) {
        const [unitX, unitY] = unit.position;
        unitIndex = units.findIndex(
          (u) =>
            u === unit ||
            (u.position &&
              Array.isArray(u.position) &&
              u.position[0] === unitX &&
              u.position[1] === unitY &&
              u.owner === unit.owner &&
              u.type_id === unit.type_id),
        );
      }

      // Make absolutely sure we have the right unit before moving it
      if (unitIndex !== -1) {
        const unitToMove = units[unitIndex];
        const originalPosition = [...unitToMove.position];

        console.log(
          `Unitatea mugitzen ${unitToMove.type_id} [${originalPosition}] posiziotik [${targetX},${targetY}] posiziora`,
        );

        // Calculate the movement cost
        const movementCost =
          Math.abs(targetX - originalPosition[0]) +
          Math.abs(targetY - originalPosition[1]);

        if (unitToMove.remainingMovement === undefined) {
          unitToMove.remainingMovement = unitToMove.movement || 2;
        }

        if (
          !unlimitedMovementsActive &&
          unitToMove.remainingMovement < movementCost
        ) {
          showToastNotification(
            "Mugimendu baliogabea: ez dago nahiko mugimendu puntu",
            "error",
          );
          movementInProgress = false;
          return;
        }

        // Create a copy of the unit object to avoid reference issues
        const updatedUnit = { ...unitToMove };

        // Update unit position and movement points
        updatedUnit.position = [targetX, targetY];

        // Only decrease remaining movement if unlimited movements is not active
        if (!unlimitedMovementsActive) {
          updatedUnit.remainingMovement -= movementCost;
        }

        // Update unit status based on remaining movement or unlimited movement cheat
        if (!unlimitedMovementsActive && updatedUnit.remainingMovement <= 0) {
          updatedUnit.status = "exhausted";
        } else {
          updatedUnit.status = "moved";
        }

        // Update the unit in the array with our updated copy
        units[unitIndex] = updatedUnit;

        // Ensure reactivity by creating a new array
        units = [...units];

        // Update unit info panel if it's showing this unit
        if (
          selectedUnitInfo &&
          (selectedUnitInfo.id === updatedUnit.id || selectedUnitInfo === unit)
        ) {
          selectedUnitInfo = updatedUnit;
        }

        // Update game data
        if (
          gameData &&
          gameData.player &&
          Array.isArray(gameData.player.units)
        ) {
          const gameDataUnitIndex = gameData.player.units.findIndex(
            (u) =>
              (u.id && u.id === updatedUnit.id) ||
              (u.position &&
                Array.isArray(u.position) &&
                u.position[0] === originalPosition[0] &&
                u.position[1] === originalPosition[1] &&
                u.type_id === updatedUnit.type_id),
          );

          if (gameDataUnitIndex !== -1) {
            gameData.player.units[gameDataUnitIndex].position = [
              targetX,
              targetY,
            ];
            gameData.player.units[gameDataUnitIndex].status =
              updatedUnit.status;
            gameData.player.units[gameDataUnitIndex].remainingMovement =
              updatedUnit.remainingMovement;
          }
        }

        // Update fog of war around new position
        updateFogOfWarAroundPosition(targetX, targetY, 2);

        // Update selected unit reference to the updated unit
        selectedUnit = updatedUnit;

        // Actualiza las unidades de jugador en gameData antes de guardar
        if (gameData && gameData.player) {
          gameData.player.units = units.filter((u) => u.owner === "player");
        }
        if (gameData && gameData.ia) {
          gameData.ia.units = units.filter((u) => u.owner === "ia");
        }
        await gameAPI.updateGameSession(gameData);
        // --- FIN NUEVO ---
        // --- NUEVO: Refrescar la tarjeta de información de la tropa ---
        refreshSelectedUnitInfo();
        // --- FIN NUEVO ---

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
        showToastNotification(
          "Errorea unitatea mugitzean: unitatea ez da aurkitu",
          "error",
        );
      }
    } catch (error) {
      console.error("Error moving unit:", error);
      showToastNotification("Errorea unitatea mugitzean", "error");
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

    // --- MODIFICADO: NO mostrar el popup de ataque al hacer click en la unidad ---
    // El popup de ataque solo se muestra al pulsar el botón "Atacar" de la tarjeta

    // Check if the clicked position is an attack target (solo si showAttackOptions es true)
    if (attackingUnit && showAttackOptions) {
      const targetUnit = units.find(
        (u) =>
          u.owner === "ia" &&
          u.position &&
          Array.isArray(u.position) &&
          u.position[0] === x &&
          u.position[1] === y,
      );

      if (targetUnit && attackTargets.some((target) => target === targetUnit)) {
        initiateAttack(targetUnit);
        return;
      }
    }

    if (
      selectedUnit &&
      validMoveTargets.some((target) => target.x === x && target.y === y)
    ) {
      moveUnitToPosition(selectedUnit, x, y);
      return;
    }

    // Check if there's a city at the clicked position
    const cityAtPosition = cities.find(
      (city) =>
        (city.position.x === x && city.position.y === y) ||
        (Array.isArray(city.position) &&
          city.position[0] === x &&
          city.position[1] === y),
    );

    if (cityAtPosition) {
      if (
        cityAtPosition.owner === "ia" &&
        showFogOfWar &&
        grid[y] &&
        grid[y][x] !== FOG_OF_WAR.VISIBLE
      ) {
        // No mostrar nada, ni seleccionar la ciudad
        selectedCityInfo = null;
        selectedTile = null;
        selectedUnit = null;
        selectedUnitInfo = null;
        validMoveTargets = [];
        return;
      }
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

    const unitAtPosition = units.find(
      (unit) =>
        unit &&
        unit.position &&
        Array.isArray(unit.position) &&
        unit.position[0] === x &&
        unit.position[1] === y,
    );

    if (unitAtPosition) {
      selectedCityInfo = null; // Clear selected city
      selectedUnitInfo = unitAtPosition;
      selectedTile = null;

      if (unitAtPosition.owner === "ia") {
        showToastNotification(
          "Hau etsai unitate bat da. Ezin duzu kontrolatu.",
          "warning",
        );
        selectedUnit = null;
        validMoveTargets = [];
        return;
      }

      if (unitAtPosition.status === "exhausted") {
        showToastNotification(
          "Unitate honek dagoeneko agortu ditu bere mugimenduak txanda honetan.",
          "warning",
        );
        selectedUnit = null;
        validMoveTargets = [];
      } else {
        selectUnit(unitAtPosition);
      }
      // --- NO mostrar popup de ataque aquí ---
      return;
    } else {
      selectedUnit = null;
      selectedUnitInfo = null;
      selectedCityInfo = null; // Clear selected city
      validMoveTargets = [];
    }

    if (showFogOfWar && grid[y] && grid[y][x] === FOG_OF_WAR.HIDDEN) {
      selectedTile = {
        x,
        y,
        terrainName: "Ezezaguna (ez esploratua)",
        isExplored: false,
      };
      selectedUnit = null;
      selectedUnitInfo = null;
      selectedCityInfo = null;
      validMoveTargets = [];
      return; // IMPORTANTE: salir aquí para no seguir con la lógica normal
    }
  }

  function calculateCityArea(city) {
    cityAreaTiles = [];

    if (!city || !city.area) {
      return;
    }

    // Get city position
    const cityPosX = Array.isArray(city.position)
      ? city.position[0]
      : city.position.x;
    const cityPosY = Array.isArray(city.position)
      ? city.position[1]
      : city.position.y;

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
        showToastNotification(
          "Ezin duzu unitatea posizio horretan kokatu. Aukeratu beste laukia hiriaren eremuan.",
          "error",
        );
        return;
      }

      // Now that we have a valid position, get the FULL troop details with position
      try {
        // Here's where we call getTroopType with the position the player chose
        const position = [x, y];
        const troopDetails = await gameAPI.getTroopType(
          newlyProducedUnit.type_id,
          position,
        );

        // Update the unit with complete details from the API
        newlyProducedUnit.position = position;
        newlyProducedUnit.movement =
          troopDetails.movement || newlyProducedUnit.movement;
        newlyProducedUnit.remainingMovement =
          troopDetails.movement || newlyProducedUnit.movement;
        newlyProducedUnit.health =
          troopDetails.health || newlyProducedUnit.health;
        newlyProducedUnit.attack =
          troopDetails.attack || newlyProducedUnit.attack;
        newlyProducedUnit.defense =
          troopDetails.defense || newlyProducedUnit.defense;

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
      if (producingCity) {
        // FIXED: Completely reset the production object instead of just clearing fields
        producingCity.production = {
          current_item: null,
          turns_remaining: 0,
          itemType: null,
          production_type: null,
        };

        // Make sure the city in gameData is also updated
        if (gameData && gameData.player && gameData.player.cities) {
          const cityIndex = gameData.player.cities.findIndex(
            (c) => c.id === producingCity.id,
          );
          if (cityIndex !== -1) {
            gameData.player.cities[cityIndex].production =
              producingCity.production;
          }
        }
      }

      // Update the game state
      await gameAPI.updateGameSession(gameData);

      // Show a success notification
      showToastNotification(
        `¡${newlyProducedUnit.name} arrakastaz kokatu da!`,
        "success",
        4000,
      );

      // Clear the placement mode and city area highlighting
      awaitingUnitPlacement = false;
      newlyProducedUnit = null;
      producingCity = null;
      cityAreaTiles = [];
    } catch (error) {
      console.error("Error placing new unit:", error);
      showToastNotification("Errorea unitatea kokatzean", "error");
    }
  }

  function isValidPlacementPosition(x, y) {
    if (!producingCity) return false;

    // Check if position is within the city area tiles
    const isInCityArea = cityAreaTiles.some(
      (tile) => tile.x === x && tile.y === y,
    );
    if (!isInCityArea) {
      return false;
    }

    // Check if position is water
    if (terrain[y] && terrain[y][x] === TERRAIN_TYPES.WATER) {
      return false;
    }

    // Check if position is occupied by another unit
    const isOccupied = units.some(
      (unit) =>
        unit.position &&
        Array.isArray(unit.position) &&
        unit.position[0] === x &&
        unit.position[1] === y,
    );

    // NEW: Check if position has a city
    const hasCityAtPosition = cities.some(
      (city) =>
        (city.position.x === x && city.position.y === y) ||
        (Array.isArray(city.position) &&
          city.position[0] === x &&
          city.position[1] === y),
    );

    return !isOccupied && !hasCityAtPosition;
  }
  function togglePauseMenu() {
    showPauseMenu = !showPauseMenu;
    pauseGame(showPauseMenu);
  }

  onMount(async () => {
    try {
      document.body.classList.add("map-active");
      document.documentElement.classList.add("map-active");
      document.addEventListener("click", handleFirstInteraction);
      document.addEventListener("keydown", handleFirstInteraction);

      if (!$user) {
        navigate("/");
        return;
      }

      window.addEventListener("keydown", handleKeyPress);

      selectedMapId = $gameState?.currentScenario?.mapId;
      console.log("Selected map ID:", selectedMapId);

      await initializeGame();

      // Refresca la tarjeta de información de la tropa al cargar el mapa
      refreshSelectedUnitInfo();

      return () => {
        document.body.classList.remove("map-active");
        document.documentElement.classList.remove("map-active");
        window.removeEventListener("keydown", handleKeyPress);
        document.removeEventListener("click", handleFirstInteraction);
        document.removeEventListener("keydown", handleFirstInteraction);
      };
    } catch (err) {
      console.error("Error mounting Map component:", err);
      loadingError = err.message;
    }
  });

  onDestroy(() => {
    document.body.classList.remove("map-active");
    document.documentElement.classList.remove("map-active");
    window.removeEventListener("keydown", handleKeyPress);
  });

  function handleKeyPress(event) {
    if (event.key === "Escape") {
      togglePauseMenu();
    }

    // Fix: Check for Ctrl+T key combo to open cheat console
    // Check if we're NOT inside the cheat console already
    if (event.key.toLowerCase() === "t" && !showCheatConsole) {
      event.preventDefault(); // Prevent browser's default action
      toggleCheatConsole();
    }
  }

  // Function to toggle the cheat console visibility
  function toggleCheatConsole() {
    showCheatConsole = true;
    if (showCheatConsole) {
      // Focus on the input field when opening the console
      setTimeout(() => {
        document.getElementById("cheat-input")?.focus();
      }, 100);
    }
    cheatResult = null; // Clear previous result
  }

  // Function to process cheat commands
  async function processCheat(event) {
    const command = event.detail.command;

    try {
      // Check if this is an insert troop command
      if (command.startsWith("insert_")) {
        const parts = command.split("_");
        if (parts.length !== 4) {
          cheatResult =
            "Formatu baliogabea. Erabili: insert_[troop]_[cordX]_[cordY]";
          cheatResultType = "error";
          return;
        }

        const troopType = parts[1];
        const cordX = parseInt(parts[2], 10);
        const cordY = parseInt(parts[3], 10);

        // Validate coordinates
        if (
          isNaN(cordX) ||
          isNaN(cordY) ||
          cordX < 0 ||
          cordY < 0 ||
          cordX >= mapWidth ||
          cordY >= mapHeight
        ) {
          cheatResult = `Koordenatu baliogabeak. Kokapenak ${mapWidth}x${mapHeight} artekoa izan behar du`;
          cheatResultType = "error";
          return;
        }

        // Check if position is water
        if (terrain[cordY] && terrain[cordY][cordX] === TERRAIN_TYPES.WATER) {
          cheatResult = "Ezin duzu tropa bat ur gainean kokatu";
          cheatResultType = "error";
          return;
        }

        // Check if the position is occupied
        const isOccupied = units.some(
          (u) =>
            u.position &&
            Array.isArray(u.position) &&
            u.position[0] === cordX &&
            u.position[1] === cordY,
        );

        if (isOccupied) {
          cheatResult = "Kokapena okupatuta dago jada";
          cheatResultType = "error";
          return;
        }

        // Check if there's a city at that position
        const cityAtPosition = cities.find(
          (city) =>
            (city.position.x === cordX && city.position.y === cordY) ||
            (Array.isArray(city.position) &&
              city.position[0] === cordX &&
              city.position[1] === cordY),
        );

        if (cityAtPosition) {
          cheatResult = "Ezin duzu tropa bat hiriko laukian kokatu";
          cheatResultType = "error";
          return;
        }

        // Fetch troop type from API to validate it exists
        try {
          // Create position array for the API call
          const position = [cordX, cordY];
          const troopInfo = await gameAPI.getTroopType(troopType, position);

          // If no error was thrown, the troop type exists
          // Create unique ID for the new unit
          const unitId = `cheat-unit-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;

          // Create the new unit
          const newUnit = {
            ...troopInfo,
            id: unitId,
            type_id: troopType,
            position: [cordX, cordY],
            owner: "player",
            status: "ready",
            movement: troopInfo.movement || 2,
            remainingMovement: troopInfo.movement || 2,
            health: troopInfo.health || 100,
            attack: troopInfo.attack || 10,
            defense: troopInfo.defense || 5,
          };

          // Add unit to game data and units array
          if (!gameData.player.units) {
            gameData.player.units = [];
          }

          gameData.player.units.push(newUnit);
          units = [...units, newUnit];

          // Update fog of war around new unit
          updateFogOfWarAroundPosition(cordX, cordY, 2);

          // Save changes to game session
          await gameAPI.updateGameSession(gameData);

          // Make sure the cheats_used array exists
          if (!gameData.cheats_used) {
            gameData.cheats_used = [];
          }
          // Add to cheats_used array if not already there
          if (!gameData.cheats_used.includes("insert_troop")) {
            gameData.cheats_used.push("insert_troop");
          }

          cheatResult = `'${troopInfo.name || troopType}' tropa [${cordX}, ${cordY}] kokapenean gehitu da`;
          cheatResultType = "success";

          // Center the map on the new unit
          centerMapOnPosition(cordX, cordY);
        } catch (error) {
          console.error("Error validating troop type:", error);
          cheatResult = `'${troopType}' tropa mota ez da existitzen`;
          cheatResultType = "error";
          return;
        }
        return;
      }

      // Process the other existing cheat commands
      if (command === "fogOfWar_Off") {
        if (showFogOfWar) {
          // Disable fog of war
          showFogOfWar = false;

          // Make sure the cheats_used array exists
          if (!gameData.cheats_used) {
            gameData.cheats_used = [];
          }

          // Add to cheats_used array if not already there
          if (!gameData.cheats_used.includes("fogOfWar_Off")) {
            gameData.cheats_used.push("fogOfWar_Off");
          }

          // Save changes to session
          await gameAPI.updateGameSession(gameData);

          cheatResult = "Gerra lainoa desaktibatuta";
          cheatResultType = "success";
        } else {
          cheatResult = "Gerra lainoa jada desaktibatuta dago";
          cheatResultType = "info";
        }
      } else if (command === "unlimitedMovements") {
        unlimitedMovementsActive = true;

        // Make sure the cheats_used array exists
        if (!gameData.cheats_used) {
          gameData.cheats_used = [];
        }

        // Add to cheats_used array if not already there
        if (!gameData.cheats_used.includes("unlimitedMovements")) {
          gameData.cheats_used.push("unlimitedMovements");
        }

        // Restore all player units' movement points
        if (
          gameData &&
          gameData.player &&
          Array.isArray(gameData.player.units)
        ) {
          gameData.player.units.forEach((unit) => {
            unit.status = "ready";
            unit.remainingMovement = unit.movement || 2;
          });

          // Update units array to match gameData
          units = units.map((unit) => {
            if (unit.owner === "player") {
              return {
                ...unit,
                status: "ready",
                remainingMovement: unit.movement || 2,
              };
            }
            return unit;
          });
        }

        // Save changes to session
        await gameAPI.updateGameSession(gameData);

        cheatResult =
          "Mugimendu mugagabeak aktibatuta! Zure tropak mugarik gabe mugitu daitezke";
        cheatResultType = "success";
      } else if (command === "unlimitedResources") {
        // --- NUEVO: Da 99999 de cada recurso y guarda en sesión ---
        if (gameData && gameData.player && gameData.player.resources) {
          gameData.player.resources.food = 99999;
          gameData.player.resources.gold = 99999;
          gameData.player.resources.wood = 99999;
          gameData.player.resources.iron = 99999;
          gameData.player.resources.stone = 99999;
        }
        // Añade el cheat a la lista si no está
        if (!gameData.cheats_used) {
          gameData.cheats_used = [];
        }
        if (!gameData.cheats_used.includes("unlimitedResources")) {
          gameData.cheats_used.push("unlimitedResources");
        }
        // Guarda en la sesión
        await gameAPI.updateGameSession(gameData);

        cheatResult =
          "Baliabide mugagabeak aktibatuta! 99999 baliabide bakoitzetik gehituta";
        cheatResultType = "success";
      } else {
        // Invalid command
        cheatResult = `Komando baliogabea: ${command}`;
        cheatResultType = "error";
      }

      console.log(`Cheat processed: ${command} - Result: ${cheatResult}`);
    } catch (error) {
      console.error("Error processing cheat:", error);
      cheatResult = `Errorea: ${error.message}`;
      cheatResultType = "error";
    }
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
            const playerUnits = gameData.player.units.map((unit) => ({
              ...unit,
              owner: "player",
            }));
            units = [...playerUnits];
            console.log("Player units loaded:", playerUnits.length);
          }

          if (gameData.ia && Array.isArray(gameData.ia.units)) {
            const aiUnits = gameData.ia.units.map((unit) => ({
              ...unit,
              owner: "ia",
            }));
            units = [...units, ...aiUnits];
            console.log("AI units loaded:", aiUnits.length);
          }

          console.log("Total units loaded:", units.length);

          if (
            gameData &&
            gameData.player &&
            Array.isArray(gameData.player.cities)
          ) {
            cities = [...gameData.player.cities, ...gameData.ia.cities];
            console.log("Loaded cities:", cities.length);
          } else {
            cities = [];
          }

          // Initialize cheats_used array if it doesn't exist
          if (!gameData.cheats_used) {
            gameData.cheats_used = [];
          }

          // Apply any previously used cheats
          if (gameData.cheats_used.includes("fogOfWar_Off")) {
            showFogOfWar = false;
          }

          // Check if unlimitedMovements cheat was previously used
          if (gameData.cheats_used.includes("unlimitedMovements")) {
            unlimitedMovementsActive = true;
          }

          ceasefireTurns = gameData.ceasefire_turns || 0;
          ceasefireActive = !!gameData.ceasefire_active && ceasefireTurns > 0;
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
      loadingError = error.message || "Errore ezezaguna jokoa hasieratzean.";
      isLoading = false;
    }
  }

  function initializeFogOfWar() {
    grid = Array(mapHeight)
      .fill()
      .map(() => Array(mapWidth).fill(FOG_OF_WAR.HIDDEN));

    if (startPoint && startPoint.length === 2) {
      const [startX, startY] = startPoint;
      const visibilityRadius = 3;

      for (
        let y = Math.max(0, startY - visibilityRadius);
        y <= Math.min(mapHeight - 1, startY + visibilityRadius);
        y++
      ) {
        for (
          let x = Math.max(0, startX - visibilityRadius);
          x <= Math.min(mapWidth - 1, startX + visibilityRadius);
          x++
        ) {
          const distance = Math.sqrt(
            Math.pow(x - startX, 2) + Math.pow(y - startY, 2),
          );
          if (distance <= visibilityRadius) {
            grid[y][x] = FOG_OF_WAR.VISIBLE;
          }
        }
      }
    }
  }

  function initializeTerrain() {
    terrain = Array(mapHeight)
      .fill()
      .map(() => Array(mapWidth).fill(TERRAIN_TYPES.NORMAL));

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
      if (
        startX >= 0 &&
        startX < mapWidth &&
        startY >= 0 &&
        startY < mapHeight
      ) {
        terrain[startY][startX] = TERRAIN_TYPES.NORMAL;

        for (
          let y = Math.max(0, startY - 1);
          y <= Math.min(mapHeight - 1, startY + 1);
          y++
        ) {
          for (
            let x = Math.max(0, startX - 1);
            x <= Math.min(mapWidth - 1, startX + 1);
            x++
          ) {
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

      offsetX = containerWidth / 2 - startX * tileSize * zoomLevel;
      offsetY = containerHeight / 2 - startY * tileSize * zoomLevel;
    }
  }

  function updateFogOfWarAroundPosition(centerX, centerY, radius) {
    if (!showFogOfWar) return;

    for (
      let y = Math.max(0, centerY - radius);
      y <= Math.min(mapHeight - 1, centerY + radius);
      y++
    ) {
      for (
        let x = Math.max(0, centerX - radius);
        x <= Math.min(mapWidth - 1, centerX + radius);
        x++
      ) {
        const distance = Math.sqrt(
          Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2),
        );
        if (distance <= radius && grid[y] && grid[y][x] !== undefined) {
          grid[y][x] = FOG_OF_WAR.VISIBLE;
        }
      }
    }
    grid = [...grid];
  }

  // MODIFICADO: city icon para distinguir IA
  function getCityIcon(city) {
    return { type: "image", value: "./ia_assets/city.jpg" };
  }

  // Function to get terrain background URL based on type
  function getTerrainImageUrl(terrainType) {
    switch (terrainType) {
      case TERRAIN_TYPES.WATER:
        return "./ia_assets/ura_tile.jpg";
      case TERRAIN_TYPES.NORMAL:
        return "./ia_assets/belarra_tile.jpg";
      default:
        return null;
    }
  }

  // Keep original color function as fallback for terrains without images
  function getTerrainColor(terrainType) {
    switch (terrainType) {
      case TERRAIN_TYPES.NORMAL:
        return "#8B4513";
      case TERRAIN_TYPES.WATER:
        return "#1E90FF";
      case TERRAIN_TYPES.MINERAL:
        return "#808080";
      default:
        return "#000";
    }
  }

  // Function to get resource icons based on terrain type
  function getResourceIcon(terrainType) {
    switch (terrainType) {
      case 2:
        return { type: "image", value: "./ia_assets/oro.png" }; // Gold - changed to image
      case 3:
        return { type: "image", value: "./ia_assets/metala.png" }; // Iron/Metal
      case 4:
        return { type: "image", value: "./ia_assets/zuhaitza.png" }; // Wood/Tree
      case 5:
        return { type: "image", value: "./ia_assets/harria.png" }; // Stone
      default:
        return null; // No resource
    }
  }

  // Get the terrain name with updated resource types
  function getTerrainName(terrainType) {
    switch (terrainType) {
      case TERRAIN_TYPES.WATER:
        return "Ura";
      case 2:
        return "Urrea";
      case 3:
        return "Burdina";
      case 4:
        return "Egurra";
      case 5:
        return "Harria";
      case TERRAIN_TYPES.NORMAL:
        return "Lurra";
      default:
        return "Ezezaguna";
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
    const remainingMovement =
      unit.remainingMovement !== undefined
        ? unit.remainingMovement
        : totalMovement;

    // Skip the remaining movement check if unlimited movements cheat is active
    if (!unlimitedMovementsActive && remainingMovement <= 0) {
      showToastNotification(
        "Unitate honek dagoeneko agortu ditu bere mugimenduak txanda honetan.",
        "warning",
      );
      selectedUnit = null;
      return;
    }

    const [unitX, unitY] = unit.position;
    // Use either the unit's remaining movement or a high value for unlimited movement
    const movementPoints = unlimitedMovementsActive ? 20 : remainingMovement;
    calculateValidMoveTargets(unitX, unitY, movementPoints);
  }

  function handleUnitClick(unit) {
    if (unit.owner !== "player") {
      showToastNotification(
        "Hau etsai unitate bat da. Ezin duzu kontrolatu.",
        "warning",
      );
      return;
    }

    selectedUnitInfo = unit;

    // If the unit can attack, highlight this information
    if (canAttack(unit)) {
      showToastNotification(
        "¡Unitate honek inguruko etsaiak erasotu ditzake!",
        "info",
      );
    }

    if (unit.status === "exhausted") {
    }

    selectedUnitInfo = unit;

    // If the unit can attack, highlight this information
    if (canAttack(unit)) {
      showToastNotification(
        "¡Unitate honek inguruko etsaiak erasotu ditzake!",
        "info",
      );
    }

    if (unit.status === "exhausted") {
      showToastNotification(
        "Unitate honek dagoeneko agortu ditu bere mugimenduak txanda honetan.",
        "warning",
      );
      selectedUnit = null;
      validMoveTargets = [];
    } else {
      selectUnit(unit);
    }
  }

  // Update the enterCity function to be more reliable
  async function enterCity(city) {
    if (!gameData || !city) {
      showToastNotification("Errorea hirira sartzean", "error");
      return;
    }

    try {
      // Save current game state to session before navigating
      console.log(
        "Guardando estado del juego en sesión antes de entrar a la ciudad",
      );
      await gameAPI.updateGameSession(gameData);

      // Store the city ID in both in-memory storage and localStorage
      const cityId = city.id;

      // Make sure cityId is valid
      if (!cityId) {
        showToastNotification("Hiriaren ID baliogabea", "error");
        return;
      }

      console.log("Entering city with ID:", cityId);

      // Store the ID before navigating
      gameAPI.storeTemporaryData("selectedCityId", cityId);

      // Navigate to city page
      navigate("/city");
    } catch (error) {
      console.error("Error entering city:", error);
      showToastNotification(
        "Errorea hirira sartzean: " + error.message,
        "error",
      );
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
      case "warrior":
        return "./ia_assets/warrior.png";
      case "settler":
        return "./ia_assets/settler.png";
      case "cavalry":
        return "./ia_assets/cavalry.png";
      case "archer":
        return "./ia_assets/archer.png";
      case "boar_rider":
        return "./ia_assets/boar_rider.png";
      case "tank":
        return "./ia_assets/tank.png";
      default:
        return null;
    }
  }

  // Actualiza la tarjeta de información de la tropa si hay cambios en el JSON del juego
  function refreshSelectedUnitInfo() {
    if (!selectedUnitInfo || !selectedUnitInfo.id) return;
    // Buscar la tropa actualizada en units (que siempre refleja el JSON)
    const updated = units.find((u) => u.id === selectedUnitInfo.id);
    if (updated) {
      selectedUnitInfo = updated;
    }
  }
</script>

<svelte:head>
  <title>Mapa - Zibilizazio Jokoa</title>
</svelte:head>

<div class="map-page">
  <AudioPlayer bind:this={audioPlayer} />

  {#if isLoading}
    <div class="loading">
      <div class="loading-spinner"></div>
      <h2>Jokoa hasieratzen...</h2>
      {#if loadingError}
        <div class="error-message">Errorea: {loadingError}</div>
        <button class="retry-button" on:click={initializeGame}
          >Saiatu berriro</button
        >
      {/if}
    </div>
  {:else if loadingError}
    <div class="error">
      <h2>Errorea jokoa kargatzean</h2>
      <p>{loadingError}</p>
      <button on:click={() => navigate("/new-game")}
        >Partida Berrira Itzuli</button
      >
    </div>
  {:else}
    <div class="map-controls">
      <div class="left-controls">
        <button class="menu-button" on:click={togglePauseMenu}>☰ Menua</button>
        <span class="game-info">
          Txanda: {$currentTurn} | Jokalaria: {$currentPlayer} | Mapa: {mapWidth}x{mapHeight}
          | Zailtasuna: {difficulty}
        </span>
      </div>
      <div class="right-controls">
        <button
          class="end-turn-button"
          on:click={endTurn}
          title={processingAITurn
            ? "IA txanda prozesatzen..."
            : "Txanda Amaitu"}
          disabled={processingAITurn}
          class:processing={processingAITurn}
        >
          {processingAITurn ? "IA pentsatzen..." : "Txanda Amaitu"}
        </button>
        <button on:click={zoomIn} title="Zooma handitu">+</button>
        <button on:click={zoomOut} title="Zooma txikitu">-</button>
        <button on:click={centerMapOnStartPoint} title="Mapa zentratu">⌖</button
        >
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
            {@const isVisible =
              !showFogOfWar || (grid[y] && grid[y][x] === FOG_OF_WAR.VISIBLE)}
            {@const terrainType =
              terrain[y] && terrain[y][x] !== undefined
                ? terrain[y][x]
                : TERRAIN_TYPES.NORMAL}
            {@const isValidMoveTarget = validMoveTargets.some(
              (target) => target.x === x && target.y === y,
            )}
            {@const unitAtPosition = units.find(
              (unit) =>
                unit &&
                unit.position &&
                Array.isArray(unit.position) &&
                unit.position.length >= 2 &&
                unit.position[0] === x &&
                unit.position[1] === y,
            )}
            {@const isSelectedUnit =
              selectedUnit && unitAtPosition === selectedUnit}
            {@const terrainImageUrl = isVisible
              ? getTerrainImageUrl(terrainType)
              : null}
            {@const hasResource =
              isVisible &&
              (terrainType === 2 ||
                terrainType === 3 ||
                terrainType === 4 ||
                terrainType === 5)}

            <div
              class="map-tile"
              class:fog={showFogOfWar && !isVisible}
              class:water={isVisible && terrainType === TERRAIN_TYPES.WATER}
              class:mineral={isVisible && terrainType === TERRAIN_TYPES.MINERAL}
              class:valid-move={isVisible && isValidMoveTarget}
              class:selected-unit-tile={isVisible && isSelectedUnit}
              class:city-area-tile={cityAreaTiles.some(
                (tile) => tile.x === x && tile.y === y,
              )}
              class:city-center-tile={selectedCityInfo &&
                ((Array.isArray(selectedCityInfo.position) &&
                  selectedCityInfo.position[0] === x &&
                  selectedCityInfo.position[1] === y) ||
                  (selectedCityInfo.position.x === x &&
                    selectedCityInfo.position.y === y))}
              style="
                left: {x * tileSize}px;
                top: {y * tileSize}px;
                width: {tileSize}px;
                height: {tileSize}px;
                background-color: {isVisible && !terrainImageUrl
                ? hasResource
                  ? getTerrainColor(TERRAIN_TYPES.NORMAL)
                  : getTerrainColor(terrainType)
                : '#000'};
                background-image: {terrainImageUrl && !hasResource
                ? `url('${terrainImageUrl}')`
                : hasResource
                  ? `url('./ia_assets/belarra_tile.jpg')`
                  : 'none'};
                background-size: cover;
              "
              on:click={() => handleTileClick(x, y)}
              on:keydown={(e) => e.key === "Enter" && handleTileClick(x, y)}
              role="button"
              tabindex="0"
              class:selected={selectedTile &&
                selectedTile.x === x &&
                selectedTile.y === y}
              aria-label="Map tile at position {x},{y}"
            >
              {#if hasResource && isVisible}
                <div
                  class="resource-marker"
                  title={getTerrainName(terrainType)}
                >
                  {#if getResourceIcon(terrainType).type === "emoji"}
                    <span class="resource-icon"
                      >{getResourceIcon(terrainType).value}</span
                    >
                  {:else}
                    <img
                      src={getResourceIcon(terrainType).value}
                      alt={getTerrainName(terrainType)}
                      class="resource-image"
                    />
                  {/if}
                </div>
              {/if}

              {#each cities as city}
                {#if ((city.position.x === x && city.position.y === y) || (Array.isArray(city.position) && city.position[0] === x && city.position[1] === y)) && (!showFogOfWar || (grid[y] && grid[y][x] === FOG_OF_WAR.VISIBLE) || city.owner !== "ia")}
                  <div
                    class="city-marker"
                    title="{city.name} (Biztanleria: {city.population || 0})"
                  >
                    <span class="city-icon">
                      {#if getCityIcon(city).type === "emoji"}
                        {getCityIcon(city).value}
                      {:else}
                        <img
                          src={getCityIcon(city).value}
                          alt="City"
                          class="city-image"
                        />
                      {/if}
                    </span>
                  </div>
                {/if}
              {/each}

              {#if unitAtPosition && isVisible}
                <div
                  class="unit-marker"
                  class:selected={isSelectedUnit}
                  class:exhausted={unitAtPosition.status === "exhausted"}
                  class:enemy={unitAtPosition.owner === "ia"}
                  title="{unitAtPosition.name ||
                    unitAtPosition.type_id} {unitAtPosition.owner === 'ia'
                    ? '(Etsaia)'
                    : ''} {unitAtPosition.status
                    ? '(' + unitAtPosition.status + ')'
                    : ''}"
                >
                  {#if getUnitImageUrl(unitAtPosition.type_id)}
                    <img
                      src={getUnitImageUrl(unitAtPosition.type_id)}
                      alt={unitAtPosition.type_id}
                      class="unit-image"
                    />
                  {:else}
                    <span class="unit-icon"
                      >{getUnitIcon(unitAtPosition.type_id)}</span
                    >
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
            <h4>Laukia ({selectedTile.x}, {selectedTile.y})</h4>
            <button class="close-button" on:click={() => (selectedTile = null)}
              >×</button
            >
          </div>

          <div class="terrain-info">
            <h5>Lurraldea: {selectedTile.terrainName}</h5>
            {#if selectedTile.isExplored !== false}
              <div
                class="terrain-sample"
                style="background-color: {getTerrainColor(
                  selectedTile.terrain,
                )};"
              ></div>
            {/if}
          </div>

          {#if startPoint && startPoint[0] === selectedTile.x && startPoint[1] === selectedTile.y}
            <div class="start-info">
              <h5>Maparen hasierako puntua</h5>
              <p>Hau da partida hasteko gomendatutako hasierako posizioa.</p>
            </div>
          {/if}

          {#if selectedTile.isExplored === false}
            <div class="fog-info">
              <p>Eremu hau ez da oraindik esploratu.</p>
            </div>
          {/if}
        </div>
      </div>
    {/if}

    {#if selectedUnitInfo && !showPauseMenu}
      {#if !showFogOfWar || (selectedUnitInfo.position && grid[selectedUnitInfo.position[1]] && grid[selectedUnitInfo.position[1]][selectedUnitInfo.position[0]] === FOG_OF_WAR.VISIBLE)}
        <div class="unit-info-overlay">
          <div
            class="unit-info-card"
            class:enemy-unit={selectedUnitInfo.owner === "ia"}
          >
            <div class="unit-info-header">
              <h4>
                {selectedUnitInfo.name ||
                  selectedUnitInfo.type_id ||
                  "Unitatea"}
              </h4>
              <button
                class="close-button"
                on:click={() => {
                  selectedUnitInfo = null;
                }}>×</button
              >
            </div>

            <div class="unit-details">
              <div class="unit-image-container">
                {#if selectedUnitInfo.type_id && getUnitImageUrl(selectedUnitInfo.type_id)}
                  <img
                    src={getUnitImageUrl(selectedUnitInfo.type_id)}
                    alt={selectedUnitInfo.type_id}
                    class="unit-portrait"
                  />
                {:else}
                  <div class="unit-icon-large">
                    {selectedUnitInfo.type_id
                      ? getUnitIcon(selectedUnitInfo.type_id)
                      : "❓"}
                  </div>
                {/if}
              </div>

              <div class="unit-stats">
                <p>
                  <strong>Mota:</strong>
                  {selectedUnitInfo.type_id || "Ezezaguna"}
                </p>
                <p>
                  <strong>Taldea:</strong>
                  {selectedUnitInfo.owner === "ia" ? "Etsaia" : "Jokalaria"}
                </p>
                <p>
                  <strong>Egoera:</strong>
                  {selectedUnitInfo.status || "ready"}
                </p>
                <p>
                  <strong>Mugimenduak:</strong>
                  {selectedUnitInfo.remainingMovement !== undefined
                    ? selectedUnitInfo.remainingMovement
                    : selectedUnitInfo.movement ||
                      2}/{selectedUnitInfo.movement || 2}
                </p>
                {#if selectedUnitInfo.position && Array.isArray(selectedUnitInfo.position) && selectedUnitInfo.position.length >= 2}
                  <p>
                    <strong>Kokapena:</strong> [{selectedUnitInfo.position[0]}, {selectedUnitInfo
                      .position[1]}]
                  </p>
                {/if}

                {#if selectedUnitInfo.health !== undefined}
                  <p><strong>Osasuna:</strong> {selectedUnitInfo.health}</p>
                {/if}

                {#if selectedUnitInfo.attack !== undefined}
                  <p><strong>Erasoa:</strong> {selectedUnitInfo.attack}</p>
                {/if}

                {#if selectedUnitInfo.defense !== undefined}
                  <p><strong>Defentsa:</strong> {selectedUnitInfo.defense}</p>
                {/if}
              </div>
            </div>

            {#if selectedUnitInfo.owner !== "ia" && selectedUnitInfo.status !== "exhausted"}
              <div class="unit-actions">
                <button
                  class="action-button"
                  on:click={() => selectUnit(selectedUnitInfo)}>Mugitu</button
                >

                {#if selectedUnitInfo.type_id === "settler"}
                  <button
                    class="action-button found-city-button"
                    on:click={() => showFoundCityDialog(selectedUnitInfo)}
                  >
                    Hiria Sortu
                  </button>
                {/if}

                <button
                  class="action-button attack-button"
                  on:click={() => tryAttackFromCard(selectedUnitInfo)}
                >
                  Eraso
                </button>

                <button
                  class="action-button negotiate-button"
                  on:click={() => openNegotiation(selectedUnitInfo)}
                  disabled={!canNegotiate(selectedUnitInfo)}
                  title={canNegotiate(selectedUnitInfo)
                    ? "IArekin negoziatu"
                    : "Etsai unitate batetik 2 laukira egon behar zara negoziatzeko"}
                >
                  Negoziatu
                </button>
              </div>
            {:else if selectedUnitInfo.owner === "ia"}
              <div class="unit-enemy-message">
                <p>Hau etsai unitate bat da. Ezin duzu kontrolatu.</p>
              </div>
            {:else}
              <div class="unit-exhausted-message">
                <p>
                  Unitate honek dagoeneko agortu ditu bere mugimenduak txanda
                  honetan.
                </p>
              </div>
            {/if}
          </div>
        </div>
      {/if}
    {/if}

    {#if selectedCityInfo && !showPauseMenu}
      <div class="city-info-overlay">
        <div
          class="city-info-card"
          class:enemy-city-card={selectedCityInfo.owner === "ia"}
        >
          <div class="city-info-header">
            <h4>{selectedCityInfo.name || "Hiria"}</h4>
            <button
              class="close-button"
              on:click={() => {
                selectedCityInfo = null;
              }}>×</button
            >
          </div>

          <div class="city-details">
            <div class="city-image-container">
              <div class="city-icon-large">
                {#if getCityIcon(selectedCityInfo).type === "emoji"}
                  {getCityIcon(selectedCityInfo).value}
                {:else}
                  <img
                    src={getCityIcon(selectedCityInfo).value}
                    alt="City"
                    class="city-portrait"
                  />
                {/if}
              </div>
            </div>

            <div class="city-stats">
              <p>
                <strong>Biztanleria:</strong>
                {selectedCityInfo.population || 0}
              </p>
              {#if selectedCityInfo.position}
                <p>
                  <strong>Kokapena:</strong>
                  {Array.isArray(selectedCityInfo.position)
                    ? `[${selectedCityInfo.position[0]}, ${selectedCityInfo.position[1]}]`
                    : `[${selectedCityInfo.position.x}, ${selectedCityInfo.position.y}]`}
                </p>
              {/if}

              {#if selectedCityInfo.buildings && selectedCityInfo.buildings.length > 0}
                <p>
                  <strong>Eraikinak:</strong>
                  {selectedCityInfo.buildings.length}
                </p>
              {/if}

              {#if selectedCityInfo.production && selectedCityInfo.production.current_item}
                <p>
                  <strong>Ekoizpena:</strong>
                  {selectedCityInfo.production.current_item}
                </p>
                <p>
                  <strong>Geratzen diren txandak:</strong>
                  {selectedCityInfo.production.turns_remaining}
                </p>
              {/if}
            </div>
          </div>

          <div class="city-actions">
            <button
              class="action-button enter-city-button"
              on:click={() => enterCity(selectedCityInfo)}
            >
              Hirian Sartu
            </button>
          </div>
        </div>
      </div>
    {/if}

    {#if showCityFoundingModal}
      <div class="modal-overlay">
        <div class="modal-content">
          <h3>Hiri Berria Sortu</h3>
          <p>
            Hiri berri bat sortuko duzu kokaleku honetan [{settlerToFoundCity
              ?.position[0] || 0}, {settlerToFoundCity?.position[1] || 0}].
          </p>

          <div class="form-group">
            <label for="city-name">Hiriaren Izena:</label>
            <input
              type="text"
              id="city-name"
              bind:value={newCityName}
              placeholder="Sartu zure hiriarentzat izen bat"
            />
          </div>

          <div class="resource-requirements">
            <h4>Beharrezko baliabideak:</h4>
            <div class="resource wood">
              <div class="resource-icon">
                <img
                  src="./ia_assets/zuhaitza.png"
                  alt="Wood"
                  class="resource-icon-img"
                />
              </div>
              <div class="resource-value">20</div>
            </div>
            <div class="resource stone">
              <div class="resource-icon">
                <img
                  src="./ia_assets/harria.png"
                  alt="Stone"
                  class="resource-icon-img"
                />
              </div>
              <div class="resource-value">15</div>
            </div>
          </div>

          <div class="modal-actions">
            <button class="cancel-button" on:click={cancelCityFounding}
              >Utzi</button
            >
            <button class="confirm-button" on:click={foundCity}
              >Hiria Sortu</button
            >
          </div>
        </div>
      </div>
    {/if}

    {#if showPauseMenu}
      <div class="pause-menu-overlay">
        <div class="pause-menu">
          <div class="pause-header">
            <h2>Jokoa Pausatua</h2>
            <button class="close-button" on:click={togglePauseMenu}>×</button>
          </div>

          <div class="menu-options">
            <button class="menu-option primary" on:click={togglePauseMenu}>
              Partidarekin Jarraitu
            </button>

            <button class="menu-option" on:click={saveAndExit}>
              Gorde eta Irten
            </button>

            <button class="menu-option danger" on:click={exitWithoutSaving}>
              Gorde Gabe Irten
            </button>
          </div>

          <div class="game-details">
            <p>Izena: {$gameState.gameName || "Nire Partida"}</p>
            <p>Zailtasuna: {difficulty}</p>
            <p>Mapa-tamaina: {mapWidth}x{mapHeight}</p>
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
          <img
            src="./ia_assets/janaria.png"
            alt="Food"
            class="resource-bar-icon"
          />
        </div>
        <div class="resource-value">{gameData.player.resources.food || 0}</div>
      </div>
      <div class="resource gold">
        <div class="resource-icon">
          <img
            src="./ia_assets/lingotes_oro.png"
            alt="Gold"
            class="resource-bar-icon"
          />
        </div>
        <div class="resource-value">{gameData.player.resources.gold || 0}</div>
      </div>
      <div class="resource wood">
        <div class="resource-icon">
          <img
            src="./ia_assets/zuhaitza.png"
            alt="Wood"
            class="resource-bar-icon"
          />
        </div>
        <div class="resource-value">{gameData.player.resources.wood || 0}</div>
      </div>
      <!-- Add iron resource -->
      <div class="resource iron">
        <div class="resource-icon">
          <img
            src="./ia_assets/lingote_hierro.png"
            alt="Iron"
            class="resource-bar-icon"
          />
        </div>
        <div class="resource-value">{gameData.player.resources.iron || 0}</div>
      </div>
      <!-- Add stone resource -->
      <div class="resource stone">
        <div class="resource-icon">
          <img
            src="./ia_assets/harria.png"
            alt="Stone"
            class="resource-bar-icon"
          />
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
          <h4>IA Ekintza {aiActionIndex + 1}/{aiActions.length}</h4>
        </div>

        <div class="ai-action-content">
          <div class="ai-action-icon">
            {#if currentAIAction.type === "movement"}
              <span class="action-icon">🚶</span>
            {:else if currentAIAction.type === "attack"}
              <span class="action-icon">⚔️</span>
            {:else if currentAIAction.type === "construction"}
              <span class="action-icon">🏗️</span>
            {:else}
              <span class="action-icon">🔄</span>
            {/if}
          </div>

          <div class="ai-action-description">
            <p>{aiActionDescription}</p>
            {#if currentAIAction.type === "attack"}
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
        <h4>IA Estrategia</h4>
        <p>{aiTurnReasoning}</p>
      </div>
    </div>
  {/if}

  <!-- Add attack targets overlay -->
  {#if showAttackOptions && attackTargets.length > 0 && !showPauseMenu}
    <div class="attack-targets-overlay">
      <div class="attack-targets-card">
        <div class="attack-targets-header">
          <h4>Aukeratu erasotzeko helburua</h4>
          <button
            class="close-button"
            on:click={() => (showAttackOptions = false)}>×</button
          >
        </div>

        <div class="attack-targets-list">
          {#each attackTargets as target}
            <div class="attack-target" on:click={() => initiateAttack(target)}>
              <div class="target-icon">
                {#if getUnitImageUrl(target.type_id)}
                  <img
                    src={getUnitImageUrl(target.type_id)}
                    alt={target.type_id}
                  />
                {:else}
                  <span class="unit-icon">{getUnitIcon(target.type_id)}</span>
                {/if}
              </div>
              <div class="target-info">
                <h5>{target.name || target.type_id}</h5>
                <p>Osasuna: {target.health || 100}</p>
                <p>Kokapena: [{target.position[0]}, {target.position[1]}]</p>
              </div>
              <button class="attack-button">Eraso</button>
            </div>
          {/each}
        </div>
      </div>
    </div>
  {/if}

  {#if showNegotiationModal}
    <NegotiationModal
      unit={negotiationUnit}
      on:close={closeNegotiation}
      on:result={handleNegotiationResult}
    />
  {/if}

  {#if ceasefireActive && ceasefireTurns > 0}
    <div class="ceasefire-banner">
      🕊️ Su-etena aktibo: Ezin da eraso egin geratzen {ceasefireTurns} txanda{ceasefireTurns ===
      1
        ? ""
        : "k"}.
    </div>
  {/if}
</div>

<!-- Add CheatConsole component near the end of the template -->
<CheatConsole
  visible={showCheatConsole}
  result={cheatResult}
  resultType={cheatResultType}
  on:close={() => (showCheatConsole = false)}
  on:execute={processCheat}
/>

<style>
  /* ...existing code... */
  .ceasefire-banner {
    position: fixed;
    top: 48px;
    left: 50%;
    transform: translateX(-50%);
    background: #222e3a;
    color: #fff;
    padding: 10px 28px;
    border-radius: 8px;
    font-size: 1.1rem;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.18);
    z-index: 2000;
    border: 2px solid #5b7cff;
    letter-spacing: 0.5px;
  }
</style>
