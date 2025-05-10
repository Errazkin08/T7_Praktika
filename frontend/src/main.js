import App from './App.svelte';
import './styles/global.css'; // Import global CSS before any other styles
import './app.css';

// Global scroll fix - ensure we remove map-active class on page loads/refreshes
if (typeof window !== 'undefined') {
  // Remove map-active class on page load
  window.addEventListener('load', () => {
    if (window.location.pathname !== '/map') {
      document.body.classList.remove('map-active');
      document.documentElement.classList.remove('map-active');
      document.body.style.overflow = 'auto';
      document.documentElement.style.overflow = 'auto';
    }
  });
}

const app = new App({
  target: document.getElementById('app')
});

export default app;
