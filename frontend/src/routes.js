import Home from './pages/Home.svelte';
import Proba from './pages/Proba.svelte';
import NotFound from './pages/NotFound.svelte';
import Login from './pages/Login.svelte';
import Register from './pages/Register.svelte';

// Define routes
const routes = {
  '/': Home,
  '/proba': Proba,
  '/login': Login,
  '/register': Register,
  '*': NotFound
};

export default routes;
