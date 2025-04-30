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
    turnNumber: 1
  }));
}

export function pauseGame(isPaused) {
  gameState.update(state => ({
    ...state,
    isPaused
  }));
}

export function endGame() {
  gameState.set(initialState);
}
