<script>
  import { onMount } from 'svelte';
  import { navigate } from '../router.js';
  import { gameAPI } from '../services/gameAPI.js';
  import '../styles/pages/battle.css';

  // Battle data will be passed through gameAPI temporary storage
  let attacker = null;
  let defender = null;
  let battleLog = [];
  let battleEnded = false;
  let winner = null;
  let gameData = null;

  // Animation states
  let attackerAnimating = false;
  let defenderAnimating = false;
  let showDamageNumber = false;
  let damageAmount = 0;
  let damagePosition = 'defender'; // 'attacker' or 'defender'

  onMount(async () => {
    try {
      // Get battle data from temporary storage
      const battleData = gameAPI.getTemporaryData('battleData');
      
      if (!battleData) {
        throw new Error('No battle data found');
      }

      attacker = battleData.attacker;
      defender = battleData.defender;
      gameData = battleData.gameData;

      console.log('Battle initialized with:', { attacker, defender });
      
      // Add initial battle log entry
      battleLog = [
        `¡Batalla entre ${attacker.name || attacker.type_id} y ${defender.name || defender.type_id}!`
      ];

      // Start battle after a shorter delay (reduced from 1500ms to 500ms)
      setTimeout(() => startBattle(), 500);
    } catch (error) {
      console.error('Error initializing battle:', error);
      battleLog = [...battleLog, `Error: ${error.message}`];
    }
  });

  // Battle mechanics
  async function startBattle() {
    if (!attacker || !defender) {
      return;
    }

    let currentTurn = 0;
    let isAttackerTurn = true;

    while (attacker.health > 0 && defender.health > 0) {
      currentTurn++;
      battleLog = [...battleLog, `--- Turno ${currentTurn} ---`];

      // Determine who attacks this turn
      const currentAttacker = isAttackerTurn ? attacker : defender;
      const currentDefender = isAttackerTurn ? defender : attacker;
      
      // Calculate damage with randomness factor
      const randomFactor = Math.random() * 2; // Random number between 0 and 2
      const baseDamage = currentAttacker.attack * randomFactor;
      
      // Defense reduces damage by a percentage (each defense point reduces damage by 5%)
      const defenseReduction = currentDefender.defense * 0.05;
      const defenseMultiplier = Math.max(0.1, 1 - defenseReduction); // At least 10% damage passes through
      
      let damage = Math.round(baseDamage * defenseMultiplier);
      
      // Animate the attacker
      if (isAttackerTurn) {
        attackerAnimating = true;
      } else {
        defenderAnimating = true;
      }

      // Show damage number
      damageAmount = damage;
      damagePosition = isAttackerTurn ? 'defender' : 'attacker';
      showDamageNumber = true;

      // Log the attack
      battleLog = [...battleLog, 
        `${currentAttacker.name || currentAttacker.type_id} ataca y causa ${damage} puntos de daño a ${currentDefender.name || currentDefender.type_id}`
      ];

      // Apply damage
      if (isAttackerTurn) {
        defender.health -= damage;
      } else {
        attacker.health -= damage;
      }

      // Wait for animation (reduced from 1000ms to 400ms)
      await new Promise(resolve => setTimeout(resolve, 400));
      
      // Reset animations
      attackerAnimating = false;
      defenderAnimating = false;
      showDamageNumber = false;

      // Switch turns
      isAttackerTurn = !isAttackerTurn;
      
      // Add a shorter delay between turns (reduced from 800ms to 300ms)
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // Check if battle has ended
      if (attacker.health <= 0 || defender.health <= 0) {
        break;
      }
    }

    // Determine winner
    if (attacker.health <= 0) {
      winner = defender;
      battleLog = [...battleLog, `¡${defender.name || defender.type_id} ha vencido!`];
    } else {
      winner = attacker;
      battleLog = [...battleLog, `¡${attacker.name || attacker.type_id} ha vencido!`];
    }

    battleEnded = true;
    
    // Update game state
    await updateGameState();
    
    // Return to map after shorter delay (reduced from 2000ms to 1000ms)
    setTimeout(() => {
      navigate('/map');
    }, 1000);
  }

  async function updateGameState() {
    try {
      if (!gameData) return;
      
      const loser = winner === attacker ? defender : attacker;
      const loserOwner = loser.owner;
      const loserPosition = loser.position;
      
      // Remove the defeated unit from the game data
      if (loserOwner === 'player') {
        const playerUnitIndex = gameData.player.units.findIndex(unit => 
          unit.id === loser.id || 
          (Array.isArray(unit.position) && 
           Array.isArray(loserPosition) && 
           unit.position[0] === loserPosition[0] && 
           unit.position[1] === loserPosition[1])
        );
        
        if (playerUnitIndex !== -1) {
          gameData.player.units.splice(playerUnitIndex, 1);
        }
      } else if (loserOwner === 'ia') {
        const aiUnitIndex = gameData.ia.units.findIndex(unit => 
          unit.id === loser.id || 
          (Array.isArray(unit.position) && 
           Array.isArray(loserPosition) && 
           unit.position[0] === loserPosition[0] && 
           unit.position[1] === loserPosition[1])
        );
        
        if (aiUnitIndex !== -1) {
          gameData.ia.units.splice(aiUnitIndex, 1);
        }
      }
      
      // Update the winner's health in the game data
      const winnerOwner = winner.owner;
      const winnerPosition = winner.position;
      
      if (winnerOwner === 'player') {
        const playerUnitIndex = gameData.player.units.findIndex(unit => 
          unit.id === winner.id || 
          (Array.isArray(unit.position) && 
           Array.isArray(winnerPosition) && 
           unit.position[0] === winnerPosition[0] && 
           unit.position[1] === winnerPosition[1])
        );
        
        if (playerUnitIndex !== -1) {
          gameData.player.units[playerUnitIndex].health = winner.health;
          // Mark unit as having attacked this turn
          gameData.player.units[playerUnitIndex].status = 'exhausted';
          gameData.player.units[playerUnitIndex].remainingMovement = 0;
        }
      } else if (winnerOwner === 'ia') {
        const aiUnitIndex = gameData.ia.units.findIndex(unit => 
          unit.id === winner.id || 
          (Array.isArray(unit.position) && 
           Array.isArray(winnerPosition) && 
           unit.position[0] === winnerPosition[0] && 
           unit.position[1] === winnerPosition[1])
        );
        
        if (aiUnitIndex !== -1) {
          gameData.ia.units[aiUnitIndex].health = winner.health;
          // Mark AI unit as having attacked
          gameData.ia.units[aiUnitIndex].status = 'exhausted';
          gameData.ia.units[aiUnitIndex].remainingMovement = 0;
        }
      }
      
      // Update game session
      await gameAPI.updateGameSession(gameData);
      
      // Store updated game data for Map.svelte to use
      gameAPI.storeTemporaryData('updatedGameData', gameData);
      
    } catch (error) {
      console.error('Error updating game state after battle:', error);
      battleLog = [...battleLog, `Error: ${error.message}`];
    }
  }

  // Helper to get unit icon based on type
  function getUnitIcon(unitType) {
    switch (unitType) {
      case "warrior": return './ia_assets/warrior.png';
      case "settler": return './ia_assets/settler.png';
      case "cavalry": return './ia_assets/cavalry.png';
      case "archer": return './ia_assets/archer.png';
      default: return null;
    }
  }
</script>

<svelte:head>
  <title>Batalla - Civilization Game</title>
</svelte:head>

<div class="battle-page">
  <div class="battle-container">
    <div class="battle-header">
      <h2>Batalla</h2>
    </div>
    
    <div class="battle-arena">
      {#if attacker && defender}
        <!-- Attacker -->
        <div class="unit attacker" class:animating={attackerAnimating}>
          <div class="unit-portrait">
            {#if getUnitIcon(attacker.type_id)}
              <img src={getUnitIcon(attacker.type_id)} alt={attacker.type_id} />
            {:else}
              <div class="unit-fallback">{attacker.type_id?.charAt(0).toUpperCase() || 'U'}</div>
            {/if}
          </div>
          <div class="unit-info">
            <h3>{attacker.name || attacker.type_id}</h3>
            <div class="unit-stats">
              <div class="stat">
                <span class="stat-label">❤️ Vida:</span>
                <div class="health-bar">
                  <div class="health-fill" style="width: {Math.max(0, attacker.health)}%"></div>
                </div>
                <span class="stat-value">{Math.max(0, attacker.health)}</span>
              </div>
              <div class="stat">
                <span class="stat-label">⚔️ Ataque:</span>
                <span class="stat-value">{attacker.attack}</span>
              </div>
              <div class="stat">
                <span class="stat-label">🛡️ Defensa:</span>
                <span class="stat-value">{attacker.defense}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- VS indicator -->
        <div class="vs-indicator">
          <span>VS</span>
        </div>
        
        <!-- Defender -->
        <div class="unit defender" class:animating={defenderAnimating}>
          <div class="unit-portrait">
            {#if getUnitIcon(defender.type_id)}
              <img src={getUnitIcon(defender.type_id)} alt={defender.type_id} />
            {:else}
              <div class="unit-fallback">{defender.type_id?.charAt(0).toUpperCase() || 'U'}</div>
            {/if}
          </div>
          <div class="unit-info">
            <h3>{defender.name || defender.type_id}</h3>
            <div class="unit-stats">
              <div class="stat">
                <span class="stat-label">❤️ Vida:</span>
                <div class="health-bar">
                  <div class="health-fill" style="width: {Math.max(0, defender.health)}%"></div>
                </div>
                <span class="stat-value">{Math.max(0, defender.health)}</span>
              </div>
              <div class="stat">
                <span class="stat-label">⚔️ Ataque:</span>
                <span class="stat-value">{defender.attack}</span>
              </div>
              <div class="stat">
                <span class="stat-label">🛡️ Defensa:</span>
                <span class="stat-value">{defender.defense}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Damage number display -->
        {#if showDamageNumber}
          <div class="damage-number {damagePosition === 'attacker' ? 'on-attacker' : 'on-defender'}">
            -{damageAmount}
          </div>
        {/if}
      {/if}
    </div>
    
    <div class="battle-log">
      <h3>Registro de batalla</h3>
      <div class="log-content">
        {#each battleLog as entry}
          <p>{entry}</p>
        {/each}
      </div>
    </div>
    
    {#if battleEnded && winner}
      <div class="battle-result">
        <h2 class="winner-announcement">
          {winner.owner === 'player' ? '¡Has vencido!' : '¡Has sido derrotado!'}
        </h2>
      </div>
    {/if}
  </div>
</div>

<style>
  .battle-page {
    width: 100%;
    height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), 
                url('./ia_assets/battle_background.jpg') no-repeat center center;
    background-size: cover;
    color: white;
    font-family: 'Arial', sans-serif;
  }

  .battle-container {
    width: 90%;
    max-width: 1000px;
    height: 90%;
    display: flex;
    flex-direction: column;
    background-color: rgba(32, 32, 32, 0.85);
    border-radius: 10px;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.5);
    overflow: hidden;
  }

  .battle-header {
    padding: 10px 20px;
    background-color: rgba(68, 30, 10, 0.8);
    text-align: center;
  }

  .battle-header h2 {
    margin: 0;
    font-size: 28px;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
  }

  .battle-arena {
    position: relative;
    flex-grow: 1;
    display: flex;
    justify-content: space-around;
    align-items: center;
    padding: 20px;
    background: rgba(20, 20, 20, 0.6);
    min-height: 250px;
  }

  .unit {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 40%;
    max-width: 350px;
    background-color: rgba(48, 48, 48, 0.8);
    border-radius: 8px;
    padding: 15px;
    transition: transform 0.3s ease;
  }

  .unit.animating {
    animation: attack 0.6s ease-in-out;
  }

  @keyframes attack {
    0% { transform: translateX(0); }
    25% { transform: translateX(calc(20% * (var(--direction, 1)))); }
    100% { transform: translateX(0); }
  }

  .attacker.animating {
    --direction: 1;
  }

  .defender.animating {
    --direction: -1;
  }

  .unit-portrait {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    background-color: #2c2c2c;
    margin-bottom: 10px;
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
    border: 3px solid #ca973f;
  }

  .unit-portrait img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .unit-fallback {
    font-size: 42px;
    font-weight: bold;
    color: #ddd;
  }

  .unit-info {
    width: 100%;
    text-align: center;
  }

  .unit-info h3 {
    margin: 0 0 10px 0;
    font-size: 20px;
    font-weight: bold;
    color: #eee;
  }

  .unit-stats {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .stat {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
  }

  .stat-label {
    min-width: 80px;
    text-align: left;
  }

  .stat-value {
    font-weight: bold;
    color: #ffcc00;
  }

  .health-bar {
    flex-grow: 1;
    height: 12px;
    background-color: #444;
    border-radius: 4px;
    overflow: hidden;
  }

  .health-fill {
    height: 100%;
    background: linear-gradient(to right, #ff0000, #ff6600);
    transition: width 0.5s ease;
  }

  .vs-indicator {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    font-size: 36px;
    font-weight: bold;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.7);
    color: #ffcc00;
  }

  .damage-number {
    position: absolute;
    font-size: 28px;
    font-weight: bold;
    color: #ff3030;
    text-shadow: 2px 2px 0px rgba(0, 0, 0, 0.8);
    animation: damage-popup 1s ease-out forwards;
    z-index: 10;
  }

  .on-attacker {
    left: 25%;
    top: 25%;
  }

  .on-defender {
    right: 25%;
    top: 25%;
  }

  @keyframes damage-popup {
    0% { opacity: 0; transform: translateY(0); }
    20% { opacity: 1; }
    100% { opacity: 0; transform: translateY(-50px); }
  }

  .battle-log {
    height: 30%;
    padding: 15px;
    background-color: rgba(34, 34, 34, 0.9);
    overflow-y: auto;
  }

  .battle-log h3 {
    margin-top: 0;
    margin-bottom: 10px;
    color: #ffcc00;
    font-size: 18px;
  }

  .log-content {
    height: calc(100% - 30px);
    overflow-y: auto;
  }

  .log-content p {
    margin: 5px 0;
    font-size: 14px;
    color: #ddd;
  }

  .battle-result {
    padding: 15px;
    text-align: center;
    background-color: rgba(20, 20, 20, 0.8);
  }

  .winner-announcement {
    font-size: 24px;
    color: #ffcc00;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
    animation: pulse 1s infinite alternate;
  }

  @keyframes pulse {
    from { transform: scale(1); }
    to { transform: scale(1.05); }
  }

  @media (max-width: 768px) {
    .battle-arena {
      flex-direction: column;
      gap: 20px;
    }

    .unit {
      width: 90%;
    }

    .vs-indicator {
      position: relative;
      transform: none;
      margin: 10px 0;
    }
  }
</style>
