<script>
  import { register } from '$lib/stores/auth';
  import { goto } from '$app/navigation';
  
  let username = '';
  let email = '';
  let password = '';
  let confirmPassword = '';
  let errorMessage = '';
  let isLoading = false;
  
  async function handleSubmit() {
    errorMessage = '';
    
    if (password !== confirmPassword) {
      errorMessage = 'Passwords do not match';
      return;
    }
    
    isLoading = true;
    const result = await register(username, email, password);
    isLoading = false;
    
    if (result.success) {
      goto('/login?registered=true');
    } else {
      errorMessage = result.error;
    }
  }
</script>

<svelte:head>
  <title>Register - Civilization Game</title>
</svelte:head>

<div class="register-container">
  <h1>Register</h1>
  
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
      <label for="email">Email</label>
      <input 
        type="email" 
        id="email" 
        bind:value={email} 
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
    
    <div class="form-group">
      <label for="confirmPassword">Confirm Password</label>
      <input 
        type="password" 
        id="confirmPassword" 
        bind:value={confirmPassword} 
        required 
        disabled={isLoading} 
      />
    </div>
    
    <button type="submit" disabled={isLoading}>
      {isLoading ? 'Registering...' : 'Register'}
    </button>
  </form>
  
  <p class="login-link">
    Already have an account? <a href="/login">Login here</a>
  </p>
</div>

<style>
  .register-container {
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
  
  .login-link {
    text-align: center;
    margin-top: 1rem;
  }
</style>