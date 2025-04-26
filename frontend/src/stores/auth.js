import { writable } from 'svelte/store';

// Initialize from localStorage if available
const storedUser = localStorage.getItem('user');
const initialUser = storedUser ? JSON.parse(storedUser) : null;

// Create the auth store
export const user = writable(initialUser);

// Save to localStorage when user changes
user.subscribe(value => {
    if (value) {
        localStorage.setItem('user', JSON.stringify(value));
    } else {
        localStorage.removeItem('user');
    }
});

// Helper functions
export function setUser(userData) {
    user.set(userData);
}

export function clearUser() {
    user.set(null);
}

export function isLoggedIn() {
    let currentUser;
    user.subscribe(value => { currentUser = value; })();
    return !!currentUser;
}
