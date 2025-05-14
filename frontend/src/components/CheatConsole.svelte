<script>
  import { createEventDispatcher } from 'svelte';

  export let visible = false;
  export let result = null;
  export let resultType = 'info'; // 'success', 'error', 'info'

  const dispatch = createEventDispatcher();
  let command = '';

  function closeConsole() {
    dispatch('close');
  }

  function executeCheat() {
    if (!command.trim()) return;
    
    dispatch('execute', { command: command.trim() });
    command = '';
  }

  function handleKeyDown(event) {
    if (event.key === 'Escape') {
      closeConsole();
    } else if (event.key === 'Enter') {
      executeCheat();
    }
  }
</script>

<div class="cheat-console-overlay" class:visible on:keydown={handleKeyDown}>
  <div class="cheat-console">
    <div class="cheat-console-header">
      <h3>Komando Kontsola</h3>
      <button class="close-button" on:click={closeConsole}>×</button>
    </div>
    
    <div class="cheat-console-content">
      <form on:submit|preventDefault={executeCheat}>
        <div class="cheat-input-container">
          <input 
            id="cheat-input" 
            type="text" 
            bind:value={command} 
            placeholder="Idatzi komandoa hemen..."
            autocomplete="off"
          />
          <button type="submit">Exekutatu</button>
        </div>
      </form>
      
      {#if result}
        <div class="cheat-result {resultType}">
          {result}
        </div>
      {/if}
      
      <div class="cheat-help">
        <p>Komando erabilgarriak:</p>
        <ul>
          <li><code>fogOfWar_Off</code> - Gerra-lainoa desaktibatu</li>
          <li><code>unlimitedMovements</code> - Mugimendu mugagabeak zure tropentzat</li>
        </ul>
      </div>
    </div>
  </div>
</div>

<style>
  .cheat-console-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.7);
    z-index: 1000;
    display: none;
    align-items: center;
    justify-content: center;
  }

  .cheat-console-overlay.visible {
    display: flex;
  }

  .cheat-console {
    background-color: #1a1a1a;
    color: #33ff33;
    border: 2px solid #33ff33;
    border-radius: 5px;
    width: 80%;
    max-width: 600px;
    box-shadow: 0 0 20px rgba(51, 255, 51, 0.5);
  }

  .cheat-console-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 15px;
    border-bottom: 1px solid #33ff33;
  }

  .cheat-console-header h3 {
    margin: 0;
    color: #33ff33;
    font-family: 'Courier New', monospace;
  }

  .close-button {
    background: none;
    border: none;
    color: #33ff33;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
  }

  .cheat-console-content {
    padding: 15px;
  }

  .cheat-input-container {
    display: flex;
    margin-bottom: 15px;
  }

  .cheat-input-container input {
    flex-grow: 1;
    background-color: #000;
    border: 1px solid #33ff33;
    color: #33ff33;
    padding: 8px 10px;
    font-family: 'Courier New', monospace;
  }

  .cheat-input-container button {
    background-color: #33ff33;
    color: #000;
    border: none;
    padding: 8px 15px;
    margin-left: 5px;
    cursor: pointer;
    font-weight: bold;
  }

  .cheat-result {
    padding: 10px;
    margin: 10px 0;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
  }

  .cheat-result.success {
    background-color: rgba(30, 150, 30, 0.3);
    border: 1px solid #33ff33;
  }

  .cheat-result.error {
    background-color: rgba(150, 30, 30, 0.3);
    border: 1px solid #ff3333;
    color: #ff5555;
  }

  .cheat-result.info {
    background-color: rgba(30, 30, 150, 0.3);
    border: 1px solid #3333ff;
    color: #5555ff;
  }

  .cheat-help {
    border-top: 1px dashed #33ff33;
    padding-top: 10px;
    margin-top: 10px;
    font-family: 'Courier New', monospace;
    font-size: 0.9em;
  }

  .cheat-help ul {
    list-style-type: none;
    padding-left: 10px;
  }

  .cheat-help code {
    background-color: rgba(0, 0, 0, 0.5);
    padding: 2px 4px;
    border-radius: 3px;
  }
</style>
