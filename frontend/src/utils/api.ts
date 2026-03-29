import axios from 'axios';

const API_BASE = '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Interceptor para adicionar token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth
export const login = (email: string, password: string) =>
  api.post('/auth/login', { email, password });

export const register = (data: { email: string; password: string; full_name: string; organization_name: string }) =>
  api.post('/auth/register', data);

// Projects (paginated)
export const getProjects = (params?: Record<string, any>) =>
  api.get('/projects', { params });

export const getProject = (id: number) =>
  api.get(`/projects/${id}`);

export const createProject = (data: any) =>
  api.post('/projects', data);

// Ratings
export const getProjectRating = (projectId: number) =>
  api.get(`/projects/${projectId}/rating`);

// Fraud Alerts (paginated)
export const getFraudAlerts = (params?: Record<string, any>) =>
  api.get('/fraud-alerts', { params });

export const getFraudSummary = () =>
  api.get('/fraud-alerts/summary');

export const updateFraudAlert = (id: number, data: any) =>
  api.patch(`/fraud-alerts/${id}`, data);

// Portfolios
export const getPortfolios = () =>
  api.get('/portfolios');

export const getPortfolioDetail = (id: number, params?: Record<string, any>) =>
  api.get(`/portfolios/${id}`, { params });

export const createPortfolio = (data: any) =>
  api.post('/portfolios', data);

// Dashboard
export const getDashboardMetrics = () =>
  api.get('/dashboard/metrics');

export const getRiskMatrix = () =>
  api.get('/dashboard/risk-matrix');

export default api;
