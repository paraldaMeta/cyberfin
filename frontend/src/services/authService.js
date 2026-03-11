import api from './api';

// 用户认证服务
export const authService = {
  // 用户注册
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },
  
  // 用户登录
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
  },
  
  // 获取用户资料
  getProfile: async (userId) => {
    const response = await api.get(`/user/${userId}`);
    return response.data;
  },
  
  // 获取用户命盘
  getUserBazi: async (userId) => {
    const response = await api.get(`/user/${userId}/bazi`);
    return response.data;
  },
  
  // 刷新用户命盘
  refreshBazi: async (userId) => {
    const response = await api.post(`/user/${userId}/bazi/refresh`);
    return response.data;
  },
};

// 八字命理服务
export const baziService = {
  // 获取省份列表
  getProvinces: async () => {
    const response = await api.get('/bazi/provinces');
    return response.data;
  },
  
  // 获取城市列表
  getCities: async (province) => {
    const response = await api.get(`/bazi/cities/${encodeURIComponent(province)}`);
    return response.data;
  },
  
  // 获取时辰选项
  getShichenOptions: async () => {
    const response = await api.get('/bazi/shichen');
    return response.data;
  },
  
  // 计算八字命盘（不需要注册）
  calculateBazi: async (data) => {
    const response = await api.post('/bazi/calculate', data);
    return response.data;
  },
};

// 本地用户状态管理
export const userStorage = {
  // 保存用户信息到本地
  setUser: (user) => {
    localStorage.setItem('user', JSON.stringify(user));
  },
  
  // 获取本地用户信息
  getUser: () => {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },
  
  // 清除用户信息
  clearUser: () => {
    localStorage.removeItem('user');
  },
  
  // 检查是否已登录
  isLoggedIn: () => {
    return !!localStorage.getItem('user');
  },
};
