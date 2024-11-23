// API endpoints and utilities
const API = {
    CONFIG: '/api/config',
    AUTH: '/api/auth',
    ROOT: '/api/root',
    UPLOAD: '/api/upload',
    SEARCH: '/api/search'
};

// API utilities
const apiUtils = {
    // Generic API call function
    async call(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || 'API call failed');
            }

            return data;
        } catch (error) {
            console.error(`API call failed: ${error.message}`);
            throw error;
        }
    },

    // Configuration API
    config: {
        async get() {
            return apiUtils.call(API.CONFIG);
        },

        async update(config) {
            return apiUtils.call(API.CONFIG, {
                method: 'POST',
                body: JSON.stringify(config)
            });
        }
    },

    // Authentication API
    auth: {
        async login(username, password) {
            return apiUtils.call(API.AUTH + '/login', {
                method: 'POST',
                body: JSON.stringify({ username, password })
            });
        },

        async logout() {
            return apiUtils.call(API.AUTH + '/logout', {
                method: 'POST'
            });
        },

        async verify() {
            return apiUtils.call(API.AUTH + '/verify');
        }
    }
};

export default apiUtils;
