<script>
  import { navigate } from '../router.js';
  import { loginUser } from '../api.js';
  import { setUser } from '../stores/auth.js';
  
  let username = "";
  let password = "";
  let error = "";
  let isLoading = false;
  
  async function handleSubmit() {
    try {
      error = "";
      isLoading = true;
      
      console.log("Login attempt:", username);
      const response = await loginUser(username, password);
      
      // Store user data in the auth store
      setUser({
        username: response.user.username,
        score: response.user.score,
        level: response.user.level
      });
      
      // Navigate to home page after successful login
      navigate('/');
    } catch (err) {
      console.error("Login error:", err);
      error = err.message || "Failed to login. Please check your credentials.";
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="login">
  <h1>Login</h1>
  
  {#if error}
    <div class="error-message">{error}</div>
  {/if}
  
  <form on:submit|preventDefault={handleSubmit}>
    <div class="form-group">
      <label for="username">Username</label>
      <input type="text" id="username" bind:value={username} required disabled={isLoading} />
    </div>
    
    <div class="form-group">
      <label for="password">Password</label>
      <input type="password" id="password" bind:value={password} required disabled={isLoading} />
    </div>
    
    <button type="submit" disabled={isLoading}>
      {#if isLoading}
        Loading...
      {:else}
        Login
      {/if}
    </button>
  </form>
  
  <p>
    Don't have an account? <a href="/register" on:click|preventDefault={() => navigate('/register')}>Register</a>
  </p>
</div>

<style>
  .login {
    max-width: 400px;
    margin: 0 auto;
    padding: 1rem;
  }
  
  .form-group {
    margin-bottom: 1rem;
  }
  
  label {
    display: block;
    margin-bottom: 0.5rem;
  }
  
  input {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
  }
  
  button {
    background-color: #4c66af;
    color: white;
    border: none;
    padding: 0.75rem 1rem;
    border-radius: 4px;
    cursor: pointer;
    width: 100%;
  }
  
  button:disabled {
    background-color: #a0a0a0;
    cursor: not-allowed;
  }
  
  .error-message {
    color: #d32f2f;
    background-color: #ffebee;
    padding: 0.75rem;
    border-radius: 4px;
    margin-bottom: 1rem;
    border: 1px solid #ffcdd2;
  }
</style>
