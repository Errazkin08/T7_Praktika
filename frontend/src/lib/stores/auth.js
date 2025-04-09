import { writable } from 'svelte/store';

// User store to manage authentication state
export const user = writable(null);

// Helper functions for auth
export const login = async (username, password) => {
  try {
    const response = await fetch('http://localhost:5000/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Login failed');
    }
    
    const data = await response.json();
    user.set(data.user);
    return { success: true };
  } catch (error) {
    return { 
      success: false, 
      error: error.message || 'Something went wrong during login' 
    };
  }
};

export const register = async (username, email, password) => {
  try {
    const response = await fetch('http://localhost:5000/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, email, password }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Registration failed');
    }
    
    return { success: true };
  } catch (error) {
    return { 
      success: false, 
      error: error.message || 'Something went wrong during registration' 
    };
  }
};

export const logout = async () => {
  user.set(null);
  // We'll implement the actual logout endpoint later
  // This is just a placeholder for now
  return { success: true };
};