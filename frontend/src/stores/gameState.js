import { writable } from 'svelte/store';

// Initial game state
const initialState = {
  currentScenario: null,
  gameInProgress: false,
  gameName: "",
  isPaused: false,
  turnNumber: 1,
  mapSize: { width: 30, height: 30 }
};

// Create the game store
export const gameState = writable(initialState);

// New stores for turn and current player
export const currentTurn = writable(1);
export const currentPlayer = writable("player"); // 'player' or 'ia'

// Helper functions
export function setCurrentScenario(scenario) {
  gameState.update(state => ({
    ...state,
    currentScenario: scenario
  }));
}

export function startGame(name, scenario) {
  gameState.update(state => ({
    ...state,
    gameInProgress: true,
    gameName: name,
    currentScenario: scenario,
    turnNumber: scenario.turnNumber || 1,
    mapSize: { 
      width: scenario.width || 30, 
      height: scenario.height || 15 
    }
  }));
  currentTurn.set(scenario.turnNumber || 1); // Initialize turn from scenario or default to 1
  currentPlayer.set("player"); // Player always starts
  console.log("Game started with scenario:", scenario, "Turn:", scenario.turnNumber || 1);
}

export function pauseGame(isPaused) {
  gameState.update(state => ({
    ...state,
    isPaused
  }));
}

export function endGame() {
  gameState.set(initialState);
  currentTurn.set(1);
  currentPlayer.set("player");
  console.log("Game ended and state reset.");
}

export function updateMapSize(width, height) {
  gameState.update(state => ({
    ...state,
    mapSize: { width, height }
  }));
}

export function nextTurn() {
  gameState.update(state => ({
    ...state,
    turnNumber: state.turnNumber + 1
  }));
}

export function updateGameScenario(scenario) {
  gameState.update(state => ({
    ...state,
    currentScenario: scenario,
  }));
  if (scenario && typeof scenario.turnNumber !== 'undefined') {
    currentTurn.set(scenario.turnNumber);
  }
  if (scenario && scenario.currentPlayer) {
    currentPlayer.set(scenario.currentPlayer);
  }
}
