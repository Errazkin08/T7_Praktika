<script>
  import { login } from '$lib/stores/auth';
  import { goto } from '$app/navigation';
  
  let username = '';
  let password = '';
  let errorMessage = '';
  let isLoading = false;
  
  async function handleSubmit() {
    errorMessage = '';
    isLoading = true;
    
    const result = await login(username, password);
    
    isLoading = false;
    
    if (result.success) {
      goto('/games');
    } else {
      errorMessage = result.error;
    }
  }
</script>

<svelte:head>
  <title>Login - Civilization Game</title>
</svelte:head>

<div class="login-container">
  <h1>Login</h1>
  
  {#if errorMessage}
    <div class="error-message">{errorMessage}</div>
  {/if}
  
  <form on:submit|preventDefault={handleSubmit}>
    <div class="form-group">
      <label for="username">Username</label>
      <input 
        type="text" 
        id="username" 
        bind:value={username} 
        required 
        disabled={isLoading} 
      />
    </div>
    
    <div class="form-group">
      <label for="password">Password</label>
      <input 
        type="password" 
        id="password" 
        bind:value={password} 
        required 
        disabled={isLoading} 
      />
    </div>
    
    <button type="submit" disabled={isLoading}>
      {isLoading ? 'Logging in...' : 'Login'}
    </button>
  </form>
  
  <p class="register-link">
    Don't have an account? <a href="/register">Register here</a>
  </p>
</div>

<style>
  .login-container {
    max-width: 400px;
    margin: 2rem auto;
    padding: 2rem;
    border: 1px solid #ddd;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  h1 {
    text-align: center;
    margin-bottom: 1.5rem;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: bold;
  }
  
  input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 1rem;
  }
  
  button {
    width: 100%;
    padding: 0.75rem;
    background-color: #4c66af;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  
  button:hover {
    background-color: #3a4f8a;
  }
  
  button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
  }
  
  .error-message {
    background-color: #ffdddd;
    color: #ff0000;
    padding: 0.5rem;
    margin-bottom: 1rem;
    border-radius: 4px;
    text-align: center;
  }
  
  .register-link {
    text-align: center;
    margin-top: 1rem;
  }
</style>