<script>
  import { onMount, onDestroy } from 'svelte';
  import { currentRoute } from '../router.js';
  
  // Track whether we're on the map page
  $: isMapPage = $currentRoute === '/map';
  
  function updateScrollClasses() {
    if (isMapPage) {
      document.documentElement.classList.add('map-active');
      document.body.classList.add('map-active');
    } else {
      document.documentElement.classList.remove('map-active');
      document.body.classList.remove('map-active');
      
      // Force scrolling to be enabled
      document.documentElement.style.overflow = 'auto';
      document.body.style.overflow = 'auto';
    }
  }
  
  // Update whenever route changes
  $: {
    if (typeof document !== 'undefined') {
      updateScrollClasses();
    }
  }
  
  onMount(() => {
    updateScrollClasses();
    
    // Ensure scrolling is enabled on non-map pages
    if (!isMapPage) {
      document.documentElement.style.overflow = 'auto';
      document.body.style.overflow = 'auto';
    }
  });
  
  onDestroy(() => {
    // Always restore scrolling when component is destroyed
    document.documentElement.classList.remove('map-active');
    document.body.classList.remove('map-active');
    document.documentElement.style.overflow = 'auto';
    document.body.style.overflow = 'auto';
  });
</script>
