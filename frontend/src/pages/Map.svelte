<script>
  import { onMount } from 'svelte';
  
  // Map configuration
  let mapSize = { width: 20, height: 15 };
  let tileSize = 50; // pixels
  let selectedTile = null;
  
  // Map elements (to be filled later with actual data)
  let cities = [];
  let resources = [];
  let units = [];
  
  // Map navigation
  let offsetX = 0;
  let offsetY = 0;
  let isDragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let zoomLevel = 1;
  
  onMount(() => {
    // In a real implementation, we would load map data from the API
    // For now, we'll just add some placeholder data
    cities = [
      { id: 1, name: 'Capital City', x: 5, y: 5, size: 3, owner: 'player' },
      { id: 2, name: 'Eastern Settlement', x: 15, y: 7, size: 1, owner: 'player' },
      { id: 3, name: 'Enemy City', x: 11, y: 3, size: 2, owner: 'ai' }
    ];
    
    resources = [
      { id: 1, type: 'iron', x: 7, y: 6 },
      { id: 2, type: 'food', x: 4, y: 4 },
      { id: 3, type: 'gold', x: 14, y: 8 }
    ];
    
    units = [
      { id: 1, type: 'warrior', x: 6, y: 5, owner: 'player' },
      { id: 2, type: 'settler', x: 8, y: 9, owner: 'player' }
    ];
  });
  
  function handleTileClick(x, y) {
    selectedTile = { x, y };
    
    // Check if there's a city on this tile
    const city = cities.find(c => c.x === x && c.y === y);
    if (city) {
      selectedTile.city = city;
    }
    
    // Check if there's a resource on this tile
    const resource = resources.find(r => r.x === x && r.y === y);
    if (resource) {
      selectedTile.resource = resource;
    }
    
    // Check if there's a unit on this tile
    const unit = units.find(u => u.x === x && u.y === y);
    if (unit) {
      selectedTile.unit = unit;
    }
  }
  
  function startDrag(event) {
    isDragging = true;
    dragStartX = event.clientX;
    dragStartY = event.clientY;
  }
  
  function drag(event) {
    if (!isDragging) return;
    
    const dx = event.clientX - dragStartX;
    const dy = event.clientY - dragStartY;
    
    offsetX += dx;
    offsetY += dy;
    
    dragStartX = event.clientX;
    dragStartY = event.clientY;
  }
  
  function endDrag() {
    isDragging = false;
  }
  
  function zoomIn() {
    if (zoomLevel < 2) zoomLevel += 0.2;
  }
  
  function zoomOut() {
    if (zoomLevel > 0.5) zoomLevel -= 0.2;
  }
  
  function getTileColor(x, y) {
    // Simple checkerboard pattern for now
    return (x + y) % 2 === 0 ? '#8db580' : '#a7cc93';
  }
</script>

<div class="map-page">
  <div class="map-controls">
    <button on:click={zoomIn}>Zoom In (+)</button>
    <button on:click={zoomOut}>Zoom Out (-)</button>
    <button on:click={() => { offsetX = 0; offsetY = 0; }}>Center Map</button>
  </div>
  
  <div 
    class="map-container"
    on:mousedown={startDrag}
    on:mousemove={drag}
    on:mouseup={endDrag}
    on:mouseleave={endDrag}
  >
    <div 
      class="map-grid"
      style="transform: translate({offsetX}px, {offsetY}px) scale({zoomLevel}); width: {mapSize.width * tileSize}px; height: {mapSize.height * tileSize}px;"
    >
      {#each Array(mapSize.height) as _, y}
        {#each Array(mapSize.width) as _, x}
          <div 
            class="map-tile"
            style="
              left: {x * tileSize}px;
              top: {y * tileSize}px;
              width: {tileSize}px;
              height: {tileSize}px;
              background-color: {getTileColor(x, y)};
            "
            on:click={() => handleTileClick(x, y)}
            class:selected={selectedTile && selectedTile.x === x && selectedTile.y === y}
          >
            <div class="tile-coordinates">{x},{y}</div>
            
            {#each cities.filter(city => city.x === x && city.y === y) as city}
              <div class="city-marker" class:enemy={city.owner === 'ai'}>
                <span class="city-icon">🏙️</span>
              </div>
            {/each}
            
            {#each resources.filter(resource => resource.x === x && resource.y === y) as resource}
              <div class="resource-marker">
                {resource.type === 'iron' ? '⚒️' : resource.type === 'food' ? '🌾' : '💰'}
              </div>
            {/each}
            
            {#each units.filter(unit => unit.x === x && unit.y === y) as unit}
              <div class="unit-marker" class:enemy={unit.owner === 'ai'}>
                {unit.type === 'warrior' ? '⚔️' : '👨‍🌾'}
              </div>
            {/each}
          </div>
        {/each}
      {/each}
    </div>
  </div>
  
  <div class="info-panel">
    <h3>Information Panel</h3>
    {#if selectedTile}
      <div class="selected-info">
        <h4>Selected Tile: ({selectedTile.x}, {selectedTile.y})</h4>
        
        {#if selectedTile.city}
          <div class="city-info">
            <h5>City: {selectedTile.city.name}</h5>
            <p>Size: {selectedTile.city.size}</p>
            <p>Owner: {selectedTile.city.owner === 'player' ? 'You' : 'AI'}</p>
          </div>
        {/if}
        
        {#if selectedTile.resource}
          <div class="resource-info">
            <h5>Resource: {selectedTile.resource.type}</h5>
          </div>
        {/if}
        
        {#if selectedTile.unit}
          <div class="unit-info">
            <h5>Unit: {selectedTile.unit.type}</h5>
            <p>Owner: {selectedTile.unit.owner === 'player' ? 'You' : 'AI'}</p>
          </div>
        {/if}
        
        {#if !selectedTile.city && !selectedTile.resource && !selectedTile.unit}
          <p>Empty tile</p>
        {/if}
      </div>
    {:else}
      <p>No tile selected. Click on a tile to see information.</p>
    {/if}
  </div>
</div>

<style>
  .map-page {
    display: grid;
    grid-template-columns: 3fr 1fr;
    grid-template-rows: auto 1fr;
    gap: 1rem;
    height: calc(100vh - 15rem);
  }
  
  .map-controls {
    grid-column: 1 / 3;
    display: flex;
    gap: 0.5rem;
    padding: 0.5rem;
    background-color: #f0f0f0;
    border-radius: 4px;
  }
  
  .map-controls button {
    padding: 0.5rem 1rem;
    background-color: #4c66af;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  .map-container {
    grid-column: 1;
    border: 1px solid #ccc;
    border-radius: 4px;
    overflow: hidden;
    position: relative;
    cursor: grab;
    background-color: #b3e6ff;
  }
  
  .map-grid {
    position: relative;
    transform-origin: 0 0;
  }
  
  .map-tile {
    position: absolute;
    border: 1px solid rgba(0, 0, 0, 0.1);
    box-sizing: border-box;
    font-size: 0.7rem;
    color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    transition: all 0.1s;
  }
  
  .map-tile:hover {
    border: 1px solid rgba(255, 255, 255, 0.8);
    z-index: 10;
  }
  
  .map-tile.selected {
    border: 2px solid #ffcc00;
    z-index: 20;
  }
  
  .tile-coordinates {
    position: absolute;
    bottom: 2px;
    right: 2px;
    font-size: 0.6rem;
    opacity: 0.7;
  }
  
  .city-marker {
    position: absolute;
    z-index: 5;
    font-size: 1.5rem;
  }
  
  .city-marker.enemy {
    color: #ff4d4d;
  }
  
  .resource-marker {
    position: absolute;
    z-index: 4;
    font-size: 1.2rem;
  }
  
  .unit-marker {
    position: absolute;
    z-index: 6;
    font-size: 1.2rem;
  }
  
  .unit-marker.enemy {
    color: #ff4d4d;
  }
  
  .info-panel {
    grid-column: 2;
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 1rem;
    background-color: #f9f9f9;
    overflow-y: auto;
  }
  
  .info-panel h3 {
    margin-top: 0;
    margin-bottom: 1rem;
    border-bottom: 1px solid #eee;
    padding-bottom: 0.5rem;
  }
  
  .selected-info h4 {
    margin-top: 0;
    margin-bottom: 1rem;
  }
  
  .city-info, .resource-info, .unit-info {
    margin-bottom: 1rem;
    padding: 0.5rem;
    background-color: #fff;
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  }
  
  .city-info h5, .resource-info h5, .unit-info h5 {
    margin-top: 0;
    margin-bottom: 0.5rem;
  }
</style>
