<script>
  import { onMount } from 'svelte';
  import { getHello } from '../api'; // Updated import path

  let message = "Loading...";
  let error = null;
  let loading = true;

  // Fetch data from API on component mount
  onMount(async () => {
    try {
      loading = true;
      const response = await getHello();
      console.log("API Response:", response);
      message = response;
      error = null;
    } catch (err) {
      console.error("API Error:", err);
      error = err.message;
      message = "Error";
    } finally {
      loading = false;
    }
  });
</script>

<div class="proba-page">
  <h1>Proba API Test</h1>
  
  {#if loading}
    <div class="loading">Loading...</div>
  {:else if error}
    <div class="error">
      <p>Error connecting to API:</p>
      <p>{error}</p>
    </div>
  {:else}
    <div class="success">
      <h2>API Response:</h2>
      <p class="message">{message}</p>
    </div>
  {/if}
  
  <p>Check the browser console for the full response details.</p>
</div>

<style>
  .proba-page {
    max-width: 600px;
    margin: 0 auto;
    padding: 2rem;
    text-align: center;
  }
  
  .loading {
    color: #888;
    font-style: italic;
  }
  
  .error {
    color: #d32f2f;
    padding: 1rem;
    border: 1px solid #d32f2f;
    border-radius: 4px;
  }
  
  .success {
    color: #388e3c;
    padding: 1rem;
    border: 1px solid #388e3c;
    border-radius: 4px;
  }
  
  .message {
    font-size: 1.5rem;
    font-weight: bold;
  }
</style>
