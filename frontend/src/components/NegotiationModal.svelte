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
    <h3>🤝 Negociar con la IA</h3>
    <p class="subtitle">Propón un intercambio de recursos y un alto al fuego:</p>
    
    <div class="negotiation-section">
      <h4>Tu oferta a la IA</h4>
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
            <small class="max-info">Máx: {playerResources?.[res] || 0}</small>
          </div>
        {/each}
      </div>
    </div>
    
    <div class="negotiation-section">
      <h4>Lo que pides a la IA</h4>
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
            <small class="max-info">Máx: {aiResources?.[res] || 0}</small>
          </div>
        {/each}
      </div>
    </div>
    
    <div class="negotiation-section ceasefire-section">
      <label>Turnos de alto al fuego:
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
      <button class="cancel-btn" on:click={() => dispatch("close")}>Cancelar</button>
      <button class="send-btn" on:click={sendOffer} disabled={loading}>Enviar Oferta</button>
    </div>
    
    {#if loading}
      <div class="loading-msg">Cargando...</div>
    {/if}
    
    {#if error}
      <div class="error">{error}</div>
    {/if}
    
    {#if aiResponse}
      <div class="ai-response">
        <h4>Respuesta de la IA:</h4>
        {#if aiResponse.accepted}
          <div class="accepted">¡La IA ha aceptado tu oferta! <span class="emoji">✅</span></div>
        {:else if aiResponse.counter_offer}
          <div>
            <div class="counter-title">La IA propone una contraoferta:</div>
            <div class="counter-offer-table">
              <div class="counter-offer-row header">
                <div>Recurso</div>
                <div>Tú ofreces</div>
                <div>Pides a la IA</div>
              </div>
              {#each resourceKeys as res}
                <div class="counter-offer-row">
                  <div>{res.charAt(0).toUpperCase() + res.slice(1)}</div>
                  <div class="counter-value">{offer.player[res]}</div>
                  <div class="counter-value">{offer.ai[res]}</div>
                </div>
              {/each}
              <div class="counter-offer-row">
                <div>Turnos de paz</div>
                <div class="counter-value" colspan="2">{offer.ceasefireTurns}</div>
              </div>
            </div>
            <div class="counter-offer-info">
              <span>La IA ha modificado la oferta. Puedes aceptarla o modificarla y volver a enviar.</span>
            </div>
            <button class="accept-counter-btn" on:click={acceptCounterOffer}>Aceptar Contraoferta</button>
          </div>
        {:else}
          <div class="rejected">La IA ha rechazado la oferta. <span class="emoji">❌</span></div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; width: 100vw; height: 100vh;
  background: rgba(10, 15, 30, 0.85);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}
.modal-content {
  background: linear-gradient(135deg, #23263a 80%, #181a26 100%);
  border-radius: 18px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.55);
  padding: 2.5rem 2.2rem 2rem 2.2rem;
  min-width: 370px;
  max-width: 420px;
  border: 2px solid #2e3650;
  position: relative;
  animation: modal-in 0.3s;
  max-height: 90vh;
  overflow-y: auto;
}
@keyframes modal-in {
  from { opacity: 0; transform: translateY(-30px) scale(0.97);}
  to   { opacity: 1; transform: translateY(0) scale(1);}
}
h3 {
  margin-top: 0;
  margin-bottom: 0.5rem;
  font-size: 1.6rem;
  color: #e0e6f7;
  letter-spacing: 0.5px;
  font-weight: 700;
  text-align: center;
}
.subtitle {
  color: #b2b8d6;
  font-size: 1.05rem;
  margin-bottom: 1.2rem;
  text-align: center;
}
.negotiation-section {
  margin-bottom: 1.2rem;
}
.negotiation-section h4 {
  margin: 0 0 0.5rem 0;
  color: #b2b8d6;
  font-size: 1.08rem;
  font-weight: 600;
}
.resource-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem 1.2rem;
  margin-bottom: 0.2rem;
}
.resource-field {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 90px;
  margin-bottom: 0.2rem;
}
.resource-field label {
  font-size: 0.98rem;
  color: #b2b8d6;
  margin-bottom: 0.1rem;
  font-weight: 500;
}
.resource-field input {
  width: 60px;
  padding: 4px 6px;
  border-radius: 6px;
  border: 1.5px solid #2e3650;
  background: #23263a;
  color: #e0e6f7;
  font-size: 1rem;
  transition: border 0.2s, background 0.2s;
}
.resource-field input:focus {
  border: 1.5px solid #5b7cff;
  outline: none;
  background: #23263a;
}
.max-info {
  color: #888;
  font-size: 0.85em;
  margin-top: 2px;
  margin-left: 2px;
}
.ceasefire-section label {
  font-size: 1.05rem;
  color: #b2b8d6;
  font-weight: 500;
}
.ceasefire-section input {
  width: 60px;
  margin-left: 0.5rem;
  padding: 4px 6px;
  border-radius: 6px;
  border: 1.5px solid #2e3650;
  background: #23263a;
  color: #e0e6f7;
  font-size: 1rem;
  transition: border 0.2s, background 0.2s;
}
.ceasefire-section input:focus {
  border: 1.5px solid #5b7cff;
  outline: none;
  background: #23263a;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.2rem;
}
.cancel-btn, .send-btn, .accept-counter-btn {
  padding: 0.5rem 1.2rem;
  border-radius: 7px;
  border: none;
  font-size: 1.05rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.18s, color 0.18s, box-shadow 0.18s;
}
.cancel-btn {
  background: #23263a;
  color: #b2b8d6;
  border: 1.5px solid #2e3650;
}
.cancel-btn:hover {
  background: #181a26;
}
.send-btn {
  background: linear-gradient(90deg, #5b7cff 60%, #23263a 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(91,124,255,0.07);
}
.send-btn:disabled {
  background: #2e3650;
  color: #b2b8d6;
  cursor: not-allowed;
}
.send-btn:hover:enabled {
  background: linear-gradient(90deg, #23263a 60%, #5b7cff 100%);
}
.accept-counter-btn {
  background: #388e3c;
  color: #fff;
  margin-top: 0.7rem;
}
.accept-counter-btn:hover {
  background: #256c27;
}
.loading-msg {
  margin-top: 1rem;
  color: #5b7cff;
  font-weight: 500;
  text-align: center;
}
.error {
  color: #ff6b6b;
  margin-top: 0.7rem;
  text-align: center;
  font-weight: 600;
}
.ia-response {
  margin-top: 1.2rem;
  background: #23263a;
  padding: 1.1rem 1rem 1rem 1rem;
  border-radius: 10px;
  border: 1.5px solid #2e3650;
  box-shadow: 0 2px 8px rgba(91,124,255,0.04);
  color: #e0e6f7;
  font-size: 1.08rem;
}
.accepted, .rejected {
  font-size: 1.15rem;
  font-weight: 600;
  margin-top: 0.5rem;
  text-align: center;
}
.accepted { color: #4caf50; }
.rejected { color: #ff6b6b; }
.emoji { font-size: 1.3em; vertical-align: middle; }
.counter-title {
  font-weight: 600;
  color: #b2b8d6;
  margin-bottom: 0.4rem;
}
.counter-offer-table {
  margin: 0.7rem 0 0.5rem 0;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #2e3650;
  background: #181a26;
  font-size: 0.98rem;
}
.counter-offer-row {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #2e3650;
}
.counter-offer-row.header {
  background: #23263a;
  color: #b2b8d6;
  font-weight: 600;
}
.counter-offer-row:last-child {
  border-bottom: none;
}
.counter-offer-row > div {
  flex: 1;
  padding: 0.4rem 0.7rem;
  text-align: center;
}
.counter-value {
  color: #5b7cff;
  font-weight: 600;
}
.counter-offer-info {
  margin: 0.5rem 0 0.2rem 0;
  color: #b2b8d6;
  font-size: 0.95rem;
  text-align: center;
}
@media (max-width: 500px) {
  .modal-content {
    min-width: 95vw;
    padding: 1.2rem 0.5rem;
  }
  .resource-row { flex-direction: column; gap: 0.5rem 0; }
}
</style>
