<script>
  import { onMount, onDestroy } from 'svelte';
  import { navigate } from '../router.js';
  import { user } from '../stores/auth.js';
  import { gameAPI } from '../services/gameAPI.js';
  import { gameState } from '../stores/gameState.js';
  import '../styles/pages/city.css'; 
  
  let city = null;
  let isLoading = true;
  let error = null;
  let gameData = null;
  let troopTypes = [];
  let loadingTroopTypes = false;
  let activeTab = 'summary';
  let selectedTroopType = null;
  
  // Add new state variables for building types
  let buildingTypes = [];
  let loadingBuildingTypes = false;
  let selectedBuildingType = null;

  // Add state variables for the confirmation dialog
  let showConfirmationDialog = false;
  let confirmationMessage = "";
  let confirmationCallback = null;
  let itemToCancel = null;

  // Add new state variables for technology types
  let technologyTypes = [];
  let loadingTechnologyTypes = false;
  let selectedTechnology = null;

  // Add a helper function to render costs dynamically based on what's in the cost object
  function getResourceCostString(costObject) {
    if (!costObject) return 'Costo no disponible';
    
    const resourceDisplay = [];
    
    // Process each resource in the cost object
    if (costObject.food && costObject.food > 0) {
      resourceDisplay.push(`<span class="resource-cost-item"><img src="./ia_assets/janaria.png" alt="Food" class="resource-icon-small" style="width:12px;height:12px;vertical-align:middle;" /> ${costObject.food}</span>`);
    }
    
    if (costObject.gold && costObject.gold > 0) {
      resourceDisplay.push(`<span class="resource-cost-item"><img src="./ia_assets/lingotes_oro.png" alt="Gold" class="resource-icon-small" style="width:12px;height:12px;vertical-align:middle;" /> ${costObject.gold}</span>`);
    }
    
    if (costObject.wood && costObject.wood > 0) {
      resourceDisplay.push(`<span class="resource-cost-item"><img src="./ia_assets/zuhaitza.png" alt="Wood" class="resource-icon-small" style="width:12px;height:12px;vertical-align:middle;" /> ${costObject.wood}</span>`);
    }
    
    if (costObject.stone && costObject.stone > 0) {
      resourceDisplay.push(`<span class="resource-cost-item"><img src="./ia_assets/harria.png" alt="Stone" class="resource-icon-small" style="width:12px;height:12px;vertical-align:middle;" /> ${costObject.stone}</span>`);
    }
    
    if (costObject.iron && costObject.iron > 0) {
      resourceDisplay.push(`<span class="resource-cost-item"><img src="./ia_assets/lingote_hierro.png" alt="Iron" class="resource-icon-small" style="width:12px;height:12px;vertical-align:middle;" /> ${costObject.iron}</span>`);
    }
    
    return resourceDisplay.length > 0 ? resourceDisplay.join(' ') : 'Costo no disponible';
  }

  // Add a helper function to check if player has the required technology
  function hasTechnology(requiredTech) {
    // Debug logging
    console.log("Checking technology requirement:", requiredTech);
    
    // If no technology is required, always return true
    if (!requiredTech) {
      return true;
    }
    
    // Special case for basic technology - more flexible checking
    if (typeof requiredTech === 'string' && 
        (requiredTech.toLowerCase() === "basic" || 
         requiredTech.toLowerCase() === "básica" ||
         requiredTech.toLowerCase() === "none" ||
         requiredTech.toLowerCase() === "básico")) {
      console.log("Basic technology check - automatically approved");
      return true;
    }
    
    // Check if player has the required technology
    if (gameData && gameData.player && gameData.player.technologies) {
      // Debug: List all player technologies
      console.log("Player technologies:", gameData.player.technologies.map(tech => 
        typeof tech === 'string' ? tech : (tech.id || tech.name)
      ));
      
      return gameData.player.technologies.some(tech => {
        // Handle tech as object or string
        const techName = typeof tech === 'string' ? tech.toLowerCase() : 
          (tech.name || tech.id || "").toLowerCase();
        
        // For string comparison, normalize the required tech
        const requiredName = typeof requiredTech === 'string' ? 
          requiredTech.toLowerCase() : 
          (requiredTech.id || requiredTech.name || "").toLowerCase();
        
        // More flexible comparison - check for equality or substring match
        const isMatch = techName === requiredName || 
                       techName.includes(requiredName) || 
                       requiredName.includes(techName);
        
        if (isMatch) {
          console.log(`Technology match found: '${techName}' matches '${requiredName}'`);
        }
        
        return isMatch;
      });
    }
    
    return false;
  }

  // Add debug function to be called on mount
  function debugTechnologies() {
    if (gameData && gameData.player && gameData.player.technologies) {
      console.log("=== Player Technologies Debug ===");
      gameData.player.technologies.forEach((tech, i) => {
        if (typeof tech === 'string') {
          console.log(`${i+1}. String: "${tech}"`);
        } else {
          console.log(`${i+1}. Object: id="${tech.id || 'none'}", name="${tech.name || 'none'}"`);
        }
      });
      console.log("===============================");
    } else {
      console.log("No player technologies found!");
    }
  }

  // Function to get detailed building information
  function getBuildingDetails(building) {
    // If building is just a string, find its details in buildingTypes
    if (typeof building === 'string') {
      const foundType = buildingTypes.find(type => 
        type.name.toLowerCase() === building.toLowerCase() || 
        type.type?.toLowerCase() === building.toLowerCase()
      );
      return foundType || { name: building };
    } 
    
    // If building already has details
    return building;
  }

  function setActiveTab(tab) {
    activeTab = tab;
  }

  async function fetchTroopTypes() {
    loadingTroopTypes = true;
    try {
      const types = await gameAPI.getTroopTypes();
      troopTypes = types;
      console.log("Troop types loaded:", troopTypes);
    } catch (err) {
      console.error("Error loading troop types:", err);
    } finally {
      loadingTroopTypes = false;
    }
  }

  async function fetchBuildingTypes() {
    loadingBuildingTypes = true;
    try {
      const types = await gameAPI.getBuildingTypes();
      buildingTypes = types;
      console.log("Building types loaded:", buildingTypes);
    } catch (err) {
      console.error("Error loading building types:", err);
    } finally {
      loadingBuildingTypes = false;
    }
  }

  // Function to fetch technology types
  async function fetchTechnologyTypes() {
    loadingTechnologyTypes = true;
    try {
      const types = await gameAPI.getTechnologyTypes();
      technologyTypes = types;
      console.log("Technology types loaded:", technologyTypes);
    } catch (err) {
      console.error("Error loading technology types:", err);
    } finally {
      loadingTechnologyTypes = false;
    }
  }

  // Function to check if the city has a library
  function cityHasLibrary() {
    if (!city || !city.buildings) return false;
    
    return city.buildings.some(building => {
      if (typeof building === 'string') {
        return building.toLowerCase() === 'library';
      } else {
        return (building.type_id === 'library' || 
                building.name?.toLowerCase() === 'library');
      }
    });
  }

  // Function to check if a technology is already researched
  function isTechnologyResearched(techId) {
    if (!gameData || !gameData.player || !gameData.player.technologies) {
      return false;
    }
    
    return gameData.player.technologies.some(tech => {
      if (typeof tech === 'string') {
        return tech === techId;
      } else {
        return tech.id === techId || tech.technology === techId;
      }
    });
  }

  // Function to find the library building in the city
  function findLibraryBuilding() {
    if (!city || !city.buildings) return null;
    
    for (let i = 0; i < city.buildings.length; i++) {
      const building = city.buildings[i];
      // Check if it's a library (either as string or object)
      if (typeof building === 'string') {
        if (building.toLowerCase() === 'library') {
          // Convert string to object if needed
          city.buildings[i] = {
            id: `library-${Date.now()}`,
            type_id: 'library',
            name: 'Library',
            production: null
          };
          return city.buildings[i];
        }
      } else if (building.type_id === 'library' || building.name?.toLowerCase() === 'library') {
        // Initialize production field if it doesn't exist
        if (!building.production) {
          building.production = null;
        }
        return building;
      }
    }
    return null;
  }

  // Updated start research function to use library production
  async function startResearch(technology) {
    try {
      if (!city) {
        showToastNotification("Error: No hay ciudad seleccionada", "error");
        return;
      }
      
      // Find the library building
      const library = findLibraryBuilding();
      if (!library) {
        showToastNotification("La ciudad necesita una biblioteca para investigar tecnologías", "error");
        return;
      }
      
      // Check if there's already research in progress
      if ((library.production && library.production.current_technology) || 
          (city.research && city.research.current_technology)) {
        showToastNotification("Ya hay una investigación en curso", "error");
        return;
      }
      
      // Check if population meets minimum requirement
      if (city.population < technology.min_civilians) {
        showToastNotification(`Se requieren al menos ${technology.min_civilians} ciudadanos para investigar esta tecnología`, "error");
        return;
      }
      
      // Check prerequisites
      if (technology.prerequisites && technology.prerequisites.length > 0) {
        const missingPrereqs = technology.prerequisites.filter(prereq => 
          !gameData.player.technologies || !gameData.player.technologies.some(tech => 
            (typeof tech === 'string' && tech === prereq) || 
            (typeof tech === 'object' && (tech.id === prereq || tech.technology === prereq))
          )
        );
        
        if (missingPrereqs.length > 0) {
          showToastNotification(`Faltan tecnologías previas: ${missingPrereqs.join(", ")}`, "error");
          return;
        }
      }
      
      // Set the new research on the library building's production
      library.production = {
        current_technology: technology.id,
        turns_remaining: technology.turns,
        technology_name: technology.name,
        itemType: 'technology',
        production_type: 'research'
      };
      
      console.log("Setting research on library:", library.production);
      
      // Also set city.research for backward compatibility
      city.research = {
        current_technology: technology.id,
        turns_remaining: technology.turns
      };
      
      // Update the game data with the new research
      if (gameData && gameData.player && gameData.player.cities) {
        const cityIndex = gameData.player.cities.findIndex(c => c.id === city.id);
        if (cityIndex !== -1) {
          // Update the city with the modified library
          gameData.player.cities[cityIndex].buildings = city.buildings;
          gameData.player.cities[cityIndex].research = city.research;
          
          // Save changes to game session
          await gameAPI.updateGameSession(gameData);
          
          // Show confirmation
          showToastNotification(`¡Iniciada investigación de ${technology.name}!`, "success");
          
          // Switch to the summary tab to show the research info
          setActiveTab('summary');
        }
      }
    } catch (err) {
      console.error("Error starting research:", err);
      showToastNotification("Error al iniciar la investigación", "error");
    }
  }

  // Updated cancel research function to clear from library
  async function cancelResearch() {
    try {
      const library = findLibraryBuilding();
      const hasLibraryResearch = library && library.production && library.production.current_technology;
      const hasCityResearch = city && city.research && city.research.current_technology;
      
      if (!hasLibraryResearch && !hasCityResearch) {
        showToastNotification("No hay investigación activa que cancelar", "warning");
        return;
      }

      // Get a more readable name if available
      const techId = hasLibraryResearch ? library.production.current_technology : city.research.current_technology;
      const techName = hasLibraryResearch ? library.production.technology_name : null;
      const techType = technologyTypes.find(t => t.id === techId);
      const displayName = techName || (techType ? techType.name : techId);
      
      // Show the confirmation dialog
      confirmationMessage = `¿Estás seguro de que quieres cancelar la investigación de ${displayName}? No recuperarás ningún progreso.`;
      confirmationCallback = confirmCancelResearch;
      showConfirmationDialog = true;
    } catch (error) {
      console.error("Error al cancelar la investigación:", error);
      showToastNotification("Error al cancelar la investigación", "error");
    }
  }

  // Updated confirm cancel research function to clear from library
  async function confirmCancelResearch() {
    try {
      // Clear research from library if it exists
      const library = findLibraryBuilding();
      if (library && library.production) {
        library.production = null;
      }
      
      // Also clear the city.research for backward compatibility
      if (city.research) {
        city.research = {
          current_technology: null,
          turns_remaining: 0
        };
      }
      
      // Update the city in gameData
      if (gameData && gameData.player && gameData.player.cities) {
        const cityIndex = gameData.player.cities.findIndex(c => c.id === city.id);
        if (cityIndex !== -1) {
          gameData.player.cities[cityIndex].buildings = city.buildings;
          gameData.player.cities[cityIndex].research = city.research;
          
          // Save to backend
          await gameAPI.updateGameSession(gameData);
          
          // Show confirmation
          showToastNotification("Investigación cancelada", "info");
        }
      }
    } catch (error) {
      console.error("Error al cancelar la investigación:", error);
      showToastNotification("Error al cancelar la investigación", "error");
    } finally {
      // Reset the confirmation dialog state
      closeConfirmationDialog();
    }
  }

  // Update toggleTroopSelection to prevent selecting locked items
  function toggleTroopSelection(troopType, index) {
    const troopId = troopType.id || `troop-${index}`;
    
    // Check if troop is locked due to technology requirements
    if (!hasTechnology(troopType.technology)) {
      showToastNotification(`Se requiere la tecnología "${troopType.technology}" para ${troopType.name}`, "warning");
      return;
    }
    
    if (selectedTroopType && selectedTroopType._uniqueId === troopId) {
      selectedTroopType = null;
    } else {
      selectedTroopType = {
        ...troopType,
        _uniqueId: troopId
      };
      console.log("Selected troop:", selectedTroopType);
    }
  }

  // Update toggleBuildingSelection to prevent selecting locked items
  function toggleBuildingSelection(buildingType, index) {
    const buildingId = buildingType.id || `building-${index}`;
    
    // Check if building is locked due to technology requirements
    if (!hasTechnology(buildingType.technology)) {
      showToastNotification(`Se requiere la tecnología "${buildingType.technology}" para ${buildingType.name}`, "warning");
      return;
    }
    
    if (selectedBuildingType && selectedBuildingType._uniqueId === buildingId) {
      selectedBuildingType = null;
    } else {
      selectedBuildingType = {
        ...buildingType,
        _uniqueId: buildingId
      };
      console.log("Selected building:", selectedBuildingType);
    }
  }

  // Add function to check if a building type already exists in the city
  function buildingTypeExists(buildingType) {
    if (!city || !city.buildings || !buildingType) return false;
    
    const normalizedSearchType = (buildingType.type || buildingType.name).toLowerCase();
    
    return city.buildings.some(building => {
      // Handle both string and object building representations
      const buildingTypeToCheck = typeof building === 'string' 
        ? building.toLowerCase() 
        : (building.type || building.name).toLowerCase();
      
      return buildingTypeToCheck === normalizedSearchType;
    });
  }
  
  // Get the existing building of a specific type if it exists
  function getExistingBuilding(buildingType) {
    if (!city || !city.buildings || !buildingType) return null;
    
    const normalizedSearchType = (buildingType.type || buildingType.name).toLowerCase();
    
    return city.buildings.find(building => {
      const buildingTypeToCheck = typeof building === 'string' 
        ? building.toLowerCase() 
        : (building.type || building.name).toLowerCase();
      
      return buildingTypeToCheck === normalizedSearchType;
    });
  }

  // Update startProduction to double-check technology requirement
  async function startProduction(item, itemType) {
    try {
      if (!city) {
        showToastNotification("Error: No hay ciudad seleccionada", "error");
        return;
      }
      
      // Check technology requirement again as a security measure
      if (!hasTechnology(item.technology)) {
        showToastNotification(`Se requiere la tecnología "${item.technology}" para producir ${item.name}`, "error");
        return;
      }
      
      // Check if there's already production in progress
      if (city.production && city.production.current_item) {
        showToastNotification("Ya hay una producción en curso", "error");
        return;
      }
      
      // Get the number of turns required for this item
      const turnsToComplete = item.turns_to_build || item.turns || 3;
      
      // Get the proper type/id for production
      const itemId = item.id || item.type_id;
      
      if (!itemId) {
        showToastNotification(`Error: No se puede identificar el tipo de ${itemType === 'troop' ? 'tropa' : 'edificio'}`, "error");
        return;
      }
      
      console.log(`Setting ${itemType} for production:`, itemId);
      
      // Determine the production_type (build, upgrade, train)
      let production_type = itemType === 'troop' ? 'train' : 'build';
      
      // Check if it's a building upgrade
      if (itemType === 'building' && buildingTypeExists(item)) {
        production_type = 'upgrade';
      }
      
      // Create the production object with the proper values
      city.production = {
        current_item: itemId,
        turns_remaining: turnsToComplete,
        itemType: itemType, // Keep for backward compatibility
        production_type: production_type // Add new production_type attribute
      };
      
      console.log("Setting production:", city.production);
      
      // Update the game data with the new production
      if (gameData && gameData.player && gameData.player.cities) {
        const cityIndex = gameData.player.cities.findIndex(c => c.id === city.id);
        if (cityIndex !== -1) {
          gameData.player.cities[cityIndex].production = city.production;
          
          // Save changes to game session
          await gameAPI.updateGameSession(gameData);
          
          // Clear selected item to hide the expanded panel
          if (itemType === 'troop') {
            selectedTroopType = null;
          } else if (itemType === 'building') {
            selectedBuildingType = null;
          }
          
          // Show feedback messages based on production type
          if (production_type === 'upgrade') {
            showToastNotification(`¡Iniciada mejora de ${item.name}!`, "success");
          } else if (production_type === 'build') {
            showToastNotification(`¡Iniciada construcción de ${item.name}!`, "success");
          } else {
            showToastNotification(`¡Iniciado entrenamiento de ${item.name}!`, "success");
          }
          
          // Switch to the summary tab to show the production info
          setActiveTab('summary');
        }
      }
    } catch (err) {
      console.error(`Error starting ${itemType} production:`, err);
      showToastNotification("Error al iniciar la producción", "error");
    }
  }

  // Replace the direct confirm() call with our custom dialog
  async function cancelProduction() {
    try {
      if (!city || !city.production || !city.production.current_item) {
        showToastNotification("No hay producción activa que cancelar", "warning");
        return;
      }
      
      // Get name of item being canceled for better notification
      let itemName = city.production.current_item;
      
      // Find more detailed name if available
      if (city.production.itemType === 'troop') {
        const troopType = troopTypes.find(t => t.id === city.production.current_item || t.type_id === city.production.current_item);
        if (troopType) itemName = troopType.name;
      } else if (city.production.itemType === 'building') {
        const buildingType = buildingTypes.find(b => b.id === city.production.current_item || b.type_id === city.production.current_item);
        if (buildingType) itemName = buildingType.name;
      }
      
      // Store the item name for the confirmation dialog
      itemToCancel = itemName;
      
      // Show the confirmation dialog instead of using browser confirm()
      confirmationMessage = `¿Estás seguro de que quieres cancelar la ${city.production.production_type === 'upgrade' ? 'mejora' : 
        city.production.production_type === 'build' ? 'construcción' : 'producción'} de ${itemName}? No recuperarás ningún recurso.`;
      confirmationCallback = confirmCancelProduction;
      showConfirmationDialog = true;
    } catch (error) {
      console.error("Error al cancelar la producción:", error);
      showToastNotification("Error al cancelar la producción", "error");
    }
  }

  // The function to be called when cancellation is confirmed
  async function confirmCancelProduction() {
    try {
      // Clear the production object
      city.production = {
        current_item: null,
        turns_remaining: 0,
        itemType: null,
        production_type: null
      };
      
      // Update the city in gameData
      if (gameData && gameData.player && gameData.player.cities) {
        const cityIndex = gameData.player.cities.findIndex(c => c.id === city.id);
        if (cityIndex !== -1) {
          gameData.player.cities[cityIndex].production = city.production;
          
          // Save to backend
          await gameAPI.updateGameSession(gameData);
          
          // Show confirmation
          showToastNotification(`Producción de ${itemToCancel} cancelada`, "info");
        }
      }
    } catch (error) {
      console.error("Error al cancelar la producción:", error);
      showToastNotification("Error al cancelar la producción", "error");
    } finally {
      // Reset the confirmation dialog state
      closeConfirmationDialog();
    }
  }

  // Helper function to close the confirmation dialog
  function closeConfirmationDialog() {
    showConfirmationDialog = false;
    confirmationMessage = "";
    confirmationCallback = null;
    itemToCancel = null;
  }

  function showToastNotification(message, type = "info") {
    console.log(`[${type}] ${message}`);
    
    // Create a toast element
    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    toast.innerHTML = `<span class="toast-message">${message}</span>`;
    
    // Create container if it doesn't exist
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    
    // Add toast to container
    container.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  function returnToMap() {
    navigate('/map');
  }

  function getDefaultTroopIcon(type) {
    switch (type && type.toLowerCase()) {
      case 'warrior': return { type: 'image', url: './ia_assets/warrior.png' };
      case 'settler': return { type: 'image', url: './ia_assets/settler.png' };
      case 'archer': return { type: 'image', url: './ia_assets/archer.png' }; // Changed from emoji to image
      case 'cavalry': return { type: 'image', url: './ia_assets/cavalry.png' };
      case 'builder': return { type: 'emoji', value: '🔨' };
      default: return { type: 'emoji', value: '👤' };
    }
  }

  function getBuildingIcon(type) {
    // Convert type to lowercase and remove spaces for comparison
    const normalizedType = type ? type.toLowerCase().replace(/\s+/g, '') : '';
    
    switch (normalizedType) {
      case 'farm': return { type: 'image', url: './ia_assets/farm.jpg' };
      case 'barracks': return { type: 'emoji', value: '⚔️' };
      case 'library': return { type: 'emoji', value: '📚' };
      case 'market': return { type: 'emoji', value: '🏪' };
      case 'wall': return { type: 'emoji', value: '🧱' };
      case 'tower': return { type: 'emoji', value: '🗼' };
      case 'temple': return { type: 'emoji', value: '⛪' };
      // Use the new image paths for specific buildings and fix their type to 'image'
      case 'quarry': return { type: 'image', url: './ia_assets/quarry.jpg' };
      case 'sawmill': return { type: 'image', url: './ia_assets/sawmill.png' };
      case 'ironmine': return { type: 'image', url: './ia_assets/Iron_mine.png' };
      case 'iron_mine': return { type: 'image', url: './ia_assets/Iron_mine.png' };
      case 'goldmine': return { type: 'image', url: './ia_assets/mina_oro.jpg' };
      case 'gold_mine': return { type: 'image', url: './ia_assets/mina_oro.jpg' };
      default: return { type: 'emoji', value: '🏛️' };
    }
  }

  async function upgradeBuilding(building) {
    try {
      if (!city || !city.buildings) {
        showToastNotification("Error: No hay edificios en esta ciudad", "error");
        return;
      }
      
      // Find the building in the city's buildings array
      const buildingIndex = city.buildings.findIndex(b => 
        b.id === building.id || 
        (b.name === building.name && b.type === building.type)
      );
      
      if (buildingIndex === -1) {
        showToastNotification("Error: No se encontró el edificio para mejorar", "error");
        return;
      }
      
      // Define upgrade cost based on building level
      const upgradeCost = {
        gold: 50 * (building.level || 1),
        stone: 30 * (building.level || 1),
        wood: 20 * (building.level || 1)
      };
      
      // Check if player has enough resources
      if (gameData && gameData.player && gameData.player.resources) {
        const playerResources = gameData.player.resources;
        
        if (playerResources.gold < upgradeCost.gold || 
            playerResources.stone < upgradeCost.stone || 
            playerResources.wood < upgradeCost.wood) {
          showToastNotification(`Recursos insuficientes para mejorar. Necesitas: ${upgradeCost.gold} oro, ${upgradeCost.stone} piedra, ${upgradeCost.wood} madera`, "error");
          return;
        }
        
        // Deduct resources
        playerResources.gold -= upgradeCost.gold;
        playerResources.stone -= upgradeCost.stone;
        playerResources.wood -= upgradeCost.wood;
      } else {
        showToastNotification("Error: No se pueden obtener los recursos del jugador", "error");
        return;
      }
      
      // Get a copy of the building to modify (to ensure reactivity)
      const buildingToUpgrade = { ...city.buildings[buildingIndex] };
      
      // Increase the building's level
      buildingToUpgrade.level = (buildingToUpgrade.level || 1) + 1;
      
      // Get the level_upgrade value 
      const levelUpgradeValue = building.level_upgrade || 1;
      
      // Initialize output if it doesn't exist
      if (!buildingToUpgrade.output) {
        buildingToUpgrade.output = {};
      }
      
      // For each resource in the output, increase by level_upgrade
      for (const resource in buildingToUpgrade.output) {
        buildingToUpgrade.output[resource] += levelUpgradeValue;
      }
      
      // If there are no resources in output but the building should produce something,
      // add a default resource based on building type
      if (Object.keys(buildingToUpgrade.output).length === 0) {
        const defaultOutput = getDefaultBuildingOutput(buildingToUpgrade.type || buildingToUpgrade.name);
        buildingToUpgrade.output = defaultOutput;
      }
      
      // Update the city's buildings array
      city.buildings[buildingIndex] = buildingToUpgrade;
      
      // Ensure reactivity by creating a new array
      city.buildings = [...city.buildings];
      
      // Update the game data
      if (gameData && gameData.player && gameData.player.cities) {
        const cityIndex = gameData.player.cities.findIndex(c => c.id === city.id);
        if (cityIndex !== -1) {
          gameData.player.cities[cityIndex].buildings = city.buildings;
          
          // Save changes to backend
          await gameAPI.updateGameSession(gameData);
          
          // Show confirmation
          showToastNotification(`Edificio ${buildingToUpgrade.name} mejorado al nivel ${buildingToUpgrade.level}`, "success");
        }
      }
    } catch (error) {
      console.error("Error al mejorar el edificio:", error);
      showToastNotification("Error al mejorar el edificio", "error");
    }
  }

  // Helper function to get default building output based on type
  function getDefaultBuildingOutput(buildingType) {
    if (!buildingType) return { food: 1 };
    
    const type = buildingType.toLowerCase();
    
    if (type.includes('farm')) {
      return { food: 2 };
    } else if (type.includes('mine') || type.includes('gold')) {
      return { gold: 2 };
    } else if (type.includes('wood') || type.includes('lumber') || type.includes('sawmill')) {
      return { wood: 2 };
    } else if (type.includes('stone') || type.includes('quarry')) {
      return { stone: 2 };
    } else if (type.includes('iron') || type.includes('forge')) {
      return { iron: 2 };
    } else {
      return { food: 1 }; // Default to food if type is unknown
    }
  }

  onMount(async () => {
    try {
      document.body.classList.add('city-active');
      document.documentElement.classList.add('city-active');

      if (!$user) {
        navigate('/');
        return;
      }
      
      gameData = await gameAPI.getCurrentGame();
      if (!gameData) {
        throw new Error("No hay datos de juego disponibles.");
      }
      
      const selectedCityId = await gameAPI.getTemporaryData('selectedCityId');
      if (!selectedCityId) {
        // Improved error handling with more specific error
        showToastNotification("No se ha seleccionado ninguna ciudad. Volviendo al mapa...", "error");
        setTimeout(() => navigate('/map'), 1500);
        throw new Error("No se ha seleccionado ninguna ciudad.");
      }
      
      if (gameData.player && gameData.player.cities) {
        city = gameData.player.cities.find(c => c.id === selectedCityId);
      }
      
      if (!city) {
        // Improved error handling when city isn't found
        showToastNotification("La ciudad seleccionada no se encontró. Volviendo al mapa...", "error");
        setTimeout(() => navigate('/map'), 1500);
        throw new Error("No se encontró la ciudad seleccionada.");
      }
      
      // Only fetch these if we have a valid city
      await fetchTroopTypes();
      await fetchBuildingTypes();
      await fetchTechnologyTypes();

      // NEW: Debug player technologies
      debugTechnologies();
      
      isLoading = false;
    } catch (err) {
      console.error("Error loading city:", err);
      error = err.message;
      isLoading = false;
    }
  });

  onDestroy(() => {
    document.body.classList.remove('city-active');
    document.documentElement.classList.remove('city-active');
  });
</script>

<svelte:head>
  <title>Ciudad {city ? city.name : ''} - Civilization Game</title>
</svelte:head>

<div class="city-page game-view">
  <div class="city-background"></div>
  
  <button class="back-button" on:click={returnToMap}>← Volver al Mapa</button>
  
  {#if isLoading}
    <div class="loading-container">
      <div class="loading-spinner"></div>
      <h2>Cargando datos de la ciudad...</h2>
    </div>
  {:else if error}
    <div class="error-container">
      <h2>Error al cargar la ciudad</h2>
      <p>{error}</p>
      <button class="retry-button" on:click={returnToMap}>Volver al Mapa</button>
    </div>
  {:else if city}
    <div class="content-container">
      <div class="city-overlay-panel">
        <div class="city-header">
          <h1>{city.name}</h1>
          <div class="population-indicator">
            <span class="population-icon">👥</span>
            <span class="population-value">{city.population || 0}</span>
          </div>
        </div>
        
        <div class="city-tabs">
          <button 
            class="tab-button" 
            class:active={activeTab === 'summary'} 
            on:click={() => setActiveTab('summary')}
          >
            Resumen
          </button>
          <button 
            class="tab-button" 
            class:active={activeTab === 'production'} 
            on:click={() => setActiveTab('production')}
          >
            Producción
          </button>
          <button 
            class="tab-button" 
            class:active={activeTab === 'buildings'} 
            on:click={() => setActiveTab('buildings')}
          >
            Edificios
          </button>
          <button 
            class="tab-button" 
            class:active={activeTab === 'library'} 
            on:click={() => setActiveTab('library')}
          >
            Biblioteca
          </button>
        </div>
        
        <div class="city-content">
          <div class="tab-content" class:active={activeTab === 'summary'}>
            <h3>Resumen de la Ciudad</h3>
            <p>Panel de gestión de la ciudad. Aquí se mostrarán más opciones en futuras implementaciones.</p>
            
            <div class="info-section">
              <h4>Información</h4>
              <p><strong>Posición:</strong> {Array.isArray(city.position) ? 
                `${city.position[0]}, ${city.position[1]}` : 
                `${city.position.x}, ${city.position.y}`}</p>
            </div>
            
            {#if city.buildings && city.buildings.length > 0}
              <div class="info-section">
                <h4>Edificios ({city.buildings.length})</h4>
                <ul class="buildings-list">
                  {#each city.buildings as building}
                    <li>{building.name || building}</li>
                  {/each}
                </ul>
              </div>
            {:else}
              <div class="info-section">
                <h4>Edificios</h4>
                <p>No hay edificios construidos en esta ciudad.</p>
              </div>
            {/if}
            
            {#if city.production && city.production.current_item}
              {@const isProducingTroop = !city.production.itemType || city.production.itemType === 'troop'}
              {@const productionType = isProducingTroop 
                ? troopTypes.find(t => t.id === city.production.current_item || t.type_id === city.production.current_item)
                : buildingTypes.find(b => b.id === city.production.current_item || b.type_id === city.production.current_item)}
              <div class="info-section production-status-section">
                <h4>
                  {#if city.production.production_type === 'upgrade'}
                    Mejora en Curso
                  {:else if city.production.production_type === 'build' || !city.production.production_type && !isProducingTroop}
                    Construcción en Curso
                  {:else}
                    Producción Actual
                  {/if}
                </h4>
                <div class="production-type-badge {isProducingTroop ? 'troop' : 
                  city.production.production_type === 'upgrade' ? 'upgrade' : 'building'}">
                  {#if city.production.production_type === 'upgrade'}
                    Mejora
                  {:else if city.production.production_type === 'build' || !city.production.production_type && !isProducingTroop}
                    Construcción
                  {:else}
                    Entrenamiento
                  {/if}
                </div>
                <div class="production-item">
                  <div class="production-icon">
                    {#if isProducingTroop}
                      {#if productionType && getDefaultTroopIcon(productionType.name).type === 'image'}
                        <img src={getDefaultTroopIcon(productionType.name).url} alt={productionType ? productionType.name : city.production.current_item} class="production-image" />
                      {:else}
                        <span class="production-emoji">
                          {productionType ? getDefaultTroopIcon(productionType.name).value : '🛠️'}
                        </span>
                      {/if}
                    {:else}
                      {#if productionType && getBuildingIcon(productionType.type || productionType.name).type === 'image'}
                        <img src={getBuildingIcon(productionType.type || productionType.name).url} alt={productionType ? productionType.name : city.production.current_item} class="production-image" />
                      {:else}
                        <span class="production-emoji">
                          {productionType ? getBuildingIcon(productionType.type || productionType.name).value : '🏗️'}
                        </span>
                      {/if}
                    {/if}
                  </div>
                  <div class="production-details">
                    <span class="production-name">
                      {productionType ? productionType.name : city.production.current_item}
                    </span>
                    <div class="production-progress">
                      <div class="progress-bar" style="width: {100 - (city.production.turns_remaining * 100 / (productionType?.turns_to_build || productionType?.turns || 3))}%;"></div>
                      <span class="progress-text">{city.production.turns_remaining} turnos restantes</span>
                    </div>
                    <button class="cancel-production-button" on:click={cancelProduction}>Cancelar Producción</button>
                  </div>
                </div>
              </div>
            {:else}
              <div class="info-section">
                <h4>Producción</h4>
                <p>No hay producción en curso.</p>
                <button class="start-production-button" on:click={() => setActiveTab('production')}>Iniciar Producción</button>
              </div>
            {/if}
          </div>
          
          <div class="tab-content" class:active={activeTab === 'production'}>
            <h3>Producción</h3>
            <p>En este panel podrás gestionar qué construye tu ciudad.</p>
            
            <div class="info-section">
              <h4>Producción Actual</h4>
              {#if city.production && city.production.current_item}
                {@const isProducingTroop = !city.production.itemType || city.production.itemType === 'troop'}
                {@const productionType = isProducingTroop 
                  ? troopTypes.find(t => t.id === city.production.current_item || t.type_id === city.production.current_item)
                  : buildingTypes.find(b => b.id === city.production.current_item || b.type_id === city.production.current_item)}
                <div class="production-item">
                  <div class="production-icon">
                    {#if isProducingTroop}
                      {#if productionType && getDefaultTroopIcon(productionType.name).type === 'image'}
                        <img src={getDefaultTroopIcon(productionType.name).url} alt={productionType ? productionType.name : city.production.current_item} class="production-image" />
                      {:else}
                        <span class="production-emoji">
                          {productionType ? getDefaultTroopIcon(productionType.name).value : '🛠️'}
                        </span>
                      {/if}
                    {:else}
                      {#if productionType && getBuildingIcon(productionType.type || productionType.name).type === 'image'}
                        <img src={getBuildingIcon(productionType.type || productionType.name).url} alt={productionType ? productionType.name : city.production.current_item} class="production-image" />
                      {:else}
                        <span class="production-emoji">
                          {productionType ? getBuildingIcon(productionType.type || productionType.name).value : '🏗️'}
                        </span>
                      {/if}
                    {/if}
                  </div>
                  <div class="production-details">
                    <span class="production-name">
                      {productionType ? productionType.name : city.production.current_item}
                    </span>
                    <div class="production-progress">
                      <div class="progress-bar" style="width: {100 - (city.production.turns_remaining * 100 / (productionType?.turns_to_build || productionType?.turns || 3))}%;"></div>
                      <span class="progress-text">{city.production.turns_remaining} turnos restantes</span>
                    </div>
                    <button class="cancel-production-button" on:click={cancelProduction}>Cancelar Producción</button>
                  </div>
                </div>
              {:else}
                <p>No hay producción en curso. Selecciona una unidad para comenzar la producción.</p>
              {/if}
            </div>
            
            <div class="info-section">
              <h4>Construir</h4>
              <div class="production-options">
                <div class="production-option">
                  <h5>Unidades</h5>
                  {#if loadingTroopTypes}
                    <p>Cargando tipos de tropas...</p>
                  {:else if troopTypes.length === 0}
                    <p>No hay tipos de tropas disponibles.</p>
                  {:else}
                    {#each troopTypes as troopType, index}
                      {@const uniqueKey = troopType.id || `troop-type-${index}`}
                      {@const iconData = getDefaultTroopIcon(troopType.name)}
                      {@const isLocked = !hasTechnology(troopType.technology)}
                      <div class="troop-container">
                        <button 
                          class="production-button troop-button {isLocked ? 'locked' : ''}" 
                          class:expanded={selectedTroopType && (selectedTroopType._uniqueId === (troopType.id || `troop-${index}`))}
                          on:click={() => toggleTroopSelection(troopType, index)}
                        >
                          <div class="troop-info">
                            {#if iconData.type === 'image'}
                              <div class="troop-image-container {isLocked ? 'locked' : ''}">
                                <img src={iconData.url} alt={troopType.name} class="troop-image" />
                                {#if isLocked}
                                  <div class="lock-overlay">🔒</div>
                                {/if}
                              </div>
                            {:else}
                              <span class="troop-icon {isLocked ? 'locked' : ''}">{iconData.value}</span>
                              {#if isLocked}
                                <span class="lock-icon">🔒</span>
                              {/if}
                            {/if}
                            
                            <div class="troop-details">
                              <span class="troop-name">{troopType.name}</span>
                              <span class="troop-cost">{@html getResourceCostString(troopType.cost)}</span>
                              {#if isLocked && troopType.technology}
                                <span class="tech-requirement">Requiere: {troopType.technology}</span>
                              {/if}
                            </div>
                            <span class="production-turns">
                              <span class="turns-icon">🕒</span>
                              <span class="turns-count">{troopType.turns_to_build || troopType.turns || '?'}</span>
                              <span class="turns-label">turnos</span>
                            </span>
                          </div>
                        </button>
                        
                        {#if selectedTroopType && (selectedTroopType._uniqueId === (troopType.id || `troop-${index}`))}
                          <div class="troop-details-expanded">
                            <div class="troop-attributes">
                              {#if troopType.description}
                                <p class="troop-description">{troopType.description}</p>
                              {/if}
                              
                              <div class="attributes-grid">
                                {#if troopType.attack !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">⚔️</span>
                                    <span class="attribute-label">Ataque:</span>
                                    <span class="attribute-value">{troopType.attack}</span>
                                  </div>
                                {/if}
                                
                                {#if troopType.defense !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">🛡️</span>
                                    <span class="attribute-label">Defensa:</span>
                                    <span class="attribute-value">{troopType.defense}</span>
                                  </div>
                                {/if}
                                
                                {#if troopType.health !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">❤️</span>
                                    <span class="attribute-label">Salud:</span>
                                    <span class="attribute-value">{troopType.health}</span>
                                  </div>
                                {/if}
                                
                                {#if troopType.movement !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">👣</span>
                                    <span class="attribute-label">Movimiento:</span>
                                    <span class="attribute-value">{troopType.movement}</span>
                                  </div>
                                {/if}
                                
                                {#if troopType.range !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">🎯</span>
                                    <span class="attribute-label">Alcance:</span>
                                    <span class="attribute-value">{troopType.range}</span>
                                  </div>
                                {/if}
                              </div>
                              
                              <div class="troop-action">
                                <button class="train-button" on:click={() => startProduction(troopType, 'troop')}>
                                  Entrenar {troopType.name}
                                </button>
                              </div>
                            </div>
                          </div>
                        {/if}
                      </div>
                    {/each}
                  {/if}
                </div>
                <div class="production-option">
                  <h5>Edificios</h5>
                  {#if loadingBuildingTypes}
                    <p>Cargando tipos de edificios...</p>
                  {:else if buildingTypes.length === 0}
                    <p>No hay tipos de edificios disponibles.</p>
                  {:else}
                    {#each buildingTypes as buildingType, index}
                      {@const uniqueKey = buildingType.id || `building-type-${index}`}
                      {@const iconData = getBuildingIcon(buildingType.type || buildingType.name)}
                      {@const existingBuilding = getExistingBuilding(buildingType)}
                      {@const isLocked = !hasTechnology(buildingType.technology)}
                      <div class="building-container">
                        <button 
                          class="production-button building-button {existingBuilding ? 'existing-building' : ''} {isLocked ? 'locked' : ''}" 
                          class:expanded={selectedBuildingType && (selectedBuildingType._uniqueId === (buildingType.id || `building-${index}`))}
                          on:click={() => toggleBuildingSelection(buildingType, index)}
                        >
                          <div class="building-info">
                            {#if iconData.type === 'image'}
                              <div class="building-image-container {isLocked ? 'locked' : ''}">
                                <img src={iconData.url} alt={buildingType.name} class="building-image" />
                                {#if isLocked}
                                  <div class="lock-overlay">🔒</div>
                                {/if}
                              </div>
                            {:else}
                              <span class="building-icon {isLocked ? 'locked' : ''}">{iconData.value}</span>
                              {#if isLocked}
                                <span class="lock-icon">🔒</span>
                              {/if}
                            {/if}
                            
                            <div class="building-details">
                              <span class="building-name">{buildingType.name}</span>
                              <span class="building-status">
                                {#if existingBuilding}
                                  {#if typeof existingBuilding === 'string'}
                                    <span class="building-level">Construido</span>
                                  {:else}
                                    <span class="building-level">Nivel {existingBuilding.level || 1}</span>
                                  {/if}
                                {:else}
                                  <span class="building-cost">{@html getResourceCostString(buildingType.cost)}</span>
                                {/if}
                              </span>
                              {#if isLocked && buildingType.technology}
                                <span class="tech-requirement">Requiere: {buildingType.technology}</span>
                              {/if}
                            </div>
                            <span class="production-turns">
                              <span class="turns-icon">🕒</span>
                              <span class="turns-count">{buildingType.turns_to_build || buildingType.turns || '?'}</span>
                              <span class="turns-label">turnos</span>
                            </span>
                          </div>
                        </button>
                        
                        {#if selectedBuildingType && (selectedBuildingType._uniqueId === (buildingType.id || `building-${index}`))}
                          {@const existingBuilding = getExistingBuilding(buildingType)}
                          <div class="building-details-expanded">
                            <div class="building-attributes">
                              {#if buildingType.description}
                                <p class="building-description">{buildingType.description}</p>
                              {/if}
                              
                              <div class="attributes-grid">
                                <!-- Level Information -->
                                {#if buildingType.level !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">⭐</span>
                                    <span class="attribute-label">Nivel:</span>
                                    <span class="attribute-value">{buildingType.level}</span>
                                  </div>
                                {/if}
                                
                                <!-- Level Upgrade Cost -->
                                {#if buildingType.level_upgrade !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">⬆️</span>
                                    <span class="attribute-label">Mejora:</span>
                                    <span class="attribute-value">{buildingType.level_upgrade}</span>
                                  </div>
                                {/if}
                                
                                <!-- Output Resources -->
                                {#if buildingType.output}
                                  <!-- Replace the original output display with more compact version -->
                                  <div class="resource-output-attribute">
                                    <div class="resource-output-header">
                                      <span class="attribute-icon">⚒️</span>
                                      <span class="attribute-label">Producción</span>
                                    </div>
                                    {#each Object.entries(buildingType.output) as [resource, amount]}
                                      <div class="resource-item">
                                        <span class="resource-icon-container">
                                          {#if resource === 'food'}
                                            <img src="./ia_assets/janaria.png" alt="Food" class="resource-icon-small" />
                                          {:else if resource === 'gold'}
                                            <img src="./ia_assets/lingotes_oro.png" alt="Gold" class="resource-icon-small" />
                                          {:else if resource === 'wood'}
                                            <img src="./ia_assets/zuhaitza.png" alt="Wood" class="resource-icon-small" />
                                          {:else if resource === 'stone'}
                                            <img src="./ia_assets/harria.png" alt="Stone" class="resource-icon-small" />
                                          {:else if resource === 'iron'}
                                            <img src="./ia_assets/lingote_hierro.png" alt="Iron" class="resource-icon-small" />
                                          {:else}
                                            {resource} 
                                          {/if}
                                        </span>
                                        <span class="resource-name">{resource}:</span>
                                        <span class="resource-output-value">+{amount}</span>
                                      </div>
                                    {/each}
                                  </div>
                                {/if}
                                
                                <!-- Other building attributes -->
                                {#if buildingType.production_bonus !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">⚒️</span>
                                    <span class="attribute-label">Producción:</span>
                                    <span class="attribute-value">+{buildingType.production_bonus}%</span>
                                  </div>
                                {/if}
                                
                                {#if buildingType.research_bonus !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">📚</span>
                                    <span class="attribute-label">Investigación:</span>
                                    <span class="attribute-value">+{buildingType.research_bonus}%</span>
                                  </div>
                                {/if}
                                
                                {#if buildingType.defense_bonus !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">🛡️</span>
                                    <span class="attribute-label">Defensa:</span>
                                    <span class="attribute-value">+{buildingType.defense_bonus}%</span>
                                  </div>
                                {/if}
                              </div>
                              
                              <div class="building-action">
                                {#if existingBuilding}
                                  <button class="upgrade-button" on:click={() => startProduction(buildingType, 'building')}>
                                    Mejorar {buildingType.name}
                                  </button>
                                {:else}
                                  <button class="construct-button" on:click={() => startProduction(buildingType, 'building')}>
                                    Construir {buildingType.name}
                                  </button>
                                {/if}
                              </div>
                            </div>
                          </div>
                        {/if}
                      </div>
                    {/each}
                  {/if}
                </div>
              </div>
            </div>
          </div>
          
          <div class="tab-content" class:active={activeTab === 'buildings'}>
            <h3>Edificios</h3>
            <p>Gestiona los edificios de tu ciudad.</p>
            
            {#if city.buildings && city.buildings.length > 0}
              <div class="info-section buildings-grid">
                {#each city.buildings as buildingItem}
                  {@const building = getBuildingDetails(buildingItem)}
                  {@const iconData = getBuildingIcon(building.type || building.name)}
                  <div class="building-card">
                    <div class="building-icon-wrapper">
                      {#if iconData.type === 'image'}
                        <img src={iconData.url} alt={building.name} class="building-image" />
                      {:else}
                        <span class="building-icon">{iconData.value}</span>
                      {/if}
                    </div>
                    <h4>{building.name}</h4>
                    
                    {#if building.description}
                      <p class="building-description">{building.description}</p>
                    {:else}
                      <p class="building-description">Edificio de la ciudad.</p>
                    {/if}
                    
                    <div class="building-stats">
                      <!-- Level Information -->
                      <div class="building-stat">
                        <span class="stat-icon">⭐</span>
                        <span class="stat-label">Nivel:</span>
                        <span class="stat-value">{building.level || 1}</span>
                      </div>
                      
                      <!-- Output Resources -->
                      {#if building.output}
                        {#each Object.entries(building.output) as [resource, amount]}
                          <div class="building-stat resource-output">
                            <span class="stat-icon">
                              {#if resource === 'food'}
                                <img src="./ia_assets/janaria.png" alt="Food" class="resource-icon-small" />
                              {:else if resource === 'gold'}
                                <img src="./ia_assets/lingotes_oro.png" alt="Gold" class="resource-icon-small" />
                              {:else if resource === 'wood'}
                                <img src="./ia_assets/zuhaitza.png" alt="Wood" class="resource-icon-small" />
                              {:else if resource === 'stone'}
                                <img src="./ia_assets/harria.png" alt="Stone" class="resource-icon-small" />
                              {:else if resource === 'iron'}
                                <img src="./ia_assets/lingote_hierro.png" alt="Iron" class="resource-icon-small" />
                              {:else}
                                {resource} 
                              {/if}
                            </span>
                            <span class="stat-label">Producción:</span>
                            <span class="stat-value">+{amount}/turno</span>
                          </div>
                        {/each}
                      {/if}
                      
                      <!-- Level Upgrade Information -->
                      {#if building.level_upgrade !== undefined}
                        <div class="building-stat upgrade-info">
                          <span class="stat-icon">⬆️</span>
                          <span class="stat-label">Mejora al siguiente nivel:</span>
                          <span class="stat-value">{building.level_upgrade}</span>
                        </div>
                      {/if}
                      
                      <!-- Other building stats -->
                      {#if building.production_bonus !== undefined}
                        <div class="building-stat">
                          <span class="stat-icon">⚒️</span>
                          <span class="stat-label">Producción:</span>
                          <span class="stat-value">+{building.production_bonus}%</span>
                        </div>
                      {/if}
                      
                      {#if building.research_bonus !== undefined}
                        <div class="building-stat">
                          <span class="stat-icon">📚</span>
                          <span class="stat-label">Investigación:</span>
                          <span class="stat-value">+{building.research_bonus}%</span>
                        </div>
                      {/if}
                      
                      {#if building.defense_bonus !== undefined}
                        <div class="building-stat">
                          <span class="stat-icon">🛡️</span>
                          <span class="stat-label">Defensa:</span>
                          <span class="stat-value">+{building.defense_bonus}%</span>
                        </div>
                      {/if}
                      
                      {#if building.food_bonus !== undefined}
                        <div class="building-stat">
                          <span class="stat-icon">🌾</span>
                          <span class="stat-label">Alimento:</span>
                          <span class="stat-value">+{building.food_bonus}%</span>
                        </div>
                      {/if}
                      
                      {#if building.gold_bonus !== undefined}
                        <div class="building-stat">
                          <span class="stat-icon">💰</span>
                          <span class="stat-label">Oro:</span>
                          <span class="stat-value">+{building.gold_bonus}%</span>
                        </div>
                      {/if}
                    </div>
                    
                    <!-- Upgrade Building Button -->
                    {#if building.level !== undefined && building.level_upgrade !== undefined}
                      <div class="building-upgrade">
                        <button class="upgrade-button" on:click={() => upgradeBuilding(building)}>Mejorar a Nivel {building.level + 1}</button>
                      </div>
                    {/if}
                  </div>
                {/each}
              </div>
            {:else}
              <div class="info-section">
                <p>No hay edificios construidos en esta ciudad.</p>
                <button class="action-button" on:click={() => setActiveTab('production')}>Construir Edificios</button>
              </div>
            {/if}
          </div>

          <div class="tab-content" class:active={activeTab === 'library'}>
            <h3>Biblioteca y Tecnologías</h3>
            {#if cityHasLibrary()}
              <p>Investiga nuevas tecnologías para mejorar tu civilización.</p>
              
              {#if city.research && city.research.current_technology}
                {@const researchTech = technologyTypes.find(t => t.id === city.research.current_technology)}
                <div class="info-section research-status-section">
                  <h4>Investigación en Curso</h4>
                  <div class="production-type-badge research">Investigación</div>
                  <div class="production-item">
                    <div class="production-icon">
                      <span class="production-emoji">
                        {researchTech ? researchTech.icon : '📚'}
                      </span>
                    </div>
                    <div class="production-details">
                      <span class="production-name">
                        {researchTech ? researchTech.name : city.research.current_technology}
                      </span>
                      <div class="production-progress">
                        <div class="progress-bar" style="width: {100 - (city.research.turns_remaining * 100 / (researchTech?.turns || 10))}%;"></div>
                        <span class="progress-text">{city.research.turns_remaining} turnos restantes</span>
                      </div>
                      <button class="cancel-production-button" on:click={cancelResearch}>Cancelar Investigación</button>
                    </div>
                  </div>
                </div>
              {/if}
              
              <div class="info-section">
                <h4>Tecnologías Disponibles</h4>
                {#if loadingTechnologyTypes}
                  <p>Cargando tecnologías...</p>
                {:else if technologyTypes.length === 0}
                  <p>No hay tecnologías disponibles.</p>
                {:else}
                  <div class="technologies-list">
                    {#each technologyTypes as technology}
                      {@const isResearched = isTechnologyResearched(technology.id)}
                      {@const isResearching = city.research && city.research.current_technology === technology.id}
                      {@const canResearch = !isResearched && !isResearching && city.population >= technology.min_civilians}
                      {@const hasMissingPrereqs = technology.prerequisites && technology.prerequisites.some(prereq => !isTechnologyResearched(prereq))}
                      
                      <div class="technology-container">
                        <div class="technology-card {isResearched ? 'researched' : ''} {isResearching ? 'researching' : ''} {!canResearch || hasMissingPrereqs ? 'disabled' : ''}">
                          <div class="technology-icon">{technology.icon}</div>
                          <div class="technology-details">
                            <h4 class="technology-name">{technology.name}</h4>
                            <p class="technology-description">{technology.description}</p>
                            
                            {#if isResearched}
                              <div class="technology-status">Investigada</div>
                            {:else if isResearching}
                              <div class="technology-status">En progreso ({city.research.turns_remaining} turnos)</div>
                            {:else}
                              <div class="technology-requirements">
                                <div class="technology-req {city.population >= technology.min_civilians ? 'met' : ''}">
                                  <span class="req-icon">👥</span>
                                  <span class="req-label">Población:</span>
                                  <span class="req-value">{city.population}/{technology.min_civilians}</span>
                                </div>
                                
                                {#if technology.prerequisites && technology.prerequisites.length > 0}
                                  <div class="technology-prereqs">
                                    <span class="req-icon">📋</span>
                                    <span class="req-label">Requisitos:</span>
                                    <span class="req-value">
                                      {#each technology.prerequisites as prereq}
                                        {@const prereqName = technologyTypes.find(t => t.id === prereq)?.name || prereq}
                                        <span class="prereq-item {isTechnologyResearched(prereq) ? 'met' : ''}">{prereqName}</span>
                                      {/each}
                                    </span>
                                  </div>
                                {/if}
                                
                                <div class="technology-time">
                                  <span class="req-icon">⏳</span>
                                  <span class="req-label">Tiempo:</span>
                                  <span class="req-value">{technology.turns} turnos</span>
                                </div>
                              </div>
                              
                              <button 
                                class="research-button" 
                                disabled={!canResearch || hasMissingPrereqs || (city.research && city.research.current_technology)}
                                on:click={() => startResearch(technology)}
                              >
                                Investigar
                              </button>
                            {/if}
                          </div>
                        </div>
                        
                        {#if technology.unlocks && technology.unlocks.length > 0}
                          <div class="technology-unlocks">
                            <h5>Desbloquea:</h5>
                            <div class="unlocks-list">
                              {#each technology.unlocks as unlock}
                                <span class="unlock-item">{unlock}</span>
                              {/each}
                            </div>
                          </div>
                        {/if}
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>
            {:else}
              <div class="info-section">
                <p>Para investigar tecnologías, primero debes construir una Biblioteca en esta ciudad.</p>
                <button class="action-button" on:click={() => setActiveTab('production')}>Construir Biblioteca</button>
              </div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  {/if}

  {#if gameData && gameData.player && gameData.player.resources}
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
      <div class="resource iron">
        <div class="resource-icon">
          <img src="./ia_assets/lingote_hierro.png" alt="Iron" class="resource-bar-icon" />
        </div>
        <div class="resource-value">{gameData.player.resources.iron || 0}</div>
      </div>
      <div class="resource stone">
        <div class="resource-icon">
          <img src="./ia_assets/harria.png" alt="Stone" class="resource-bar-icon" />
        </div>
        <div class="resource-value">{gameData.player.resources.stone || 0}</div>
      </div>
    </div>
  {/if}

  {#if showConfirmationDialog}
    <div class="modal-overlay">
      <div class="confirmation-dialog">
        <h3>Confirmar Acción</h3>
        <p>{confirmationMessage}</p>
        
        <div class="confirmation-actions">
          <button class="cancel-button" on:click={closeConfirmationDialog}>Cancelar</button>
          <button class="confirm-button" on:click={confirmationCallback}>Confirmar</button>
        </div>
      </div>
    </div>
  {/if}
</div>
