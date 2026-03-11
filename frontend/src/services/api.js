import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Create axios instance with longer timeout for AI predictions
const api = axios.create({
  baseURL: API,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Create a separate instance for AI/Divination with longer timeout
const aiApi = axios.create({
  baseURL: API,
  timeout: 120000, // 2 minutes for AI predictions
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

// Predictions - using longer timeout
export const getAIPrediction = (data) => aiApi.post('/predict/ai', data);
export const getDivinationPrediction = (data) => aiApi.post('/predict/divination', data);

export default api;
