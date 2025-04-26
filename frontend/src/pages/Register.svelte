<script>
  import { navigate } from '../router.js'; // Updated import path
  let username = "";
  let email = "";
  let password = "";
  let confirmPassword = "";
  
  function handleSubmit() {
    console.log("Register attempt:", username, email);
    // This would normally call an API
  }
</script>

<div class="register">
  <h1>Register</h1>
  
  <form on:submit|preventDefault={handleSubmit}>
    <div class="form-group">
      <label for="username">Username</label>
      <input type="text" id="username" bind:value={username} required />
    </div>
    
    <div class="form-group">
      <label for="email">Email</label>
      <input type="email" id="email" bind:value={email} required />
    </div>
    
    <div class="form-group">
      <label for="password">Password</label>
      <input type="password" id="password" bind:value={password} required />
    </div>
    
    <div class="form-group">
      <label for="confirmPassword">Confirm Password</label>
      <input type="password" id="confirmPassword" bind:value={confirmPassword} required />
    </div>
    
    <button type="submit">Register</button>
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
</style>
