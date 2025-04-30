<script>
  import { navigate } from '../router.js';
  import { user } from '../stores/auth.js';
  import { gameState, setCurrentScenario, startGame } from '../stores/gameState.js';
  import { onMount } from 'svelte';
  
  let error = null;
  
  // Redirect to welcome page if not logged in
  onMount(() => {
    try {
      if (!$user) {
        navigate('/');
      }
    } catch (err) {
      console.error("Error in NewGame component:", err);
      error = err.message;
    }
  });
  
  // Define available scenarios with different difficulties
  const availableScenarios = [
    {
      _id: "europe_map_01",
      name: "Europe Map - Easy",
      description: "An easier scenario with more resources for the player",
      difficulty: "easy",
      thumbnail: "europe_easy.jpg",
      map_size: { width: 30, height: 30 }, // Reduced map size for better performance
      initial_state: {
        player: {
          resources: {
            food: 50,
            production: 40,
            science: 20,
            gold: 300
          },
          cities: [
            { id: "city1", name: 'London', position: { x: 12, y: 8 }, population: 4, buildings: [], production: { current_item: "warrior", turns_remaining: 2 } },
            { id: "city2", name: 'Paris', position: { x: 15, y: 12 }, population: 3, buildings: [], production: { current_item: "settler", turns_remaining: 3 } }
          ],
          units: [
            { id: "unit1", type: 'warrior', position: { x: 13, y: 9 }, movement_points: 2, movement_points_left: 2, strength: 6, health: 100 },
            { id: "unit2", type: 'archer', position: { x: 16, y: 13 }, movement_points: 2, movement_points_left: 2, strength: 5, health: 100 }
          ],
          technologies: [
            { id: "agriculture", completed: true },
            { id: "pottery", completed: true },
            { id: "animal_husbandry", in_progress: true, turns_remaining: 2 }
          ]
        },
        ai: {
          resources: {
            food: 30,
            production: 15,
            science: 5,
            gold: 150
          },
          cities: [
            { id: "ai_city1", name: 'Berlin', position: { x: 20, y: 8 }, visible: false },
            { id: "ai_city2", name: 'Rome', position: { x: 20, y: 18 }, visible: false }
          ],
          units: [
            { id: "ai_unit1", type: 'warrior', position: { x: 19, y: 9 }, visible: false }
          ],
          technologies: []
        },
        map: {
          explored: [],
          visible_objects: [
            { type: "resource", resource_type: "iron", position: { x: 17, y: 15 }, improved: false },
            { type: "resource", resource_type: "food", position: { x: 14, y: 10 }, improved: false }
          ]
        }
      }
    },
    {
      _id: "europe_map_02",
      name: "Europe Map - Hard",
      description: "A challenging scenario with stronger AI opponents",
      difficulty: "hard",
      thumbnail: "europe_hard.jpg",
      map_size: { width: 30, height: 30 }, // Reduced map size for better performance
      initial_state: {
        player: {
          resources: {
            food: 20,
            production: 15,
            science: 5,
            gold: 100
          },
          cities: [
            { id: "city1", name: 'London', position: { x: 10, y: 8 }, population: 2, buildings: [], production: { current_item: "warrior", turns_remaining: 3 } },
          ],
          units: [
            { id: "unit1", type: 'warrior', position: { x: 11, y: 9 }, movement_points: 2, movement_points_left: 2, strength: 5, health: 100 },
          ],
          technologies: [
            { id: "agriculture", completed: true }
          ]
        },
        ai: {
          resources: {
            food: 50,
            production: 35,
            science: 15,
            gold: 250
          },
          cities: [
            { id: "ai_city1", name: 'Berlin', position: { x: 20, y: 8 }, visible: false },
            { id: "ai_city2", name: 'Rome', position: { x: 20, y: 18 }, visible: false },
            { id: "ai_city3", name: 'Moscow', position: { x: 22, y: 10 }, visible: false }
          ],
          units: [
            { id: "ai_unit1", type: 'warrior', position: { x: 19, y: 9 }, visible: false },
            { id: "ai_unit2", type: 'archer', position: { x: 21, y: 11 }, visible: false }
          ],
          technologies: []
        },
        map: {
          explored: [],
          visible_objects: [
            { type: "resource", resource_type: "iron", position: { x: 16, y: 15 }, improved: false },
            { type: "resource", resource_type: "food", position: { x: 13, y: 10 }, improved: false }
          ]
        }
      }
    }
  ];
  
  let selectedScenario = availableScenarios[0];
  let gameName = "My Game";
  
  function startNewGame() {
    try {
      // Store the selected scenario and game name in the game state
      startGame(gameName, selectedScenario);
      
      // Navigate directly to the map
      navigate('/map');
    } catch (err) {
      console.error("Error starting game:", err);
      error = err.message;
    }
  }
</script>

<div class="new-game-page">
  {#if error}
    <div class="error-message">
      <p>{error}</p>
      <button on:click={() => window.location.reload()}>Reload Page</button>
    </div>
  {:else}
    <div class="page-header">
      <h1>New Game</h1>
      <button class="back-button" on:click={() => navigate('/home')}>
        Back to Dashboard
      </button>
    </div>
    
    <div class="game-configuration">
      <div class="config-section">
        <h2>Game Settings</h2>
        
        <div class="form-group">
          <label for="game-name">Game Name:</label>
          <input type="text" id="game-name" bind:value={gameName} />
        </div>
      </div>
      
      <div class="config-section">
        <h2>Select Scenario</h2>
        
        <div class="scenario-options">
          {#each availableScenarios as scenario}
            <div 
              class="scenario-card" 
              class:selected={selectedScenario._id === scenario._id}
              on:click={() => selectedScenario = scenario}
            >
              <h3>{scenario.name}</h3>
              <p>{scenario.description}</p>
              <div class="difficulty-badge {scenario.difficulty}">
                {scenario.difficulty.toUpperCase()}
              </div>
            </div>
          {/each}
        </div>
      </div>
      
      <button class="start-button" on:click={startNewGame}>
        Start Game
      </button>
    </div>
  {/if}
</div>

<style>
  .new-game-page {
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
  
  .game-configuration {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 2rem;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }
  
  .config-section {
    margin-bottom: 2rem;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: bold;
  }
  
  input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ced4da;
    border-radius: 4px;
  }
  
  .scenario-options {
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
  }
  
  .scenario-card {
    background-color: white;
    border-radius: 6px;
    padding: 1.5rem;
    width: 280px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    cursor: pointer;
    transition: all 0.2s ease;
    position: relative;
    border: 3px solid transparent;
  }
  
  .scenario-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.1);
  }
  
  .scenario-card.selected {
    border-color: #4CAF50;
    background-color: #f0fff0;
  }
  
  .difficulty-badge {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    padding: 0.3rem 0.6rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: bold;
  }
  
  .difficulty-badge.easy {
    background-color: #4CAF50;
    color: white;
  }
  
  .difficulty-badge.hard {
    background-color: #f44336;
    color: white;
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
  
  .start-button:hover {
    background-color: #45a049;
    transform: translateY(-2px);
  }

  .error-message {
    background-color: #ffebee;
    color: #c62828;
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 1rem;
    text-align: center;
  }
</style>
