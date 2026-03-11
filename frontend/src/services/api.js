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

// Prediction History
export const savePredictionHistory = (data) => api.post('/history/save', data);
export const getPredictionHistory = (params) => api.get('/history', { params });
export const deletePredictionHistory = (historyId) => api.delete(`/history/${historyId}`);

// Watchlist
export const getWatchlist = (clientId) => api.get(`/watchlist/${clientId}`);
export const addToWatchlist = (clientId, item) => api.post(`/watchlist/${clientId}`, item);
export const removeFromWatchlist = (clientId, symbol) => api.delete(`/watchlist/${clientId}/${encodeURIComponent(symbol)}`);
export const getWatchlistWithData = (clientId) => api.get(`/watchlist/${clientId}/data`);

export default api;
