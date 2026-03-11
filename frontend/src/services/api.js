import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Create axios instance
const api = axios.create({
  baseURL: API,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Markets
export const getMarkets = () => api.get('/markets');
export const getMarketStocks = (marketType) => api.get(`/market/${marketType}`);
export const getMarketOverview = () => api.get('/overview');

// Stock
export const getStockDetail = (symbol) => api.get(`/stock/${encodeURIComponent(symbol)}`);
export const searchStocks = (query) => api.get(`/search?q=${encodeURIComponent(query)}`);

// Predictions
export const getAIPrediction = (data) => api.post('/predict/ai', data);
export const getDivinationPrediction = (data) => api.post('/predict/divination', data);

export default api;
