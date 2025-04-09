<script>
  import { onMount } from 'svelte';
  import { navigating } from '$app/stores';
  import { goto } from '$app/navigation';
  import { user } from '$lib/stores/auth';
  
  onMount(() => {
    // Check if user is logged in on app load
    const checkAuth = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/auth/profile', {
          method: 'GET',
          credentials: 'include'
        });
        
        if (response.ok) {
          const userData = await response.json();
          user.set(userData);
        } else {
          user.set(null);
          if (window.location.pathname !== '/login' && 
              window.location.pathname !== '/register') {
            goto('/login');
          }
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        user.set(null);
      }
    };
    
    checkAuth();
  });
</script>

<header>
  <nav>
    <div class="logo">Civilization Game</div>
    <div class="nav-links">
      {#if $user}
        <a href="/games">My Games</a>
        <a href="/profile">Profile</a>
        <button on:click={() => {
          fetch('http://localhost:5000/api/auth/logout', {
            method: 'POST',
            credentials: 'include'
          }).then(() => {
            user.set(null);
            goto('/login');
          });
        }}>Logout</button>
      {:else}
        <a href="/login">Login</a>
        <a href="/register">Register</a>
      {/if}
    </div>
  </nav>
</header>

{#if $navigating}
  <div class="loading-indicator">Loading...</div>
{/if}

<main>
  <slot />
</main>

<footer>
  <p>© 2025 Civilization Game Project</p>
</footer>

<style>
  header {
    background-color: #333;
    color: white;
    padding: 1rem;
  }
  
  nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .logo {
    font-size: 1.5rem;
    font-weight: bold;
  }
  
  .nav-links a, .nav-links button {
    color: white;
    margin-left: 1rem;
    text-decoration: none;
  }
  
  .nav-links button {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1rem;
  }
  
  main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }
  
  footer {
    background-color: #333;
    color: white;
    text-align: center;
    padding: 1rem;
    position: fixed;
    bottom: 0;
    width: 100%;
  }
  
  .loading-indicator {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    background-color: #ffcc00;
    color: #333;
    text-align: center;
    padding: 0.5rem;
    z-index: 1000;
  }
</style>