import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  server: {
    host: '0.0.0.0',
    port: 80,
    proxy: {
      // Use the service name instead of localhost
      '/proba': {
        target: 'http://backend:5000',
        changeOrigin: true
      },
      '/api': {
        target: 'http://backend:5000',
        changeOrigin: true
      }
    }
  }
});
