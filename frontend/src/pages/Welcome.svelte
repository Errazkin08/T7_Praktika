<script>
  import { navigate } from '../router.js';
  import { user } from '../stores/auth.js';
  import { onMount } from 'svelte';
  
  // Redirect if already logged in
  onMount(() => {
    if ($user) {
      navigate('/home');
    }
  });
</script>

<div class="welcome-page">
  <div class="welcome-container">
    <h1>CIVilizaTu Game</h1>
    <p>Welcome to the CIVilizaTu Strategy Game</p>
    
    <div class="action-buttons">
      <button class="btn-primary" on:click={() => navigate('/login')}>
        Login
      </button>
      <button class="btn-secondary" on:click={() => navigate('/register')}>
        Register
      </button>
    </div>
  </div>
</div>

<style>
  .welcome-page {
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    background: linear-gradient(135deg, #1a2a6c, #b21f1f, #fdbb2d);
    min-height: calc(100vh - 150px);
  }
  
  .welcome-container {
    background-color: rgba(255, 255, 255, 0.9);
    padding: 3rem;
    border-radius: 8px;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    text-align: center;
    max-width: 500px;
    width: 100%;
  }
  
  h1 {
    font-size: 2.5rem;
    color: #333;
    margin-bottom: 1rem;
  }
  
  p {
    font-size: 1.2rem;
    color: #666;
    margin-bottom: 2rem;
  }
  
  .action-buttons {
    display: flex;
    justify-content: center;
    gap: 1rem;
  }
  
  button {
    padding: 0.8rem 2rem;
    border: none;
    border-radius: 4px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    min-width: 150px;
  }
  
  button:hover {
    transform: translateY(-3px);
  }
  
  .btn-primary {
    background-color: #4CAF50;
    color: white;
  }
  
  .btn-secondary {
    background-color: #2196F3;
    color: white;
  }
</style>
