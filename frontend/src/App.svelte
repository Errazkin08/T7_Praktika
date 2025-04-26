<script>
  import { currentRoute, navigate } from './router.js'; // Updated import path
  import routes from './routes';
  
  // Get the component for the current route
  $: component = routes[$currentRoute] || routes['*'];
</script>

<header>
  <nav>
    <div class="logo">Civilization Game</div>
    <div class="nav-links">
      <a href="/" on:click|preventDefault={() => navigate('/')}>Home</a>
      <a href="/proba" on:click|preventDefault={() => navigate('/proba')}>Proba</a>
      <a href="/login" on:click|preventDefault={() => navigate('/login')}>Login</a>
      <a href="/register" on:click|preventDefault={() => navigate('/register')}>Register</a>
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
