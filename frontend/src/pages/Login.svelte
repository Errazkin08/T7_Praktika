<script>
  import { navigate } from '../router.js';
  import { setUser } from '../stores/auth.js';
  
  let username = "";
  let password = "";
  let error = "";
  let isLoading = false;
  
  async function handleSubmit() {
    try {
      error = "";
      isLoading = true;
      
      // Call the backend login endpoint
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Important to include cookies
        body: JSON.stringify({ username, password }),
      });
      
      // First check if response is ok before trying to parse JSON
      if (!response.ok) {
        // Try to parse error response as JSON, but have a fallback
        let errorMessage;
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || `Error: ${response.status} ${response.statusText}`;
        } catch (e) {
          // If JSON parsing fails, use status text
          errorMessage = `Error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      // Safely parse the response
      let data;
      try {
        data = await response.json();
      } catch (e) {
        throw new Error("Invalid response format from server");
      }
      
      // Store user data in the auth store
      if (data && data.user) {
        setUser(data.user);
        
        // Navigate to home page after successful login
        navigate('/home');
      } else {
        throw new Error("Login response missing user data");
      }
    } catch (err) {
      console.error("Login error:", err);
      error = err.message || "Saioa hastean huts egin du. Egiaztatu zure kredentzialak.";
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="login">
  <h1>Hasi saioa</h1>
  
  {#if error}
    <div class="error-message">{error}</div>
  {/if}
  
  <form on:submit|preventDefault={handleSubmit}>
    <div class="form-group">
      <label for="username">Erabiltzaile-izena</label>
      <input type="text" id="username" bind:value={username} required disabled={isLoading} />
    </div>
    
    <div class="form-group">
      <label for="password">Pasahitza</label>
      <input type="password" id="password" bind:value={password} required disabled={isLoading} />
    </div>
    
    <button type="submit" disabled={isLoading}>
      {#if isLoading}
        Kargatzen...
      {:else}
        Hasi saioa
      {/if}
    </button>
  </form>
  
  <p>
    Ez duzu konturik? <a href="/register" on:click|preventDefault={() => navigate('/register')}>Erregistratu</a>
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
