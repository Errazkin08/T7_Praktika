<script>
  import { currentRoute, navigate } from './router.js';
  import routes from './routes';
  import { user, clearUser } from './stores/auth.js';
  import ScrollManager from './components/ScrollManager.svelte';
  
  // Get the component for the current route
  $: component = routes[$currentRoute] || routes['*'];
  
  function handleLogout() {
    clearUser();
    navigate('/');
  }
  
  // Check if we're on a page that should have minimal UI
  // Add city page to the game pages that need full screen
  $: isGamePage = $currentRoute === '/map' || $currentRoute === '/city';
  $: isAuthPage = $currentRoute === '/login' || $currentRoute === '/register' || $currentRoute === '/';
  $: showHeader = !isGamePage;
  $: showFooter = !isGamePage && !isAuthPage;
</script>

<ScrollManager />

{#if showHeader}
<header class:minimal={isAuthPage}>
  <nav>
    <div class="logo">CIVilizaTu Game</div>
    <div class="nav-links">
      {#if $user}
        <a href="/home" on:click|preventDefault={() => navigate('/home')}>Dashboard</a>
        <span class="user-welcome">Welcome, {$user.username}</span>
        <a href="/" on:click|preventDefault={handleLogout}>Logout</a>
      {:else if !isAuthPage}
        <a href="/login" on:click|preventDefault={() => navigate('/login')}>Login</a>
        <a href="/register" on:click|preventDefault={() => navigate('/register')}>Register</a>
      {/if}
    </div>
  </nav>
</header>
{/if}

<main class:full-height={isAuthPage || isGamePage} class:game-view={isGamePage}>
  <svelte:component this={component} />
</main>

{#if showFooter}
<footer>
  <p>© 2025 Civilization Game Project</p>
</footer>
{/if}

<style>
  header {
    background-color: #333;
    color: white;
    padding: 1rem;
  }
  
  header.minimal {
    padding: 0.5rem 1rem;
    background-color: rgba(51, 51, 51, 0.8);
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
  
  .nav-links {
    display: flex;
    align-items: center;
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
  
  main.full-height {
    max-width: 100%;
    padding: 0;
    min-height: calc(100vh - 60px);
  }
  
  main.map-view {
    max-width: none;
    padding: 0;
    margin: 0;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
  }
  
  main.game-view {
    max-width: none;
    padding: 0;
    margin: 0;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
  }
  
  footer {
    background-color: #333;
    color: white;
    text-align: center;
    padding: 1rem;
  }
</style>
