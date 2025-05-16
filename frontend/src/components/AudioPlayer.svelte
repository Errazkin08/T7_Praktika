<script>
  import { onMount, onDestroy } from 'svelte';
  import { writable } from 'svelte/store';

  // Crear stores para música
  export const musicEnabled = writable(
    localStorage.getItem("musicEnabled") !== "false" // true por defecto
  );
  export const musicVolume = writable(
    parseFloat(localStorage.getItem("musicVolume") || "0.5") // 0.5 por defecto
  );

  // Lista de pistas de música para el juego
  const musicTracks = [
    "../../music/Musika1.mp3",
    "../../music/Musika2.mp3",
    "../../music/Musika3.mp3",
    // Añade más pistas según necesites
  ];

  let audioElement;
  let currentTrackIndex = 0;
  let initialized = false;

  // Inicializar reproducción después de interacción del usuario
  export function initializeAudio() {
    if (initialized) return;
    
    try {
      audioElement.volume = $musicVolume;
      audioElement.play().then(() => {
        initialized = true;
        console.log("Audio initialized successfully");
      }).catch(error => {
        console.error("Failed to initialize audio:", error);
      });
    } catch (error) {
      console.error("Error initializing audio:", error);
    }
  }

  // Cambiar volumen cuando cambie el store
  $: if (audioElement && initialized) {
    audioElement.volume = $musicVolume;
    if ($musicEnabled) {
      audioElement.play().catch(e => console.log("Auto-play prevented:", e));
    } else {
      audioElement.pause();
    }
  }

  // Reproducir siguiente pista cuando termine la actual
  function playNextTrack() {
    currentTrackIndex = (currentTrackIndex + 1) % musicTracks.length;
    audioElement.src = musicTracks[currentTrackIndex];
    if ($musicEnabled && initialized) {
      audioElement.play().catch(e => console.log("Play failed:", e));
    }
  }

  onMount(() => {
    // Crear elemento de audio
    audioElement = new Audio();
    
    // Verificar si existe el archivo de audio antes de asignarlo
    if (musicTracks.length > 0) {
      audioElement.src = musicTracks[currentTrackIndex];
      audioElement.loop = false; // No usar loop interno
      audioElement.addEventListener('ended', playNextTrack);
      audioElement.volume = $musicVolume;
    }
    
    // Guardar preferencias cuando cambien
    const unsubVolume = musicVolume.subscribe(value => {
      localStorage.setItem("musicVolume", value.toString());
    });
    
    const unsubEnabled = musicEnabled.subscribe(value => {
      localStorage.setItem("musicEnabled", value.toString());
    });
    
    return () => {
      unsubVolume();
      unsubEnabled();
    };
  });

  onDestroy(() => {
    if (audioElement) {
      audioElement.removeEventListener('ended', playNextTrack);
      audioElement.pause();
      audioElement = null;
    }
  });

  export function toggleMusic() {
    musicEnabled.update(value => !value);
  }

  export function setVolume(value) {
    musicVolume.set(Math.max(0, Math.min(1, value)));
  }
</script>

<!-- Control de música flotante -->
<div class="audio-controls">
  <button 
    on:click={toggleMusic}
    class="audio-toggle"
    title={$musicEnabled ? "Silenciar música" : "Activar música"}
  >
    {#if $musicEnabled}
      🔊
    {:else}
      🔇
    {/if}
  </button>
  
  <input 
    type="range" 
    min="0" 
    max="1" 
    step="0.01" 
    bind:value={$musicVolume} 
    class="volume-slider"
    title="Volumen"
  />
</div>

<style>
  .audio-controls {
    position: fixed;
    bottom: 10px;
    right: 10px;
    background: rgba(0, 0, 0, 0.5);
    padding: 5px 10px;
    border-radius: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    z-index: 9999;
  }
  
  .audio-toggle {
    background: none;
    border: none;
    color: white;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .volume-slider {
    width: 80px;
    cursor: pointer;
  }
</style>