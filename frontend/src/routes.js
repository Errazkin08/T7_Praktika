import Home from './pages/Home.svelte';
import Welcome from './pages/Welcome.svelte';
import Proba from './pages/Proba.svelte';
import NotFound from './pages/NotFound.svelte';
import Login from './pages/Login.svelte';
import Register from './pages/Register.svelte';
import Map from './pages/Map.svelte';
import NewGame from './pages/NewGame.svelte';
import LoadGame from './pages/LoadGame.svelte';
import Maps from './pages/Maps.svelte';
import City from './pages/City.svelte';

// Define routes
const routes = {
  '/': Welcome,
  '/home': Home,
  '/proba': Proba,
  '/login': Login,
  '/register': Register,
  '/map': Map,
  '/new-game': NewGame,
  '/load-game': LoadGame,
  '/maps': Maps,
  '/city': City,
  '*': NotFound
};

export default routes;
