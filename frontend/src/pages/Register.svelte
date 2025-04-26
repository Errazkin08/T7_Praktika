<script>
  import { navigate } from '../router.js';
  import { registerUser } from '../api.js';
  
  let username = "";
  let email = "";
  let password = "";
  let confirmPassword = "";
  let error = "";
  let isLoading = false;
  
  async function handleSubmit() {
    try {
      // Reset error
      error = "";
      
      // Client-side validation
      if (password !== confirmPassword) {
        error = "Passwords do not match";
        return;
      }
      
      isLoading = true;
      console.log("Register attempt:", username, email);
      
      // Call the API
      await registerUser(username, email, password);
      
      // Navigate to login after successful registration
      navigate('/login');
      
    } catch (err) {
      console.error("Registration error:", err);
      error = err.message || "Registration failed. Please try again.";
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="register">
  <h1>Register</h1>
  
  {#if error}
    <div class="error-message">{error}</div>
  {/if}
  
  <form on:submit|preventDefault={handleSubmit}>
    <div class="form-group">
      <label for="username">Username</label>
      <input type="text" id="username" bind:value={username} required disabled={isLoading} />
    </div>
    
    <div class="form-group">
      <label for="email">Email</label>
      <input type="email" id="email" bind:value={email} required disabled={isLoading} />
    </div>
    
    <div class="form-group">
      <label for="password">Password</label>
      <input type="password" id="password" bind:value={password} required disabled={isLoading} />
    </div>
    
    <div class="form-group">
      <label for="confirmPassword">Confirm Password</label>
      <input type="password" id="confirmPassword" bind:value={confirmPassword} required disabled={isLoading} />
    </div>
    
    <button type="submit" disabled={isLoading}>
      {#if isLoading}
        Loading...
      {:else}
        Register
      {/if}
    </button>
  </form>
  
  <p>
    Already have an account? <a href="/login" on:click|preventDefault={() => navigate('/login')}>Login</a>
  </p>
</div>

<style>
  .register {
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
