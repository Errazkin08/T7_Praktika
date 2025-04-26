import App from './App.svelte';
import './app.css';
import { initRouter } from './router.js'; // Updated import path

// Initialize the router
initRouter();

const app = new App({
  target: document.getElementById('app')
});

export default app;
