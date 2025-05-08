<script>
  import { navigate } from '../router.js';
  import { user } from '../stores/auth.js';
  import { onMount } from 'svelte';
  import { gameAPI } from '../services/gameAPI.js';
  
  let error = null;
  let isLoading = true;
  let maps = [];
  let showConfirmDialog = false;
  let mapToDelete = null;
  let showCreateMapForm = false;
  
  // Datos para crear un nuevo mapa
  let newMapData = {
    width: 30,
    height: 15,
    startPoint: [15, 7],
    difficulty: "medium",
    name: ""
  };
  
  // Redirect to welcome page if not logged in
  onMount(async () => {
    try {
      if (!$user) {
        navigate('/');
        return;
      }
      
      // Load all available maps
      await loadMaps();
    } catch (err) {
      console.error("Error in Maps component:", err);
      error = err.message;
    }
  });

  // Function to load maps
  async function loadMaps() {
    try {
      isLoading = true;
      error = null;
      maps = await gameAPI.getAllMaps();
    } catch (err) {
      console.error("Error loading maps:", err);
      error = "No se pudieron cargar los mapas. " + err.message;
    } finally {
      isLoading = false;
    }
  }
  
  // Function to confirm map deletion
  function confirmDelete(map) {
    mapToDelete = map;
    showConfirmDialog = true;
  }
  
  // Function to cancel deletion
  function cancelDelete() {
    showConfirmDialog = false;
    mapToDelete = null;
  }
  
  // Function to delete map
  async function deleteMap() {
    try {
      if (!mapToDelete || !mapToDelete.map_id) {
        error = "No se seleccionó un mapa para borrar";
        showConfirmDialog = false;
        return;
      }
      
      const mapIdToDelete = mapToDelete.map_id;
      isLoading = true;
      
      console.log(`Intentando borrar mapa con ID: ${mapIdToDelete}`);
      
      try {
        await gameAPI.deleteMap(mapIdToDelete);
        console.log(`Mapa con ID ${mapIdToDelete} borrado exitosamente`);
      } catch (err) {
        console.error(`Error al borrar mapa ${mapIdToDelete}:`, err);
        
        // Si el mapa no existe (404), lo consideramos como borrado para fines de la interfaz
        if (err.message && (err.message.includes('404') || err.message.includes('no existe'))) {
          console.log("El mapa no existía en el servidor, actualizando interfaz de todas formas");
        } else {
          throw err; // Propagar otros errores
        }
      }
      
      // Remove the deleted map from the local array without reloading
      maps = maps.filter(map => map.map_id !== mapIdToDelete);
      
      // If after deletion there are no maps left, ensure we display the empty state
      if (maps.length === 0) {
        console.log("No maps left after deletion");
      }
      
      // Reset state
      showConfirmDialog = false;
      mapToDelete = null;
      
      // Only reload if we still have maps
      if (maps.length > 0) {
        await loadMaps();
      }
    } catch (err) {
      console.error("Error deleting map:", err);
      error = "Error al borrar el mapa: " + err.message;
    } finally {
      isLoading = false;
    }
  }
  
  // Función para crear un nuevo mapa
  async function createNewMap() {
    try {
      isLoading = true;
      
      // Validar datos del mapa
      if (!newMapData.width || !newMapData.height || !newMapData.startPoint || !newMapData.difficulty) {
        throw new Error("Todos los campos son obligatorios");
      }
      
      // Convertir a números si es necesario
      newMapData.width = Number(newMapData.width);
      newMapData.height = Number(newMapData.height);
      
      // Validación adicional para ancho y alto
      if (newMapData.width < 10 || newMapData.width > 100) {
        throw new Error("El ancho debe estar entre 10 y 100");
      }
      
      if (newMapData.height < 10 || newMapData.height > 100) {
        throw new Error("El alto debe estar entre 10 y 100");
      }
      
      // Procesar el punto de inicio
      if (typeof newMapData.startPoint === 'string') {
        try {
          // Intentar diferentes formatos: "x,y", "[x,y]", etc.
          const cleanString = newMapData.startPoint.replace(/[\[\]]/g, '');
          newMapData.startPoint = cleanString.split(',').map(coord => {
            const num = Number(coord.trim());
            if (isNaN(num)) {
              throw new Error("Las coordenadas deben ser números");
            }
            return num;
          });
        } catch (err) {
          throw new Error("Formato de punto de inicio inválido. Usa formato 'x,y'");
        }
      }
      
      // Validar punto de inicio
      if (newMapData.startPoint.length !== 2) {
        throw new Error("El punto de inicio debe tener exactamente dos coordenadas [x,y]");
      }
      
      const [x, y] = newMapData.startPoint;
      
      // Verificar que las coordenadas son números
      if (isNaN(x) || isNaN(y)) {
        throw new Error("Las coordenadas del punto de inicio deben ser números");
      }
      
      // Verificar que el punto de inicio está dentro de los límites del mapa
      if (x < 0 || x >= newMapData.width || y < 0 || y >= newMapData.height) {
        throw new Error(`El punto de inicio [${x},${y}] está fuera de los límites del mapa (${newMapData.width}x${newMapData.height})`);
      }
      
      // Crear el mapa
      console.log("Enviando datos del mapa:", newMapData);
      const result = await gameAPI.createMap(newMapData);
      
      console.log("Map created:", result);
      
      // Recargar la lista de mapas
      await loadMaps();
      
      // Cerrar el formulario
      showCreateMapForm = false;
      
      // Reiniciar los valores del formulario para una próxima creación
      newMapData = {
        width: 30,
        height: 15,
        startPoint: [15, 7],
        difficulty: "medium",
        name: ""
      };
    } catch (err) {
      console.error("Error creating map:", err);
      error = "Error al crear el mapa: " + err.message;
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="maps-page">
  {#if error}
    <div class="error-message">
      <p>{error}</p>
      <button on:click={() => { error = null; }}>Cerrar</button>
    </div>
  {/if}
  
  <div class="page-header">
    <h1>Gestión de Mapas</h1>
    <button class="back-button" on:click={() => navigate('/home')}>
      Volver al Inicio
    </button>
  </div>
  
  {#if isLoading}
    <div class="loading">
      <div class="loading-spinner"></div>
      <p>Cargando...</p>
    </div>
  {:else}
    <div class="maps-container">
      <div class="section-header">
        <h2>Mapas Disponibles</h2>
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
            <small class="form-hint">Las coordenadas deben estar entre 0 y el ancho/alto del mapa. Ejemplo: 15,7</small>
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
      {/if}
      
      {#if maps.length === 0}
        <div class="no-maps">
          <p>No hay mapas disponibles.</p>
          {#if !showCreateMapForm}
            <button class="create-map-button" on:click={() => showCreateMapForm = true}>
              Crear Nuevo Mapa
            </button>
          {/if}
        </div>
      {:else}
        <div class="maps-grid">
          {#each maps as map}
            <div class="map-card">
              <div class="map-preview">
                <div class="map-dimensions">{map.width}x{map.height}</div>
              </div>
              <div class="map-info">
                <h3>{map.name || `Mapa ${map.map_id.substring(0, 8)}...`}</h3>
                <p>Dimensiones: {map.width}x{map.height}</p>
                <p>Dificultad: {map.difficulty || 'normal'}</p>
                <button class="delete-button" on:click={() => confirmDelete(map)}>
                  Borrar Mapa
                </button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
  
  {#if showConfirmDialog}
    <div class="confirm-dialog-overlay">
      <div class="confirm-dialog">
        <h3>Confirmar Borrado</h3>
        <p>¿Estás seguro de que quieres borrar este mapa? Esta acción no se puede deshacer.</p>
        
        <div class="map-info">
          <p><strong>ID:</strong> {mapToDelete.map_id}</p>
          <p><strong>Dimensiones:</strong> {mapToDelete.width}x{mapToDelete.height}</p>
          <p><strong>Dificultad:</strong> {mapToDelete.difficulty || 'normal'}</p>
        </div>
        
        <div class="dialog-buttons">
          <button class="cancel-button" on:click={cancelDelete}>Cancelar</button>
          <button class="confirm-button" on:click={deleteMap}>Borrar</button>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .maps-page {
    max-width: 1000px;
    margin: 0 auto;
    padding: 2rem 1rem;
  }
  
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
  }
  
  .back-button {
    padding: 0.5rem 1rem;
    background-color: #6c757d;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
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
  
  .maps-container {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 2rem;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }
  
  .maps-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1.5rem;
    margin-top: 1.5rem;
  }
  
  .map-card {
    background-color: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  
  .map-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
  }
  
  .map-preview {
    background-color: #e9ecef;
    height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .map-dimensions {
    font-weight: bold;
    font-size: 1.2rem;
    color: #495057;
  }
  
  .map-info {
    padding: 1rem;
  }
  
  .map-info h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.1rem;
  }
  
  .map-info p {
    margin: 0 0 1rem 0;
    font-size: 0.9rem;
    color: #6c757d;
  }
  
  .delete-button {
    width: 100%;
    padding: 0.5rem;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .delete-button:hover {
    background-color: #c82333;
  }
  
  .error-message {
    background-color: #ffebee;
    color: #c62828;
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 1rem;
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
    border-radius: 8px;
  }
  
  .create-map-button {
    padding: 0.5rem 1rem;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  .create-map-button:hover {
    background-color: #45a049;
  }
  
  .create-map-form {
    background-color: white;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
  
  .submit-map-button {
    padding: 0.6rem 1.2rem;
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.2s;
  }
  
  .submit-map-button:hover:not(:disabled) {
    background-color: #45a049;
  }
  
  .submit-map-button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
  
  .form-hint {
    display: block;
    font-size: 0.8rem;
    color: #6c757d;
    margin-top: 0.25rem;
  }
  
  .confirm-dialog-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }
  
  .confirm-dialog {
    background-color: white;
    border-radius: 8px;
    width: 90%;
    max-width: 500px;
    padding: 2rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  }
  
  .confirm-dialog h3 {
    margin-top: 0;
    color: #dc3545;
  }
  
  .dialog-buttons {
    display: flex;
    justify-content: flex-end;
    gap: 1rem;
    margin-top: 1.5rem;
  }
  
  .cancel-button {
    padding: 0.5rem 1rem;
    background-color: #6c757d;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .confirm-button {
    padding: 0.5rem 1rem;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
</style>
