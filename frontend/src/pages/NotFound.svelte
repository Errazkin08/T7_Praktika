<script>
  import { navigate } from '../router.js'; // Updated import path
</script>

<div class="not-found">
  <h1>404 - Orrialdea ez da aurkitu</h1>
  <p>Bilatzen ari zaren orrialdea ez da existitzen edo mugitu egin da.</p>
  <a href="/" on:click|preventDefault={() => navigate('/')}>Itzuli hasierako orrira</a>
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
