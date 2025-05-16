<script>
  import { navigate } from '../router.js';
  import { user } from '../stores/auth.js';
  import { gameState, startGame } from '../stores/gameState.js';
  import { onMount } from 'svelte';
  import { gameAPI } from '../services/gameAPI.js';
  import AudioPlayer from '../components/AudioPlayer.svelte';
  
  let error = null;
  let isLoading = true;
  let existingMaps = [];
  let selectedMap = null;
  let gameName = "Mi partida";
  let showCreateMapForm = false;
  let audioPlayer;

  function handleFirstInteraction() {
    if (audioPlayer) {
      audioPlayer.initializeAudio();
      // Eliminar event listeners después de inicialización
      document.removeEventListener('click', handleFirstInteraction);
      document.removeEventListener('keydown', handleFirstInteraction);
    }
  }

  // Datos para crear un nuevo mapa
  let newMapData = {
    width: 30,
    height: 15,
    startPoint: [15, 7],
    difficulty: "medium",
    name: ""
  };

  // Civilization selection
  let civilizations = [];
  let selectedPlayerCiv = null;
  let selectedAICiv = null;
  
  // Redirect to welcome page if not logged in
  onMount(async () => {
    try {
      if (!$user) {
        navigate('/');
        return;
      }
      document.addEventListener('click', handleFirstInteraction);
    document.addEventListener('keydown', handleFirstInteraction);
      // Cargar todos los mapas disponibles
      await loadExistingMaps();
      
      // Load available civilizations
      await loadCivilizations();
    } catch (err) {
      console.error("Error in NewGame component:", err);
      error = err.message;
    }
    return () => {
      document.removeEventListener('click', handleFirstInteraction);
      document.removeEventListener('keydown', handleFirstInteraction);
    };
  });

  // Función para cargar los mapas existentes
  async function loadExistingMaps() {
    try {
      isLoading = true;
      existingMaps = await gameAPI.getAllMaps();
      if (existingMaps.length > 0) {
        selectedMap = existingMaps[0];
      }
    } catch (err) {
      console.error("Error loading maps:", err);
      error = "No se pudieron cargar los mapas. " + err.message;
      // Crear mapas de ejemplo en caso de error para desarrollo
      existingMaps = [
        { map_id: "sample1", width: 30, height: 15, difficulty: "easy" },
        { map_id: "sample2", width: 40, height: 20, difficulty: "medium" }
      ];
      selectedMap = existingMaps[0];
    } finally {
      isLoading = false;
    }
  }

  // Load civilizations from the API
  async function loadCivilizations() {
    try {
      const response = await fetch('/api/civilizations');
      if (!response.ok) {
        throw new Error('Failed to load civilizations');
      }
      civilizations = await response.json();
      
      // Set default selections
      if (civilizations.length > 0) {
        selectedPlayerCiv = civilizations[0];
        // Select a different civ for AI
        selectedAICiv = civilizations.length > 1 ? civilizations[1] : civilizations[0];
      }
    } catch (err) {
      console.error("Error loading civilizations:", err);
      error = "No se pudieron cargar las civilizaciones: " + err.message;
      
      // Provide default civilizations in case of error
      civilizations = [
        {
          "civ_id": "rome",
          "name": "Rome",
          "description": "Masters of warfare and organization",
          "starting_resources": {
            "food": 110,
            "gold": 70,
            "wood": 20,
            "stone": 20,
            "iron": 15
          },
          "starting_units": {
            "settler": 1,
            "warrior": 2
          },
          "image": "ia_assets/Erroma.jpeg"
        },
        {
          "civ_id": "egypt",
          "name": "Egypt",
          "description": "Masters of agriculture and construction",
          "starting_resources": {
            "food": 120,
            "gold": 50,
            "wood": 15,
            "stone": 30,
            "iron": 10
          },
          "starting_units": {
            "settler": 2,
            "warrior": 1
          },
          "image": "ia_assets/Egipto.jpeg"
        },
        {
          "civ_id": "greece",
          "name": "Greece",
          "description": "Masters of philosophy and naval warfare",
          "starting_resources": {
            "food": 100,
            "gold": 60,
            "wood": 25,
            "stone": 25,
            "iron": 5
          },
          "starting_units": {
            "settler": 1,
            "warrior": 1,
            "archer": 1
          },
          "image": "ia_assets/Grezia.jpeg"
        },
        {
          "civ_id": "mongolia",
          "name": "Mongolia",
          "description": "Masters of cavalry and conquest",
          "starting_resources": {
            "food": 90,
            "gold": 40,
            "wood": 15,
            "stone": 15,
            "iron": 25
          },
          "starting_units": {
            "settler": 1,
            "warrior": 1,
            "cavalry": 1
          },
          "image": "ia_assets/Mongolia.jpeg"
        }
      ];
      selectedPlayerCiv = civilizations[0];
      selectedAICiv = civilizations[1];
    }
  }
  
  // Set the civilization for player
  function selectPlayerCiv(civ) {
    selectedPlayerCiv = civ;
    
    // If AI has the same civ, select a different one
    if (selectedAICiv && selectedAICiv.civ_id === civ.civ_id) {
      const otherCivs = civilizations.filter(c => c.civ_id !== civ.civ_id);
      if (otherCivs.length > 0) {
        selectedAICiv = otherCivs[0];
      }
    }
  }
  
  // Set the civilization for AI
  function selectAICiv(civ) {
    selectedAICiv = civ;
    
    // If player has the same civ, select a different one
    if (selectedPlayerCiv && selectedPlayerCiv.civ_id === civ.civ_id) {
      const otherCivs = civilizations.filter(c => c.civ_id !== civ.civ_id);
      if (otherCivs.length > 0) {
        selectedPlayerCiv = otherCivs[0];
      }
    }
  }

  // Función para crear un nuevo mapa
  async function createNewMap() {
    try {
      isLoading = true;
      
      // Validar datos del mapa
      if (!newMapData.width || !newMapData.height || !newMapData.startPoint || !newMapData.difficulty) {
        throw new Error("Los campos de dimensiones, punto de inicio y dificultad son obligatorios");
      }
      
      // Generar un nombre por defecto si no se proporciona
      if (!newMapData.name) {
        newMapData.name = `Mapa ${newMapData.width}x${newMapData.height} (${newMapData.difficulty})`;
      }
      
      // Convertir a números si es necesario
      newMapData.width = Number(newMapData.width);
      newMapData.height = Number(newMapData.height);
      
      if (typeof newMapData.startPoint === 'string') {
        newMapData.startPoint = newMapData.startPoint.split(',').map(coord => Number(coord.trim()));
      }
      
      // Validar punto de inicio
      if (newMapData.startPoint.length !== 2 || 
          isNaN(newMapData.startPoint[0]) || 
          isNaN(newMapData.startPoint[1])) {
        throw new Error("El punto de inicio debe ser de formato [x, y]");
      }
      
      // Validar que el punto de inicio está dentro de los límites del mapa (considerando índices desde 0)
      const [startX, startY] = newMapData.startPoint;
      if (startX < 0 || startX >= newMapData.width || startY < 0 || startY >= newMapData.height) {
        throw new Error(`El punto de inicio [${startX}, ${startY}] está fuera de los límites del mapa (0-${newMapData.width-1}, 0-${newMapData.height-1})`);
      }
      
      // Crear el mapa
      const result = await gameAPI.createMap(newMapData);
      
      console.log("Map created:", result);
      
      // Recargar la lista de mapas
      await loadExistingMaps();
      
      // Seleccionar el mapa recién creado si tenemos su ID
      if (result && result.map_id) {
        selectedMap = existingMaps.find(map => map.map_id === result.map_id) || existingMaps[0];
      }
      
      // Cerrar el formulario
      showCreateMapForm = false;
    } catch (err) {
      console.error("Error creating map:", err);
      error = "Error al crear el mapa: " + err.message;
    } finally {
      isLoading = false;
    }
  }
  
  // Función para seleccionar un mapa
  function selectMap(map) {
    console.log("Selected map:", map);
    selectedMap = map;
  }
  
  // Función para iniciar una nueva partida con el mapa seleccionado
  async function startNewGame() {
    try {
      if (!selectedMap) {
        error = "Debes seleccionar un mapa para comenzar";
        return;
      }
      
      if (!selectedPlayerCiv || !selectedAICiv) {
        error = "Debes seleccionar civilizaciones para el jugador y la IA";
        return;
      }
      
      isLoading = true;
      
      // Aseguramos que tenemos un valor de string para map_id
      const mapId = String(selectedMap.map_id || selectedMap._id);
      
      // Datos para crear la partida con civilizaciones
      const gameData = {
        map_id: mapId,
        name: gameName,
        difficulty: selectedMap.difficulty || "medium",
        player_civ_id: selectedPlayerCiv.civ_id,
        ai_civ_id: selectedAICiv.civ_id
      };
      
      console.log("Creating game with data:", gameData);
      
      // Llamar al endpoint para crear una partida con civilización
      const result = await gameAPI.createGameWithCivilization(gameData);
      
      console.log("Game created:", result);
      
      // Almacenar la información del juego en el estado
      startGame(gameName, {
        mapId: mapId,
        difficulty: selectedMap.difficulty,
        width: selectedMap.width,
        height: selectedMap.height,
        playerCiv: selectedPlayerCiv.name,
        aiCiv: selectedAICiv.name
      });
      
      // Navegar al mapa para iniciar la partida
      navigate('/map');
    } catch (err) {
      console.error("Error starting game:", err);
      error = "Error al iniciar la partida: " + err.message;
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="new-game-page">
  <AudioPlayer bind:this={audioPlayer} />
  <button class="back-button-inline" on:click={() => navigate('/home')}>
    Volver al Inicio
  </button>
  {#if error}
    <div class="error-message">
      <p>{error}</p>
      <button on:click={() => { error = null; }}>Cerrar</button>
    </div>
  {/if}
  
  <div class="page-header">
    <h1>Nueva Partida</h1>
  </div>
  
  {#if isLoading}
    <div class="loading">
      <div class="loading-spinner"></div>
      <p>Cargando...</p>
    </div>
  {:else}
    <div class="game-configuration">
      <div class="config-section">
        <h2>Configuración de la Partida</h2>
        
        <div class="form-group">
          <label for="game-name">Nombre de la Partida:</label>
          <input type="text" id="game-name" bind:value={gameName} placeholder="Introduce un nombre para tu partida" />
        </div>
      </div>
      
      <!-- Civilization Selection Section -->
      <div class="config-section">
        <h2>Selección de Civilización</h2>
        
        <div class="civs-container">
          <div class="civ-selection player-civ">
            <h3>Tu Civilización</h3>
            <div class="civs-grid">
              {#each civilizations as civ}
                <div 
                  class="civ-card" 
                  class:selected={selectedPlayerCiv && selectedPlayerCiv.civ_id === civ.civ_id}
                  on:click={() => selectPlayerCiv(civ)}
                  role="button"
                  tabindex="0"
                  on:keydown={(e) => e.key === 'Enter' && selectPlayerCiv(civ)}
                >
                  <div class="civ-icon">
                    {#if civ.civ_id === 'rome'}
                      <img src="/ia_assets/Erroma.jpeg" alt="Rome" />
                    {:else if civ.civ_id === 'egypt'}
                      <img src="/ia_assets/Egipto.jpeg" alt="Egypt" />
                    {:else if civ.civ_id === 'greece'}
                      <img src="/ia_assets/Grezia.jpeg" alt="Greece" />
                    {:else if civ.civ_id === 'mongolia'}
                      <img src="/ia_assets/Mongolia.jpeg" alt="Mongolia" />
                    {/if}
                  </div>
                  <div class="civ-info">
                    <h4>{civ.name}</h4>
                    <p class="civ-description">{civ.description}</p>
                    
                    {#if civ.starting_units}
                      <div class="civ-units">
                        <h5>Unidades iniciales:</h5>
                        <ul>
                          {#each Object.entries(civ.starting_units) as [unit, count]}
                            <li>
                              {#if unit === "settler"}
                                Colonizador: {count}
                              {:else if unit === "warrior"}
                                Guerrero: {count}
                              {:else if unit === "archer"}
                                Arquero: {count}
                              {:else if unit === "cavalry"}
                                Caballería: {count}
                              {:else}
                                {unit}: {count}
                              {/if}
                            </li>
                          {/each}
                        </ul>
                      </div>
                    {/if}
                    
                    {#if civ.starting_resources}
                      <div class="civ-resources">
                        <h5>Recursos iniciales:</h5>
                        <ul>
                          <li>Comida: {civ.starting_resources.food}</li>
                          <li>Oro: {civ.starting_resources.gold}</li>
                          <li>Madera: {civ.starting_resources.wood}</li>
                          <li>Piedra: {civ.starting_resources.stone}</li>
                          <li>Hierro: {civ.starting_resources.iron}</li>
                        </ul>
                      </div>
                    {/if}
                  </div>
                </div>
              {/each}
            </div>
          </div>
          
          <div class="civ-selection ai-civ">
            <h3>Civilización de la IA</h3>
            <div class="civs-grid">
              {#each civilizations as civ}
                <div 
                  class="civ-card" 
                  class:selected={selectedAICiv && selectedAICiv.civ_id === civ.civ_id}
                  on:click={() => selectAICiv(civ)}
                  role="button"
                  tabindex="0"
                  on:keydown={(e) => e.key === 'Enter' && selectAICiv(civ)}
                >
                  <div class="civ-icon">
                    {#if civ.civ_id === 'rome'}
                      <img src="/ia_assets/Erroma.jpeg" alt="Rome" />
                    {:else if civ.civ_id === 'egypt'}
                      <img src="/ia_assets/Egipto.jpeg" alt="Egypt" />
                    {:else if civ.civ_id === 'greece'}
                      <img src="/ia_assets/Grezia.jpeg" alt="Greece" />
                    {:else if civ.civ_id === 'mongolia'}
                      <img src="/ia_assets/Mongolia.jpeg" alt="Mongolia" />
                    {/if}
                  </div>
                  <div class="civ-info">
                    <h4>{civ.name}</h4>
                    <p class="civ-description">{civ.description}</p>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>
      
      <div class="config-section">
        <div class="section-header">
          <h2>Selecciona un Mapa</h2>
          <button class="create-map-button" on:click={() => showCreateMapForm = !showCreateMapForm}>
            {showCreateMapForm ? 'Cancelar' : 'Crear Nuevo Mapa'}
          </button>
        </div>
        
        {#if showCreateMapForm}
          <div class="create-map-form">
            <h3>Crear Nuevo Mapa</h3>
            
            <div class="form-group">
              <label for="map-name">Nombre del mapa:</label>
              <input type="text" id="map-name" bind:value={newMapData.name} 
                placeholder="Nombre personalizado (opcional)" />
            </div>
            
            <div class="form-group">
              <label for="map-width">Ancho:</label>
              <input type="number" id="map-width" bind:value={newMapData.width} min="10" max="100" />
            </div>
            
            <div class="form-group">
              <label for="map-height">Alto:</label>
              <input type="number" id="map-height" bind:value={newMapData.height} min="10" max="100" />
            </div>
            
            <div class="form-group">
              <label for="map-start">Punto de Inicio [x,y]:</label>
              <input type="text" id="map-start" 
                bind:value={newMapData.startPoint} 
                placeholder="15,7" />
            </div>
            
            <div class="form-group">
              <label for="map-difficulty">Dificultad:</label>
              <select id="map-difficulty" bind:value={newMapData.difficulty}>
                <option value="easy">Fácil</option>
                <option value="medium">Media</option>
                <option value="hard">Difícil</option>
              </select>
            </div>
            
            <button class="submit-map-button" on:click={createNewMap} disabled={isLoading}>
              {isLoading ? 'Creando...' : 'Crear Mapa'}
            </button>
          </div>
        {:else if existingMaps.length === 0}
          <div class="no-maps">
            <p>No hay mapas disponibles. Por favor, crea un mapa nuevo.</p>
          </div>
        {:else}
          <div class="maps-grid scrollable-container">
            {#each existingMaps as map}
              <div 
                class="map-card" 
                class:selected={selectedMap && selectedMap.map_id === map.map_id}
                on:click={() => selectMap(map)}
                role="button"
                tabindex="0"
                on:keydown={(e) => e.key === 'Enter' && selectMap(map)}
              >
                <div class="map-preview">
                  <div class="map-dimensions">{map.width}x{map.height}</div>
                </div>
                <div class="map-info">
                  <h3>{map.name || `Mapa ${map.map_id.substring(0, 8)}...`}</h3>
                  <p>Dificultad: {map.difficulty || 'normal'}</p>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
      
      <button class="start-button" on:click={startNewGame} disabled={isLoading || !selectedMap || !selectedPlayerCiv || !selectedAICiv}>
        {isLoading ? 'Iniciando...' : 'Comenzar Partida'}
      </button>
    </div>
  {/if}
</div>

<style>
  .new-game-page {
    max-width: 1000px;
    margin: 0 auto;
    padding: 2rem 1rem 1rem 1rem;
    /* Sin margin-top ni hueco arriba */
  }
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    margin-top: 0;
  }
  
  .back-button-inline {
    margin-bottom: 1.2rem;
    margin-top: 0;
    padding: 0.5rem 1.1rem;
    background-color: #6c757d;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    transition: background 0.2s;
    display: inline-block;
  }
  
  .back-button-inline:hover {
    background-color: #495057;
  }
  
  .back-button-fixed {
    display: none !important;
  }
  
  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
  }
  
  .loading-spinner {
    border: 4px solid rgba(0, 0, 0, 0.1);
    border-left-color: #4CAF50;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    animation: spin 1s linear infinite;
    margin-bottom: 1rem;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .game-configuration {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 2rem;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }
  
  .config-section {
    margin-bottom: 2rem;
  }
  
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }
  
  .create-map-button {
    padding: 0.5rem 1rem;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: bold;
  }
  
  input, select {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ced4da;
    border-radius: 4px;
    box-sizing: border-box;
  }
  
  .maps-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
  }
  
  .maps-grid.scrollable-container {
    max-height: 400px;
    overflow-y: auto;
  }
  
  .map-card {
    background-color: white;
    border-radius: 6px;
    padding: 1rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    cursor: pointer;
    transition: all 0.2s ease;
    border: 3px solid transparent;
    outline: none; /* Remove default focus outline */
  }
  
  .map-card:hover {
    transform: translateY(-3px);
  }
  
  .map-card.selected {
    border-color: #4CAF50;
    background-color: #f0fff0;
  }
  
  .map-card:focus {
    box-shadow: 0 0 0 3px #4CAF50; /* Add a visible focus indicator for accessibility */
  }
  
  .map-preview {
    background-color: #e9ecef;
    height: 100px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 0.5rem;
  }
  
  .map-dimensions {
    font-weight: bold;
    color: #495057;
  }
  
  .map-info h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
  }
  
  .map-info p {
    margin: 0;
    font-size: 0.9rem;
    color: #6c757d;
  }
  
  .create-map-form {
    background-color: white;
    border-radius: 6px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  .submit-map-button {
    padding: 0.6rem 1.2rem;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
  }
  
  .start-button {
    display: block;
    width: 200px;
    margin: 0 auto;
    padding: 0.8rem 0;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1.1rem;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .start-button:hover:not(:disabled) {
    background-color: #45a049;
    transform: translateY(-2px);
  }
  
  .start-button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
  
  .error-message {
    background-color: #ffebee;
    color: #c62828;
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 1rem;
    text-align: center;
    position: relative;
  }
  
  .error-message button {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    background: none;
    border: none;
    font-size: 1.2rem;
    cursor: pointer;
    color: #c62828;
  }
  
  .no-maps {
    text-align: center;
    padding: 2rem;
    background-color: #f8f9fa;
    border-radius: 4px;
    color: #6c757d;
  }
  
  .civs-container {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }
  
  .civ-selection h3 {
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e0e0e0;
  }
  
  .civs-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1rem;
  }
  
  .civ-card {
    background-color: white;
    border-radius: 6px;
    padding: 1rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    cursor: pointer;
    transition: all 0.2s ease;
    border: 3px solid transparent;
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  
  .civ-card:hover {
    transform: translateY(-3px);
  }
  
  .civ-card.selected {
    border-color: #4CAF50;
    background-color: #f0fff0;
  }
  
  .civ-icon {
    height: 80px;
    width: 80px;
    margin: 0 auto 1rem;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .civ-icon img {
    max-width: 100%;
    max-height: 100%;
  }
  
  .civ-info {
    text-align: center;
  }
  
  .civ-info h4 {
    margin: 0 0 0.5rem;
    font-size: 1.2rem;
    color: #333;
  }
  
  .civ-description {
    color: #666;
    margin-bottom: 1rem;
    font-size: 0.9rem;
  }
  
  .civ-units {
    text-align: left;
    margin-bottom: 1rem;
  }
  
  .civ-units h5, .civ-resources h5 {
    margin: 0 0 0.3rem;
    font-size: 0.9rem;
    color: #555;
  }
  
  .civ-units ul, .civ-resources ul {
    margin: 0;
    padding-left: 1.2rem;
    font-size: 0.85rem;
  }
  
  .civ-units li, .civ-resources li {
    margin-bottom: 0.2rem;
  }
  
  .civ-resources {
    text-align: left;
    font-size: 0.85rem;
  }
  
  .ai-civ .civ-units, .ai-civ .civ-resources {
    display: none;
  }
</style>
