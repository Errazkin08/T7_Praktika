<script>
  import { navigate } from '../router.js';
  import { setUser } from '../stores/auth.js';
  
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
        error = "Pasahitzak ez datoz bat";
        return;
      }
      
      isLoading = true;
      console.log("Register attempt:", username, email);
      
      // Call the registration API
      const registerResponse = await fetch('/api/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }), // Email might not be needed based on your API
      });
      
      if (!registerResponse.ok) {
        const errorData = await registerResponse.json();
        throw new Error(errorData.error || "Registration failed. Please try again.");
      }
      
      // After successful registration, login automatically
      const loginResponse = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
      });
      
      if (!loginResponse.ok) {
        throw new Error("Registration successful but login failed. Please try logging in manually.");
      }
      
      const loginData = await loginResponse.json();
      
      // Store user data in the auth store
      setUser(loginData.user);
      
      // Navigate to home page after successful registration and login
      navigate('/home');
      
    } catch (err) {
      console.error("Registration error:", err);
      error = err.message || "Erregistratzeak huts egin du. Saiatu berriro.";
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="register">
  <h1>Erregistratu</h1>
  
  {#if error}
    <div class="error-message">{error}</div>
  {/if}
  
  <form on:submit|preventDefault={handleSubmit}>
    <div class="form-group">
      <label for="username">Erabiltzaile-izena</label>
      <input type="text" id="username" bind:value={username} required disabled={isLoading} />
    </div>
    
    <div class="form-group">
      <label for="email">Helbide elektronikoa</label>
      <input type="email" id="email" bind:value={email} required disabled={isLoading} />
    </div>
    
    <div class="form-group">
      <label for="password">Pasahitza</label>
      <input type="password" id="password" bind:value={password} required disabled={isLoading} />
    </div>
    
    <div class="form-group">
      <label for="confirmPassword">Pasahitza berretsi</label>
      <input type="password" id="confirmPassword" bind:value={confirmPassword} required disabled={isLoading} />
    </div>
    
    <button type="submit" disabled={isLoading}>
      {#if isLoading}
        Kargatzen...
      {:else}
        Erregistratu
      {/if}
    </button>
  </form>
  
  <p>
    Dagoeneko kontua duzu? <a href="/login" on:click|preventDefault={() => navigate('/login')}>Hasi saioa</a>
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
