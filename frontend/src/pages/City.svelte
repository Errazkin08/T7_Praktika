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

  // NUEVO: Estado para el diálogo de confirmación de producción
  let showProductionConfirmationDialog = false;
  let productionConfirmationMessage = "";
  let productionConfirmationCallback = null;
  let productionItemToStart = null;
  let productionItemTypeToStart = null;
  let productionItemCostToShow = null;

  // Add a helper function to render costs dynamically based on what's in the cost object
  function getResourceCostString(costObject) {
    if (!costObject) return 'Kostua ez dago eskuragarri';
    
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
    
    return resourceDisplay.length > 0 ? resourceDisplay.join(' ') : 'Kostua ez dago eskuragarri';
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
        showToastNotification("Errorea: Ez dago hiririk hautatuta", "error");
        return;
      }
      
      // Find the library building
      const library = findLibraryBuilding();
      if (!library) {
        showToastNotification("Hiriak liburutegi bat behar du teknologiak ikertzeko", "error");
        return;
      }
      
      // Check if there's already research in progress
      if ((library.production && library.production.current_technology) || 
          (city.research && city.research.current_technology)) {
        showToastNotification("Dagoeneko ikerketa bat martxan dago", "error");
        return;
      }
      
      // Check if population meets minimum requirement
      if (city.population < technology.min_civilians) {
        showToastNotification(`Teknologia hau ikertzeko gutxienez ${technology.min_civilians} herritar behar dira`, "error");
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
          showToastNotification(`Aurretiko teknologiak falta dira: ${missingPrereqs.join(", ")}`, "error");
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
          showToastNotification(`¡${technology.name} ikerketa hasi da!`, "success");
          
          // Switch to the summary tab to show the research info
          setActiveTab('summary');
        }
      }
    } catch (err) {
      console.error("Error starting research:", err);
      showToastNotification("Errorea ikerketa hasterakoan", "error");
    }
  }

  // Updated cancel research function to clear from library
  async function cancelResearch() {
    try {
      const library = findLibraryBuilding();
      const hasLibraryResearch = library && library.production && library.production.current_technology;
      const hasCityResearch = city && city.research && city.research.current_technology;
      
      if (!hasLibraryResearch && !hasCityResearch) {
        showToastNotification("Ez dago ezeztatzeko ikerketa aktiborik", "warning");
        return;
      }

      // Get a more readable name if available
      const techId = hasLibraryResearch ? library.production.current_technology : city.research.current_technology;
      const techName = hasLibraryResearch ? library.production.technology_name : null;
      const techType = technologyTypes.find(t => t.id === techId);
      const displayName = techName || (techType ? techType.name : techId);
      
      // Show the confirmation dialog
      confirmationMessage = `Ziur zaude ${displayName} ikerketa ezeztatu nahi duzula? Ez duzu aurrerapenik berreskuratuko.`;
      confirmationCallback = confirmCancelResearch;
      showConfirmationDialog = true;
    } catch (error) {
      console.error("Errorea ikerketa ezeztatzean:", error);
      showToastNotification("Errorea ikerketa ezeztatzean", "error");
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
          showToastNotification("Ikerketa ezeztatu da", "info");
        }
      }
    } catch (error) {
      console.error("Errorea ikerketa ezeztatzean:", error);
      showToastNotification("Errorea ikerketa ezeztatzean", "error");
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
      showToastNotification(`"${troopType.technology}" teknologia beharrezkoa da ${troopType.name} egiteko`, "warning");
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
      showToastNotification(`"${buildingType.technology}" teknologia beharrezkoa da ${buildingType.name} egiteko`, "warning");
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

  // NUEVO: Función para mostrar el diálogo de confirmación de producción
  function confirmStartProduction(item, itemType) {
    // Mostrar el coste en el mensaje
    const costString = getResourceCostString(item.cost);
    productionConfirmationMessage = `${itemType === 'troop' ? 'Unitate honen ekoizpena' : (buildingTypeExists(item) ? 'Eraikin honen hobekuntza' : 'Eraikin honen eraikuntza')} "${item.name}" hasi nahi duzu?\nKostua: ${costString}`;
    productionConfirmationCallback = () => doStartProduction(item, itemType);
    productionItemToStart = item;
    productionItemTypeToStart = itemType;
    productionItemCostToShow = item.cost;
    showProductionConfirmationDialog = true;
  }

  // NUEVO: Función que realmente inicia la producción tras confirmar
  async function doStartProduction(item, itemType) {
    showProductionConfirmationDialog = false;
    productionConfirmationMessage = "";
    productionConfirmationCallback = null;
    productionItemToStart = null;
    productionItemTypeToStart = null;
    productionItemCostToShow = null;
    await startProduction(item, itemType);
  }

  // NUEVO: Cerrar el diálogo de confirmación de producción
  function closeProductionConfirmationDialog() {
    showProductionConfirmationDialog = false;
    productionConfirmationMessage = "";
    productionConfirmationCallback = null;
    productionItemToStart = null;
    productionItemTypeToStart = null;
    productionItemCostToShow = null;
  }

  // Modificado: startProduction ahora descuenta recursos y comprueba antes de iniciar
  async function startProduction(item, itemType) {
    try {
      if (!city) {
        showToastNotification("Errorea: Ez dago hiririk hautatuta", "error");
        return;
      }

      // Check technology requirement again as a security measure
      if (!hasTechnology(item.technology)) {
        showToastNotification(`"${item.technology}" teknologia beharrezkoa da ${item.name} ekoizteko`, "error");
        return;
      }

      // Check if there's already production in progress
      if (city.production && city.production.current_item) {
        showToastNotification("Dagoeneko ekoizpen bat martxan dago", "error");
        return;
      }

      // Obtener el coste del item
      const cost = item.cost || {};
      // Comprobar si el jugador (o IA) tiene suficientes recursos para TODOS los recursos requeridos
      if (gameData && gameData.player && gameData.player.resources) {
        const playerResources = gameData.player.resources;
        // Comprobar todos los recursos antes de restar
        let canAfford = true;
        for (const resource in cost) {
          if (cost[resource] > 0 && (!playerResources[resource] || playerResources[resource] < cost[resource])) {
            canAfford = false;
            break;
          }
        }
        if (!canAfford) {
          showToastNotification("Ez duzu nahikoa baliabide ekoizpena hasteko", "error");
          return;
        }
        // Restar todos los recursos (solo si puede pagarlos todos)
        for (const resource in cost) {
          if (cost[resource] > 0) {
            playerResources[resource] -= cost[resource];
          }
        }
      } else {
        showToastNotification("Errorea: Ezin dira jokalariaren baliabideak lortu", "error");
        return;
      }

      // Get the number of turns required for this item
      const turnsToComplete = item.turns_to_build || item.turns || 3;

      // Get the proper type/id for production
      const itemId = item.id || item.type_id;

      if (!itemId) {
        showToastNotification(`Errorea: Ezin da ${itemType === 'troop' ? 'tropa' : 'eraikina'} identifikatu`, "error");
        return;
      }

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

      // Update the game data with the new production
      if (gameData && gameData.player && gameData.player.cities) {
        const cityIndex = gameData.player.cities.findIndex(c => c.id === city.id);
        if (cityIndex !== -1) {
          gameData.player.cities[cityIndex].production = city.production;
          // Guardar también los recursos actualizados
          gameData.player.resources = { ...gameData.player.resources };

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
            showToastNotification(`¡${item.name} hobekuntza hasi da!`, "success");
          } else if (production_type === 'build') {
            showToastNotification(`¡${item.name} eraikuntza hasi da!`, "success");
          } else {
            showToastNotification(`¡${item.name} trebakuntza hasi da!`, "success");
          }

          // Switch to the summary tab to show the production info
          setActiveTab('summary');
        }
      }
    } catch (err) {
      console.error(`Errorea ${itemType} ekoizpena hasterakoan:`, err);
      showToastNotification("Errorea ekoizpena hasterakoan", "error");
    }
  }

  // Replace the direct confirm() call with our custom dialog
  async function cancelProduction() {
    try {
      if (!city || !city.production || !city.production.current_item) {
        showToastNotification("Ez dago ezeztatzeko ekoizpen aktiborik", "warning");
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
      confirmationMessage = `Ziur zaude ${city.production.production_type === 'upgrade' ? 'hobekuntza' : 
        city.production.production_type === 'build' ? 'eraikuntza' : 'ekoizpena'} ezeztatu nahi duzula ${itemName}? Ez duzu baliabiderik berreskuratuko.`;
      confirmationCallback = confirmCancelProduction;
      showConfirmationDialog = true;
    } catch (error) {
      console.error("Errorea ekoizpena ezeztatzean:", error);
      showToastNotification("Errorea ekoizpena ezeztatzean", "error");
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
          showToastNotification(`${itemToCancel} ekoizpena ezeztatu da`, "info");
        }
      }
    } catch (error) {
      console.error("Errorea ekoizpena ezeztatzean:", error);
      showToastNotification("Errorea ekoizpena ezeztatzean", "error");
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
      case 'tank': return { type: 'image', url: './ia_assets/tank.png' };
      case 'boar rider': return { type: 'image', url: './ia_assets/boar_rider.png' };
      default: return { type: 'emoji', value: '👤' };
    }
  }

  function getBuildingIcon(type) {
    // Convert type to lowercase and remove spaces for comparison
    const normalizedType = type ? type.toLowerCase().replace(/\s+/g, '') : '';
    
    switch (normalizedType) {
      case 'farm': return { type: 'image', url: './ia_assets/farm.jpg' };
      case 'library': return { type: 'image', url: '/ia_assets/library.jpg' };
      // Use the new image paths for specific buildings and fix their type to 'image'
      case 'quarry': return { type: 'image', url: './ia_assets/quarry.jpg' };
      case 'sawmill': return { type: 'image', url: './ia_assets/sawmill.png' };
      case 'ironmine': return { type: 'image', url: './ia_assets/Iron_mine.png' };
      case 'goldmine': return { type: 'image', url: './ia_assets/mina_oro.jpg' };
      default: return { type: 'emoji', value: '🏛️' };
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
        throw new Error("Ez dago joko daturik eskuragarri.");
      }
      
      const selectedCityId = await gameAPI.getTemporaryData('selectedCityId');
      if (!selectedCityId) {
        // Improved error handling with more specific error
        showToastNotification("Ez da hiririk hautatu. Mapara itzultzen...", "error");
        setTimeout(() => navigate('/map'), 1500);
        throw new Error("Ez da hiririk hautatu.");
      }
      
      if (gameData.player && gameData.player.cities) {
        city = gameData.player.cities.find(c => c.id === selectedCityId);
      }
      
      if (!city) {
        // Improved error handling when city isn't found
        showToastNotification("Hautatutako hiria ez da aurkitu. Mapara itzultzen...", "error");
        setTimeout(() => navigate('/map'), 1500);
        throw new Error("Hautatutako hiria ez da aurkitu.");
      }
      
      // Only fetch these if we have a valid city
      await fetchTroopTypes();
      await fetchBuildingTypes();
      await fetchTechnologyTypes();

      // NEW: Debug player technologies
      debugTechnologies();
      
      isLoading = false;
    } catch (err) {
      console.error("Errorea hiria kargatzean:", err);
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
  <title>Hiria {city ? city.name : ''} - Civilization Game</title>
</svelte:head>

<div class="city-page game-view">
  <div class="city-background"></div>
  
  <button class="back-button" on:click={returnToMap}>← Mapara Itzuli</button>
  
  {#if isLoading}
    <div class="loading-container">
      <div class="loading-spinner"></div>
      <h2>Hiriaren datuak kargatzen...</h2>
    </div>
  {:else if error}
    <div class="error-container">
      <h2>Errorea hiria kargatzean</h2>
      <p>{error}</p>
      <button class="retry-button" on:click={returnToMap}>Mapara Itzuli</button>
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
            Laburpena
          </button>
          <button 
            class="tab-button" 
            class:active={activeTab === 'production'} 
            on:click={() => setActiveTab('production')}
          >
            Ekoizpena
          </button>
          <button 
            class="tab-button" 
            class:active={activeTab === 'buildings'} 
            on:click={() => setActiveTab('buildings')}
          >
            Eraikinak
          </button>
          <button 
            class="tab-button" 
            class:active={activeTab === 'library'} 
            on:click={() => setActiveTab('library')}
          >
            Liburutegia
          </button>
        </div>
        
        <div class="city-content">
          <div class="tab-content" class:active={activeTab === 'summary'}>
            <h3>Hiriaren Laburpena</h3>
            <p>Hiria kudeatzeko panela. Etorkizuneko inplementazioetan aukera gehiago erakutsiko dira.</p>
            
            <div class="info-section">
              <h4>Informazioa</h4>
              <p><strong>Kokapena:</strong> {Array.isArray(city.position) ? 
                `${city.position[0]}, ${city.position[1]}` : 
                `${city.position.x}, ${city.position.y}`}</p>
            </div>
            
            {#if city.buildings && city.buildings.length > 0}
              <div class="info-section">
                <h4>Eraikinak ({city.buildings.length})</h4>
                <ul class="buildings-list">
                  {#each city.buildings as building}
                    <li>{building.name || building}</li>
                  {/each}
                </ul>
              </div>
            {:else}
              <div class="info-section">
                <h4>Eraikinak</h4>
                <p>Ez dago eraikinrik hiri honetan.</p>
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
                    Hobekuntza Martxan
                  {:else if city.production.production_type === 'build' || !city.production.production_type && !isProducingTroop}
                    Eraikuntza Martxan
                  {:else}
                    Uneko Ekoizpena
                  {/if}
                </h4>
                <div class="production-type-badge {isProducingTroop ? 'troop' : 
                  city.production.production_type === 'upgrade' ? 'upgrade' : 'building'}">
                  {#if city.production.production_type === 'upgrade'}
                    Hobekuntza
                  {:else if city.production.production_type === 'build' || !city.production.production_type && !isProducingTroop}
                    Eraikuntza
                  {:else}
                    Trebakuntza
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
                      <span class="progress-text">{city.production.turns_remaining} txanda geratzen dira</span>
                    </div>
                    <button class="cancel-production-button" on:click={cancelProduction}>Ekoizpena Ezeztatu</button>
                  </div>
                </div>
              </div>
            {:else}
              <div class="info-section">
                <h4>Ekoizpena</h4>
                <p>Ez dago ekoizpenik martxan.</p>
                <button class="start-production-button" on:click={() => setActiveTab('production')}>Ekoizpena Hasi</button>
              </div>
            {/if}
          </div>
          
          <div class="tab-content" class:active={activeTab === 'production'}>
            <h3>Ekoizpena</h3>
            <p>Panel honetan zure hiriak zer eraikiko duen kudeatu ahal izango duzu.</p>
            
            <div class="info-section">
              <h4>Uneko Ekoizpena</h4>
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
                      <span class="progress-text">{city.production.turns_remaining} txanda geratzen dira</span>
                    </div>
                    <button class="cancel-production-button" on:click={cancelProduction}>Ekoizpena Ezeztatu</button>
                  </div>
                </div>
              {:else}
                <p>Ez dago ekoizpenik martxan. Aukeratu unitate bat ekoizpena hasteko.</p>
              {/if}
            </div>
            
            <div class="info-section">
              <h4>Eraiki</h4>
              <div class="production-options">
                <div class="production-option">
                  <h5>Unitateak</h5>
                  {#if loadingTroopTypes}
                    <p>Tropa motak kargatzen...</p>
                  {:else if troopTypes.length === 0}
                    <p>Ez daude tropa motak eskuragarri.</p>
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
                                <span class="tech-requirement">Beharrezkoa: {troopType.technology}</span>
                              {/if}
                            </div>
                            <span class="production-turns">
                              <span class="turns-icon">🕒</span>
                              <span class="turns-count">{troopType.turns_to_build || troopType.turns || '?'}</span>
                              <span class="turns-label">txanda</span>
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
                                    <span class="attribute-label">Erasoa:</span>
                                    <span class="attribute-value">{troopType.attack}</span>
                                  </div>
                                {/if}
                                
                                {#if troopType.defense !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">🛡️</span>
                                    <span class="attribute-label">Defentsa:</span>
                                    <span class="attribute-value">{troopType.defense}</span>
                                  </div>
                                {/if}
                                
                                {#if troopType.health !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">❤️</span>
                                    <span class="attribute-label">Osasuna:</span>
                                    <span class="attribute-value">{troopType.health}</span>
                                  </div>
                                {/if}
                                
                                {#if troopType.movement !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">👣</span>
                                    <span class="attribute-label">Mugimendua:</span>
                                    <span class="attribute-value">{troopType.movement}</span>
                                  </div>
                                {/if}
                                
                                {#if troopType.range !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">🎯</span>
                                    <span class="attribute-label">Irismena:</span>
                                    <span class="attribute-value">{troopType.range}</span>
                                  </div>
                                {/if}
                              </div>
                              
                              <div class="troop-action">
                                <button class="train-button" on:click={() => confirmStartProduction(troopType, 'troop')}>
                                  {troopType.name} Entrenatu
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
                  <h5>Eraikinak</h5>
                  {#if loadingBuildingTypes}
                    <p>Eraikin motak kargatzen...</p>
                  {:else if buildingTypes.length === 0}
                    <p>Ez daude eraikin motak eskuragarri.</p>
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
                                    <span class="building-level">Eraikita</span>
                                  {:else}
                                    <span class="building-level">Maila {existingBuilding.level || 1}</span>
                                  {/if}
                                {:else}
                                  <span class="building-cost">{@html getResourceCostString(buildingType.cost)}</span>
                                {/if}
                              </span>
                              {#if isLocked && buildingType.technology}
                                <span class="tech-requirement">Beharrezkoa: {buildingType.technology}</span>
                              {/if}
                            </div>
                            <span class="production-turns">
                              <span class="turns-icon">🕒</span>
                              <span class="turns-count">{buildingType.turns_to_build || buildingType.turns || '?'}</span>
                              <span class="turns-label">txanda</span>
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
                                    <span class="attribute-label">Maila:</span>
                                    <span class="attribute-value">{buildingType.level}</span>
                                  </div>
                                {/if}
                                
                                <!-- Level Upgrade Cost -->
                                {#if buildingType.level_upgrade !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">⬆️</span>
                                    <span class="attribute-label">Hobekuntza:</span>
                                    <span class="attribute-value">{buildingType.level_upgrade}</span>
                                  </div>
                                {/if}
                                
                                <!-- Output Resources -->
                                {#if buildingType.output}
                                  <div class="resource-output-attribute">
                                    <div class="resource-output-header">
                                      <span class="attribute-icon">⚒️</span>
                                      <span class="attribute-label">Ekoizpena</span>
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
                                    <span class="attribute-label">Ekoizpena:</span>
                                    <span class="attribute-value">+{buildingType.production_bonus}%</span>
                                  </div>
                                {/if}
                                
                                {#if buildingType.research_bonus !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">📚</span>
                                    <span class="attribute-label">Ikerketa:</span>
                                    <span class="attribute-value">+{buildingType.research_bonus}%</span>
                                  </div>
                                {/if}
                                
                                {#if buildingType.defense_bonus !== undefined}
                                  <div class="attribute">
                                    <span class="attribute-icon">🛡️</span>
                                    <span class="attribute-label">Defentsa:</span>
                                    <span class="attribute-value">+{buildingType.defense_bonus}%</span>
                                  </div>
                                {/if}
                              </div>
                              
                              <div class="building-action">
                                {#if existingBuilding}
                                  <button class="upgrade-button" on:click={() => confirmStartProduction(buildingType, 'building')}>
                                    {buildingType.name} Hobetu
                                  </button>
                                {:else}
                                  <button class="construct-button" on:click={() => confirmStartProduction(buildingType, 'building')}>
                                    {buildingType.name} Eraiki
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
            <h3>Eraikinak</h3>
            <p>Zure hiriko eraikinak kudeatu.</p>
            
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
                      <p class="building-description">Hiriko eraikina.</p>
                    {/if}
                    
                    <div class="building-stats">
                      <!-- Level Information -->
                      <div class="building-stat">
                        <span class="stat-icon">⭐</span>
                        <span class="stat-label">Maila:</span>
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
                            <span class="stat-label">Ekoizpena:</span>
                            <span class="stat-value">+{amount}/txanda</span>
                          </div>
                        {/each}
                      {/if}
                      
                      <!-- Level Upgrade Information -->
                      {#if building.level_upgrade !== undefined}
                        <div class="building-stat upgrade-info">
                          <span class="stat-icon">⬆️</span>
                          <span class="stat-label">Hurrengo mailara hobetzeko:</span>
                          <span class="stat-value">{building.level_upgrade}</span>
                        </div>
                      {/if}
                      
                      <!-- Other building stats -->
                      {#if building.production_bonus !== undefined}
                        <div class="building-stat">
                          <span class="stat-icon">⚒️</span>
                          <span class="stat-label">Ekoizpena:</span>
                          <span class="stat-value">+{building.production_bonus}%</span>
                        </div>
                      {/if}
                      
                      {#if building.research_bonus !== undefined}
                        <div class="building-stat">
                          <span class="stat-icon">📚</span>
                          <span class="stat-label">Ikerketa:</span>
                          <span class="stat-value">+{building.research_bonus}%</span>
                        </div>
                      {/if}
                      
                      {#if building.defense_bonus !== undefined}
                        <div class="building-stat">
                          <span class="stat-icon">🛡️</span>
                          <span class="stat-label">Defentsa:</span>
                          <span class="stat-value">+{building.defense_bonus}%</span>
                        </div>
                      {/if}
                      
                      {#if building.food_bonus !== undefined}
                        <div class="building-stat">
                          <span class="stat-icon">🌾</span>
                          <span class="stat-label">Janaria:</span>
                          <span class="stat-value">+{building.food_bonus}%</span>
                        </div>
                      {/if}
                      
                      {#if building.gold_bonus !== undefined}
                        <div class="building-stat">
                          <span class="stat-icon">💰</span>
                          <span class="stat-label">Urrea:</span>
                          <span class="stat-value">+{building.gold_bonus}%</span>
                        </div>
                      {/if}
                    </div>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="info-section">
                <p>Ez dago eraikinrik hiri honetan.</p>
                <button class="action-button" on:click={() => setActiveTab('production')}>Eraikinak Eraiki</button>
              </div>
            {/if}
          </div>

          <div class="tab-content" class:active={activeTab === 'library'}>
            <h3>Liburutegia eta Teknologiak</h3>
            {#if cityHasLibrary()}
              <p>Teknologia berriak ikertu zure zibilizazioa hobetzeko.</p>
              
              {#if city.research && city.research.current_technology}
                {@const researchTech = technologyTypes.find(t => t.id === city.research.current_technology)}
                <div class="info-section research-status-section">
                  <h4>Martxan Dagoen Ikerketa</h4>
                  <div class="production-type-badge research">Ikerketa</div>
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
                        <span class="progress-text">{city.research.turns_remaining} txanda geratzen dira</span>
                      </div>
                      <button class="cancel-production-button" on:click={cancelResearch}>Ikerketa Ezeztatu</button>
                    </div>
                  </div>
                </div>
              {/if}
              
              <div class="info-section">
                <h4>Teknologia Eskuragarriak</h4>
                {#if loadingTechnologyTypes}
                  <p>Teknologiak kargatzen...</p>
                {:else if technologyTypes.length === 0}
                  <p>Ez dago teknologiarik eskuragarri.</p>
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
                              <div class="technology-status">Ikertuta</div>
                            {:else if isResearching}
                              <div class="technology-status">Abian ({city.research.turns_remaining} txanda)</div>
                            {:else}
                              <div class="technology-requirements">
                                <div class="technology-req {city.population >= technology.min_civilians ? 'met' : ''}">
                                  <span class="req-icon">👥</span>
                                  <span class="req-label">Biztanleria:</span>
                                  <span class="req-value">{city.population}/{technology.min_civilians}</span>
                                </div>
                                
                                {#if technology.prerequisites && technology.prerequisites.length > 0}
                                  <div class="technology-prereqs">
                                    <span class="req-icon">📋</span>
                                    <span class="req-label">Betekizunak:</span>
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
                                  <span class="req-label">Denbora:</span>
                                  <span class="req-value">{technology.turns} txanda</span>
                                </div>
                              </div>
                              
                              <button 
                                class="research-button" 
                                disabled={!canResearch || hasMissingPrereqs || (city.research && city.research.current_technology)}
                                on:click={() => startResearch(technology)}
                              >
                                Ikertu
                              </button>
                            {/if}
                          </div>
                        </div>
                        
                        {#if technology.unlocks && technology.unlocks.length > 0}
                          <div class="technology-unlocks">
                            <h5>Desblokeatzen du:</h5>
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
                <p>Teknologiak ikertzeko, lehenik Liburutegi bat eraiki behar duzu hiri honetan.</p>
                <button class="action-button" on:click={() => setActiveTab('production')}>Liburutegia Eraiki</button>
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

  {#if showProductionConfirmationDialog}
    <div class="modal-overlay">
      <div class="confirmation-dialog">
        <h3>Ekoizpena Baieztatu</h3>
        <p>{@html productionConfirmationMessage}</p>
        <div class="confirmation-actions">
          <button class="cancel-button" on:click={closeProductionConfirmationDialog}>Utzi</button>
          <button class="confirm-button" on:click={productionConfirmationCallback}>Baieztatu</button>
        </div>
      </div>
    </div>
  {/if}

  {#if showConfirmationDialog}
    <div class="modal-overlay">
      <div class="confirmation-dialog">
        <h3>Ekintza Baieztatu</h3>
        <p>{confirmationMessage}</p>
        
        <div class="confirmation-actions">
          <button class="cancel-button" on:click={closeConfirmationDialog}>Utzi</button>
          <button class="confirm-button" on:click={confirmationCallback}>Baieztatu</button>
        </div>
      </div>
    </div>
  {/if}
</div>
