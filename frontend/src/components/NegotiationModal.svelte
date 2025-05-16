<script>
  import { createEventDispatcher, onMount } from "svelte";
  import { gameAPI } from "../services/gameAPI.js";

  export let unit;
  
  // Initialize with empty objects that will be populated from session
  let playerResources = {};
  let aiResources = {};
  let gameData = null;

  const dispatch = createEventDispatcher();

  // Default empty resources object for safety
  const defaultResources = { food: 0, gold: 0, wood: 0, iron: 0, stone: 0 };
  let offer = {
    player: { ...defaultResources },
    ai: { ...defaultResources },
    ceasefireTurns: 3
  };
  
  let loading = false;
  let error = null;
  let aiResponse = null;
  let counterOffer = null;
  let resourceKeys = Object.keys(defaultResources);

  // Load game data on component mount
  onMount(async () => {
    try {
      gameData = await gameAPI.getCurrentGame();
      if (gameData) {
        // Set player resources
        if (gameData.player && gameData.player.resources) {
          playerResources = { ...defaultResources, ...gameData.player.resources };
        }
        
        // Set AI resources
        if (gameData.ia && gameData.ia.resources) {
          aiResources = { ...defaultResources, ...gameData.ia.resources };
        }
        
        console.log("Loaded resources:", { player: playerResources, ai: aiResources });
      }
    } catch (e) {
      console.error("Error loading game data:", e);
      error = "Error cargando datos del juego";
    }
  });

  // Helper para limpiar null/undefined/negativos -> 0 antes de enviar y limitar máximos
  function sanitizeOffer(obj, maxObj = {}) {
    const sanitized = {};
    for (const key of resourceKeys) {
      let val = obj[key];
      if (val === "" || val === null || val === undefined || isNaN(val)) val = 0;
      val = Number(val);
      if (val < 0) val = 0;
      // Limitar al máximo permitido si se especifica
      if (maxObj && typeof maxObj[key] === "number" && val > maxObj[key]) {
        val = maxObj[key];
      }
      sanitized[key] = val;
    }
    return sanitized;
  }
  
  async function finalizeDeal(deal) {
    // deal: { player, ai, ceasefireTurns }
    try {
      // Obtener el estado actual del juego si no lo tenemos ya
      if (!gameData) {
        gameData = await gameAPI.getCurrentGame();
      }

      // Actualizar recursos del jugador
      for (const res of resourceKeys) {
        if (!gameData.player.resources) gameData.player.resources = { ...defaultResources };
        gameData.player.resources[res] = (gameData.player.resources[res] || 0) - (deal.player[res] || 0) + (deal.ai[res] || 0);
      }
      
      // Actualizar recursos de la IA
      for (const res of resourceKeys) {
        if (!gameData.ia.resources) gameData.ia.resources = { ...defaultResources };
        gameData.ia.resources[res] = (gameData.ia.resources[res] || 0) - (deal.ai[res] || 0) + (deal.player[res] || 0);
      }
      
      // Actualizar o crear ceasefireTurns
      gameData.ceasefire_turns = deal.ceasefireTurns || 0;
      gameData.ceasefire_active = deal.ceasefireTurns > 0;

      // Guardar el estado actualizado
      await gameAPI.updateGameSession(gameData);

      // Notificar resultado al componente padre
      dispatch("result", { 
        accepted: true, 
        ceasefire_turns: deal.ceasefireTurns 
      });
      
      // No cerramos aquí - el componente padre se encargará
    } catch (e) {
      error = "Error al finalizar el trato: " + (e.message || e);
    }
  }

  async function sendOffer() {
    loading = true;
    error = null;
    aiResponse = null;
    counterOffer = null;
    
    // Limpiar nulls, negativos y limitar máximos antes de enviar
    const cleanOffer = {
      player: sanitizeOffer(offer.player, playerResources),
      ai: sanitizeOffer(offer.ai, aiResources),
      ceasefireTurns:
        offer.ceasefireTurns === null ||
        offer.ceasefireTurns === undefined ||
        isNaN(offer.ceasefireTurns) ||
        offer.ceasefireTurns < 0
          ? 0
          : Number(offer.ceasefireTurns)
    };
    
    // Actualizar el formulario con los valores ajustados antes de enviar
    offer.player = { ...cleanOffer.player };
    offer.ai = { ...cleanOffer.ai };
    offer.ceasefireTurns = cleanOffer.ceasefireTurns;

    try {
      console.log("[NEGOCIACIÓN] Petición enviada a la IA:", JSON.stringify(cleanOffer, null, 2));
      const result = await gameAPI.negotiateWithAI({
        offer: cleanOffer,
        game_state: gameData || await gameAPI.getCurrentGame()
      });
      
      console.log("[NEGOCIACIÓN] Respuesta completa de la IA:", result);
      if (result && result.counter_offer) {
        console.log("[NEGOCIACIÓN] Contraoferta de la IA:", result.counter_offer);
        // Mostrar la contraoferta de forma editable y limitar máximos
        counterOffer = {
          player: sanitizeOffer(result.counter_offer.player || {}, playerResources),
          ai: sanitizeOffer(result.counter_offer.ai || {}, aiResources),
          ceasefireTurns:
            result.counter_offer.ceasefireTurns === null ||
            result.counter_offer.ceasefireTurns === undefined ||
            isNaN(result.counter_offer.ceasefireTurns) ||
            result.counter_offer.ceasefireTurns < 0
              ? 0
              : Number(result.counter_offer.ceasefireTurns)
        };
        
        // Actualiza los valores del formulario para mostrar la contraoferta
        offer = JSON.parse(JSON.stringify(counterOffer));
      }
      
      aiResponse = result;
      dispatch("result", result);
      
      // Si la IA acepta la oferta, finalizar el trato despues de mostrar la respuesta durante 2 segundos
      if (result.accepted) {
        setTimeout(() => {
          finalizeDeal(cleanOffer);
        }, 2000);
      }
    } catch (e) {
      error = e.message || "Error en la negociación";
    } finally {
      loading = false;
    }
  }

  async function acceptCounterOffer() {
    // Aquí podrías actualizar el estado del juego según la contraoferta
    await finalizeDeal(offer);
  }
</script>

<div class="modal-overlay">
  <div class="modal-content">
    <h3>🤝 IArekin negoziatu</h3>
    <p class="subtitle">Proposatu baliabide-trukea eta bakea:</p>
    
    <div class="negotiation-section">
      <h4>Zure eskaintza IAri</h4>
      <div class="resource-row">
        {#each resourceKeys as res}
          <div class="resource-field">
            <label for={"player-" + res}>{res.charAt(0).toUpperCase() + res.slice(1)}:</label>
            <input
              id={"player-" + res}
              type="number"
              min="0"
              max={playerResources?.[res] || 0}
              bind:value={offer.player[res]}
              on:input={() => {
                // Si el campo queda vacío o negativo, poner 0
                if (
                  offer.player[res] === "" ||
                  offer.player[res] === null ||
                  offer.player[res] === undefined ||
                  Number(offer.player[res]) < 0
                ) offer.player[res] = 0;
                // Limitar al máximo permitido
                if (playerResources?.[res] !== undefined && Number(offer.player[res]) > playerResources[res]) {
                  offer.player[res] = playerResources[res];
                }
              }}
            />
            <small class="max-info">Geh: {playerResources?.[res] || 0}</small>
          </div>
        {/each}
      </div>
    </div>
    
    <div class="negotiation-section">
      <h4>IAri eskatzen diozuna</h4>
      <div class="resource-row">
        {#each resourceKeys as res}
          <div class="resource-field">
            <label for={"ai-" + res}>{res.charAt(0).toUpperCase() + res.slice(1)}:</label>
            <input
              id={"ai-" + res}
              type="number"
              min="0"
              max={aiResources?.[res] || 9999}
              bind:value={offer.ai[res]}
              on:input={() => {
                if (
                  offer.ai[res] === "" ||
                  offer.ai[res] === null ||
                  offer.ai[res] === undefined ||
                  Number(offer.ai[res]) < 0
                ) offer.ai[res] = 0;
                if (aiResources?.[res] !== undefined && Number(offer.ai[res]) > aiResources[res]) {
                  offer.ai[res] = aiResources[res];
                }
              }}
            />
            <small class="max-info">Geh: {aiResources?.[res] || 0}</small>
          </div>
        {/each}
      </div>
    </div>
    
    <div class="negotiation-section ceasefire-section">
      <label>Bake txandak:
        <input
          type="number"
          min="1"
          max="20"
          bind:value={offer.ceasefireTurns}
          on:input={() => {
            if (
              offer.ceasefireTurns === "" ||
              offer.ceasefireTurns === null ||
              offer.ceasefireTurns === undefined ||
              Number(offer.ceasefireTurns) < 0
            ) offer.ceasefireTurns = 0;
          }}
        />
      </label>
    </div>
    
    <div class="modal-actions">
      <button class="cancel-btn" on:click={() => dispatch("close")}>Utzi</button>
      <button class="send-btn" on:click={sendOffer} disabled={loading}>
        {#if !loading}
          Eskaintza Bidali
        {:else}
          <span class="spinner"></span>
        {/if}
      </button>
    </div>
    
    {#if loading}
      <div class="loading-msg">Kargatzen<span class="dot-animation">...</span></div>
    {/if}
    
    {#if error}
      <div class="error">
        <i class="error-icon">⚠️</i> {error}
      </div>
    {/if}
    
    {#if aiResponse}
      <div class="ai-response">
        <h4>IAren erantzuna:</h4>
        {#if aiResponse.accepted}
          <div class="accepted"><i class="success-icon">✅</i> IAk zure eskaintza onartu du!</div>
        {:else if aiResponse.counter_offer}
          <div>
            <div class="counter-title">IAk kontraeskaintza bat proposatzen du:</div>
            <div class="counter-offer-table">
              <div class="counter-offer-row header">
                <div>Baliabidea</div>
                <div>Zuk eskaintzen duzu</div>
                <div>IAri eskatzen diozu</div>
              </div>
              {#each resourceKeys as res}
                <div class="counter-offer-row">
                  <div>{res.charAt(0).toUpperCase() + res.slice(1)}</div>
                  <div class="counter-value">{offer.player[res]}</div>
                  <div class="counter-value">{offer.ai[res]}</div>
                </div>
              {/each}
              <div class="counter-offer-row">
                <div>Bake txandak</div>
                <div class="counter-value" colspan="2">{offer.ceasefireTurns}</div>
              </div>
            </div>
            <div class="counter-offer-info">
              <span>IAk eskaintza aldatu du. Onar dezakezu edo aldatu eta berriro bidali.</span>
            </div>
            <button class="accept-counter-btn" on:click={acceptCounterOffer}>Kontraeskaintza Onartu</button>
          </div>
        {:else}
          <div class="rejected"><i class="error-icon">❌</i> IAk eskaintza baztertu du.</div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
:root {
  --bg-primary: #151825;
  --bg-secondary: #1e2235;
  --bg-tertiary: #272b45;
  --text-primary: #e8ecf8;
  --text-secondary: #b9c0de;
  --accent: #6c8fff;
  --accent-secondary: #ff6b8e;
  --success: #4caf50;
  --error: #ff6b6b;
  --border: #3a406a;
}

.modal-overlay {
  position: fixed;
  top: 0; left: 0; width: 100vw; height: 100vh;
  background: rgba(7, 10, 25, 0.92);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: linear-gradient(160deg, var(--bg-secondary) 0%, var(--bg-primary) 100%);
  border-radius: 20px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.6), 0 0 20px rgba(108,143,255,0.15);
  padding: 2.5rem 2.5rem 2.2rem;
  min-width: 380px;
  max-width: 440px;
  border: 1px solid var(--border);
  position: relative;
  animation: modal-in 0.4s cubic-bezier(0.19, 1, 0.22, 1);
  max-height: 90vh;
  overflow-y: auto;
}

@keyframes modal-in {
  from { opacity: 0; transform: translateY(-40px) scale(0.95);}
  to   { opacity: 1; transform: translateY(0) scale(1);}
}

h3 {
  margin-top: 0;
  margin-bottom: 0.7rem;
  font-size: 1.7rem;
  color: var(--text-primary);
  letter-spacing: 0.5px;
  font-weight: 700;
  text-align: center;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.subtitle {
  color: var(--text-secondary);
  font-size: 1.05rem;
  margin-bottom: 1.5rem;
  text-align: center;
  font-weight: 400;
}

.negotiation-section {
  margin-bottom: 1.5rem;
  background: rgba(30, 34, 53, 0.4);
  padding: 1.2rem;
  border-radius: 16px;
  border: 1px solid rgba(58, 64, 106, 0.4);
  transition: all 0.2s ease;
}

.negotiation-section:hover {
  background: rgba(30, 34, 53, 0.6);
  border: 1px solid rgba(58, 64, 106, 0.6);
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.negotiation-section h4 {
  margin: 0 0 0.8rem 0;
  color: var(--accent);
  font-size: 1.1rem;
  font-weight: 600;
}

.resource-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.9rem 1.4rem;
  margin-bottom: 0.2rem;
}

.resource-field {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 90px;
  margin-bottom: 0.4rem;
}

.resource-field label {
  font-size: 0.95rem;
  color: var(--text-secondary);
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.resource-field input, .ceasefire-section input {
  width: 70px;
  padding: 6px 10px;
  border-radius: 10px;
  border: 2px solid rgba(58, 64, 106, 0.6);
  background: rgba(21, 24, 37, 0.7);
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.2s ease;
}

.resource-field input:focus, .ceasefire-section input:focus {
  border: 2px solid var(--accent);
  outline: none;
  background: rgba(21, 24, 37, 0.9);
  box-shadow: 0 0 0 3px rgba(108,143,255,0.15);
}

.max-info {
  color: #828aa8;
  font-size: 0.85em;
  margin-top: 4px;
  margin-left: 2px;
}

.ceasefire-section {
  display: flex;
  justify-content: center;
}

.ceasefire-section label {
  font-size: 1.05rem;
  color: var(--text-secondary);
  font-weight: 500;
  display: flex;
  align-items: center;
}

.ceasefire-section input {
  width: 60px;
  margin-left: 0.8rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.8rem;
}

.cancel-btn, .send-btn, .accept-counter-btn {
  padding: 0.65rem 1.4rem;
  border-radius: 12px;
  border: none;
  font-size: 1.05rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.cancel-btn {
  background: rgba(30, 34, 53, 0.8);
  color: var(--text-secondary);
  border: 2px solid rgba(58, 64, 106, 0.6);
}

.cancel-btn:hover {
  background: rgba(21, 24, 37, 0.9);
  transform: translateY(-2px);
}

.send-btn {
  background: linear-gradient(135deg, var(--accent) 0%, #5367dd 100%);
  color: #fff;
  box-shadow: 0 4px 15px rgba(108,143,255,0.25);
  min-width: 150px;
  position: relative;
}

.send-btn:disabled {
  background: #2e3650;
  color: #8c94b7;
  box-shadow: none;
  cursor: not-allowed;
  transform: none;
}

.send-btn:hover:enabled {
  background: linear-gradient(135deg, #5b7cff 0%, #4a5dcf 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(108,143,255,0.3);
}

.accept-counter-btn {
  background: linear-gradient(135deg, var(--success) 0%, #388e3c 100%);
  color: #fff;
  margin-top: 1rem;
  box-shadow: 0 4px 15px rgba(76,175,80,0.2);
  width: 100%;
  font-size: 1.1rem;
  padding: 0.7rem 0;
}

.accept-counter-btn:hover {
  background: linear-gradient(135deg, #45a049 0%, #2e7d32 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(76,175,80,0.3);
}

.loading-msg {
  margin-top: 1rem;
  color: var(--accent);
  font-weight: 500;
  text-align: center;
  font-size: 1.1rem;
}

.dot-animation {
  animation: dots 1.5s infinite;
  display: inline-block;
  width: 20px;
}

@keyframes dots {
  0%, 20% { content: "."; }
  40% { content: ".."; }
  60%, 100% { content: "..."; }
}

.spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error {
  color: var(--error);
  margin-top: 1rem;
  text-align: center;
  font-weight: 600;
  background: rgba(255,107,107,0.1);
  border: 1px solid rgba(255,107,107,0.3);
  padding: 0.7rem;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-icon, .success-icon {
  margin-right: 0.5rem;
  font-style: normal;
  font-size: 1.2rem;
}

.ai-response {
  margin-top: 1.8rem;
  background: linear-gradient(135deg, rgba(30, 34, 53, 0.6) 0%, rgba(21, 24, 37, 0.6) 100%);
  padding: 1.3rem 1.2rem 1.2rem;
  border-radius: 16px;
  border: 1px solid rgba(58, 64, 106, 0.5);
  box-shadow: 0 8px 20px rgba(0,0,0,0.2);
  color: var(--text-primary);
  font-size: 1.08rem;
  animation: fade-in 0.5s ease-out;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.ai-response h4 {
  color: var(--accent);
  margin-top: 0;
  margin-bottom: 1rem;
  text-align: center;
  font-size: 1.2rem;
  font-weight: 600;
}

.accepted, .rejected {
  font-size: 1.2rem;
  font-weight: 600;
  margin-top: 0.5rem;
  text-align: center;
  padding: 0.8rem;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.accepted { 
  color: var(--success); 
  background: rgba(76,175,80,0.1);
  border: 1px solid rgba(76,175,80,0.2);
}

.rejected { 
  color: var(--error); 
  background: rgba(255,107,107,0.1);
  border: 1px solid rgba(255,107,107,0.2);
}

.emoji { 
  font-size: 1.4em; 
  vertical-align: middle; 
  margin-right: 0.5rem;
}

.counter-title {
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 1rem;
  text-align: center;
  font-size: 1.1rem;
}

.counter-offer-table {
  margin: 1.2rem 0;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
  background: rgba(21, 24, 37, 0.5);
  font-size: 0.98rem;
  box-shadow: 0 6px 16px rgba(0,0,0,0.2);
}

.counter-offer-row {
  display: flex;
  align-items: center;
  border-bottom: 1px solid rgba(58, 64, 106, 0.4);
  transition: background 0.2s;
}

.counter-offer-row.header {
  background: linear-gradient(90deg, var(--bg-tertiary) 0%, var(--bg-secondary) 100%);
  color: var(--text-secondary);
  font-weight: 600;
  padding: 0.5rem 0;
}

.counter-offer-row:not(.header):hover {
  background: rgba(108,143,255,0.05);
}

.counter-offer-row:last-child {
  border-bottom: none;
}

.counter-offer-row > div {
  flex: 1;
  padding: 0.6rem 0.7rem;
  text-align: center;
}

.counter-value {
  color: var(--accent);
  font-weight: 600;
}

.counter-offer-info {
  margin: 0.8rem 0;
  color: var(--text-secondary);
  font-size: 0.95rem;
  text-align: center;
  padding: 0.6rem;
  background: rgba(21, 24, 37, 0.3);
  border-radius: 8px;
}

@media (max-width: 500px) {
  .modal-content {
    min-width: 95vw;
    padding: 1.5rem 1rem;
  }
  .resource-row { 
    flex-direction: column; 
    gap: 0.6rem; 
  }
  .negotiation-section {
    padding: 1rem;
  }
}
</style>
