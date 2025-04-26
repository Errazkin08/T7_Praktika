<script>
  import { currentRoute, navigate } from './router.js';
  import routes from './routes';
  import { user, clearUser } from './stores/auth.js';
  
  // Get the component for the current route
  $: component = routes[$currentRoute] || routes['*'];
  
  function handleLogout() {
    clearUser();
    navigate('/');
  }
</script>

<header>
  <nav>
    <div class="logo">Civilization Game</div>
    <div class="nav-links">
      <a href="/" on:click|preventDefault={() => navigate('/')}>Home</a>
      <a href="/proba" on:click|preventDefault={() => navigate('/proba')}>Proba</a>
      <a href="/map" on:click|preventDefault={() => navigate('/map')}>Map</a>
      
      {#if $user}
        <!-- Show these links when user is logged in -->
        <span class="user-welcome">Welcome, {$user.username}</span>
        <a href="/profile" on:click|preventDefault={() => navigate('/profile')}>Profile</a>
        <a href="/" on:click|preventDefault={handleLogout}>Logout</a>
      {:else}
        <!-- Show these links when user is logged out -->
        <a href="/login" on:click|preventDefault={() => navigate('/login')}>Login</a>
        <a href="/register" on:click|preventDefault={() => navigate('/register')}>Register</a>
      {/if}
    </div>
  </nav>
</header>

<main>
  <svelte:component this={component} />
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
  
  .nav-links a {
    color: white;
    margin-left: 1rem;
    text-decoration: none;
  }
  
  .user-welcome {
    color: #ffcc00;
    margin-left: 1rem;
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
</style>
