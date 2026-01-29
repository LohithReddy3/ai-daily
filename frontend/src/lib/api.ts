import axios from 'axios';

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
});

// Add interceptor for auth token if needed later
if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
}

export default api;
