// auth.js - Authentication management module
import api from './api.js';

class Auth {
    constructor() {
        this.token = localStorage.getItem('authToken');
        this.user = null;
    }

    // Check if user is authenticated
    async checkAuth() {
        if (!this.token) {
            return false;
        }

        try {
            const response = await api.get('/api/auth/verify');
            return response.success;
        } catch (error) {
            this.token = null;
            localStorage.removeItem('authToken');
            return false;
        }
    }

    // Login
    async login(username, password) {
        try {
            const token = btoa(`${username}:${password}`);
            const response = await api.post('/api/auth/login', { token });
            
            if (response.success) {
                this.token = token;
                localStorage.setItem('authToken', token);
                return true;
            }
            
            api.showMessage(response.message || 'Login failed', true);
            return false;
        } catch (error) {
            api.showMessage('Login failed: ' + error.message, true);
            return false;
        }
    }

    // Logout
    async logout() {
        try {
            await api.post('/api/auth/logout');
        } finally {
            this.token = null;
            localStorage.removeItem('authToken');
            window.location.href = '/login';
        }
    }

    // Get auth token
    getToken() {
        return this.token;
    }
}

export default new Auth();
