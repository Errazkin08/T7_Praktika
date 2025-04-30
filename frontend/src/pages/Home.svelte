<script>
  import { navigate } from '../router.js';
  import { user } from '../stores/auth.js';
  import { onMount } from 'svelte';
  
  // Redirect to welcome page if not logged in
  onMount(() => {
    if (!$user) {
      navigate('/');
    }
  });
</script>

<div class="dashboard">
  <div class="welcome-header">
    <h1>Welcome, {$user ? $user.username : 'Player'}</h1>
    <p>Choose an option to start playing</p>
  </div>
  
  <div class="options-container">
    <div class="option-card" on:click={() => navigate('/new-game')}>
      <div class="option-icon">🎮</div>
      <h2>New Game</h2>
      <p>Start a new CIVilizaTu and conquer the world</p>
    </div>
    
    <div class="option-card" on:click={() => navigate('/load-game')}>
      <div class="option-icon">💾</div>
      <h2>Load Game</h2>
      <p>Continue one of your saved games</p>
    </div>
  </div>
</div>

<style>
  .dashboard {
    max-width: 1000px;
    margin: 0 auto;
    padding: 2rem 1rem;
  }
  
  .welcome-header {
    text-align: center;
    margin-bottom: 3rem;
  }
  
  .welcome-header h1 {
    font-size: 2.2rem;
    color: #333;
    margin-bottom: 0.5rem;
  }
  
  .welcome-header p {
    font-size: 1.2rem;
    color: #666;
  }
  
  .options-container {
    display: flex;
    justify-content: center;
    gap: 2rem;
    flex-wrap: wrap;
  }
  
  .option-card {
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    padding: 2rem;
    width: 300px;
    cursor: pointer;
    transition: all 0.3s ease;
    text-align: center;
  }
  
  .option-card:hover {
    transform: translateY(-10px);
    box-shadow: 0 15px 20px rgba(0, 0, 0, 0.15);
  }
  
  .option-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }
  
  .option-card h2 {
    font-size: 1.8rem;
    margin-bottom: 1rem;
    color: #333;
  }
  
  .option-card p {
    color: #666;
    line-height: 1.5;
  }
</style>
