import axios from 'axios';

// In production (Vercel), use the proxy route to avoid mixed content (HTTPS→HTTP) issues.
// In local dev, call the backend directly.
const isServer = typeof window === 'undefined';
const isDev = process.env.NODE_ENV === 'development';

let baseURL: string;
if (isDev) {
    // Local dev: call backend directly
    baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://18.216.16.213:8000';
} else if (isServer) {
    // Vercel server-side: call backend directly (no browser restriction)
    baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://18.216.16.213:8000';
} else {
    // Vercel client-side (browser): use proxy to avoid mixed content
    baseURL = '/api/proxy';
}

const api = axios.create({
    baseURL,
});

// Add interceptor for auth token if needed later
if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) {
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
}


export const getTrends = async (days: number) => {
    const response = await api.get(`/trends/?days=${days}`);
    return response.data;
};

export default api;
