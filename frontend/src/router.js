import { writable } from 'svelte/store';
import routes from './routes.js';

// Create a store for the current route
export const currentRoute = writable(window.location.pathname);

// Handle browser navigation
window.addEventListener('popstate', () => {
  currentRoute.set(window.location.pathname);
});

// Function to navigate to a new route
export function navigate(path) {
  // Update browser history
  window.history.pushState({}, '', path);
  
  // Update the current route store
  currentRoute.set(path);
}

// Initialize the router when the page loads
export function initRouter() {
  // Handle clicks on links with internal hrefs
  document.addEventListener('click', (event) => {
    // Check if it's a link click with an internal href
    const anchor = event.target.closest('a');
    if (anchor && anchor.href.includes(window.location.origin) && !event._isRouterHandled) {
      event.preventDefault();
      
      // Get the path from the href
      const path = new URL(anchor.href).pathname;
      
      // Navigate to the new route
      navigate(path);
    }
  });
  
  // Set initial route
  currentRoute.set(window.location.pathname);
}
