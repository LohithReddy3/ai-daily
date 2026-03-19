import axios from 'axios';

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000',
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
