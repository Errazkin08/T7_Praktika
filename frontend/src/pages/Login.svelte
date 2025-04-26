<script>
  import { navigate } from '../lib/router.js';
  let username = "";
  let password = "";
  
  function handleSubmit() {
    console.log("Login attempt:", username);
    // This would normally call an API
  }
</script>

<div class="login">
  <h1>Login</h1>
  
  <form on:submit|preventDefault={handleSubmit}>
    <div class="form-group">
      <label for="username">Username</label>
      <input type="text" id="username" bind:value={username} required />
    </div>
    
    <div class="form-group">
      <label for="password">Password</label>
      <input type="password" id="password" bind:value={password} required />
    </div>
    
    <button type="submit">Login</button>
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
</style>
