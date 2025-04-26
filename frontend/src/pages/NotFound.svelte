<script>
  import { navigate } from '../lib/router.js';
</script>

<div class="not-found">
  <h1>404 - Page Not Found</h1>
  <p>The page you are looking for doesn't exist or has been moved.</p>
  <a href="/" on:click|preventDefault={() => navigate('/')}>Go back to Home</a>
</div>

<style>
  .not-found {
    text-align: center;
    padding: 2rem;
  }
  
  h1 {
    color: #d32f2f;
  }
</style>
