// API service for backend communication

// Change this to use relative URLs which will go through the Vite proxy
const API_BASE_URL = '';  // Empty string will use relative URLs

/**
 * Send a request to the API
 * @param {string} endpoint - API endpoint to call
 * @param {Object} options - Fetch options
 * @returns {Promise<any>} Response data
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        credentials: 'include', // For session cookies
    };
    
    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
    }
    
    return response.json();
}

/**
 * Send a request to the API expecting a text response
 * @param {string} endpoint - API endpoint to call
 * @param {Object} options - Fetch options
 * @returns {Promise<string>} Response text
 */
async function apiTextRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultOptions = {
        // No method specified here means it defaults to GET request
        headers: {
            'Accept': 'text/plain',
        },
        credentials: 'include',
    };
    
    try {
        console.log(`Making request to: ${url}`);
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`API request failed with status ${response.status}`);
        }
        
        return response.text();
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

// API endpoints as functions
export async function getHello() {
    // Using apiTextRequest for text response from /proba
    console.log('Calling /proba endpoint');
    return apiTextRequest('/proba');
}

export async function getHealth() {
    return apiRequest('/api/health');
}

export default {
    getHello,
    getHealth,
};
