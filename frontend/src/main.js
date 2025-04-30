import App from './App.svelte';
import './app.css';
import { initRouter } from './router.js';

// Initialize the router outside try block
initRouter();

let app;
// Initialize with basic error handling
try {
  console.log("Starting application...");
  
  // Create the app instance
  app = new App({
    target: document.getElementById('app')
  });
  
  console.log("App initialized successfully");
} catch (error) {
  console.error("Critical error initializing app:", error);
  
  // Show a visible error message in the DOM
  document.body.innerHTML = `
    <div style="padding: 20px; background-color: #ffebee; color: #c62828; font-family: sans-serif; text-align: center;">
      <h2>Application Error</h2>
      <p>The application could not be loaded due to an error.</p>
      <pre style="background: #f8f8f8; padding: 10px; overflow: auto; text-align: left;">${error.stack || error.message || 'Unknown error'}</pre>
      <button onclick="window.location.reload()">Reload Application</button>
    </div>
  `;
}

// Export the app at top level
export default app;
