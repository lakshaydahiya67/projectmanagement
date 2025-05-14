import axios from 'axios';

// Create axios instance with base URL
const api = axios.create({
  baseURL: '/api'
});

// Request interceptor for adding auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If error is 401 and we haven't already tried to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('No refresh token');
        
        const response = await axios.post('/api/auth/token/refresh/', {
          refresh: refreshToken
        });
        
        localStorage.setItem('access_token', response.data.access);
        
        // Update the auth header
        originalRequest.headers['Authorization'] = `Bearer ${response.data.access}`;
        
        // Retry the original request
        return axios(originalRequest);
      } catch (refreshError) {
        // If refresh fails, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// API service functions
const apiService = {
  // Auth endpoints
  auth: {
    login: (email, password) => api.post('/auth/token/', { email, password }),
    register: (userData) => api.post('/auth/users/', userData),
    refreshToken: (refreshToken) => api.post('/auth/token/refresh/', { refresh: refreshToken }),
    resetPassword: (email) => api.post('/auth/users/reset_password/', { email }),
    confirmReset: (data) => api.post('/auth/users/reset_password_confirm/', data)
  },
  
  // Organizations
  organizations: {
    getAll: () => api.get('/organizations/'),
    getById: (id) => api.get(`/organizations/${id}/`),
    create: (data) => api.post('/organizations/', data),
    update: (id, data) => api.patch(`/organizations/${id}/`, data),
    delete: (id) => api.delete(`/organizations/${id}/`),
    getMembers: (id) => api.get(`/organizations/${id}/members/`)
  },
  
  // Projects
  projects: {
    getAll: () => api.get('/projects/'),
    getByOrganization: (orgId) => api.get(`/organizations/${orgId}/projects/`),
    getById: (id) => api.get(`/projects/${id}/`),
    create: (orgId, data) => api.post(`/organizations/${orgId}/projects/`, data),
    update: (id, data) => api.patch(`/projects/${id}/`, data),
    delete: (id) => api.delete(`/projects/${id}/`),
    getMembers: (id) => api.get(`/projects/${id}/members/`),
    addMember: (id, data) => api.post(`/projects/${id}/members/`, data)
  },
  
  // Boards
  boards: {
    getAll: (projectId) => api.get(`/projects/${projectId}/boards/`),
    getById: (projectId, boardId) => api.get(`/projects/${projectId}/boards/${boardId}/`),
    create: (projectId, data) => api.post(`/projects/${projectId}/boards/`, data),
    update: (projectId, boardId, data) => api.patch(`/projects/${projectId}/boards/${boardId}/`, data),
    delete: (projectId, boardId) => api.delete(`/projects/${projectId}/boards/${boardId}/`),
    getColumns: (projectId, boardId) => api.get(`/projects/${projectId}/boards/${boardId}/columns/`)
  },
  
  // Columns
  columns: {
    getAll: (projectId, boardId) => api.get(`/projects/${projectId}/boards/${boardId}/columns/`),
    getById: (projectId, boardId, columnId) => api.get(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/`),
    create: (projectId, boardId, data) => api.post(`/projects/${projectId}/boards/${boardId}/columns/`, data),
    update: (projectId, boardId, columnId, data) => api.patch(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/`, data),
    delete: (projectId, boardId, columnId) => api.delete(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/`),
  },
  
  // Tasks
  tasks: {
    getByColumn: (projectId, boardId, columnId) => api.get(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/`),
    getById: (projectId, boardId, columnId, taskId) => api.get(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/${taskId}/`),
    create: (projectId, boardId, columnId, data) => api.post(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/`, data),
    update: (projectId, boardId, columnId, taskId, data) => api.patch(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/${taskId}/`, data),
    delete: (projectId, boardId, columnId, taskId) => api.delete(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/${taskId}/`),
    move: (projectId, boardId, columnId, taskId, data) => api.post(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/${taskId}/move/`, data),
    addLabels: (projectId, boardId, columnId, taskId, data) => api.post(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/${taskId}/add_labels/`, data),
    removeLabels: (projectId, boardId, columnId, taskId, data) => api.post(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/${taskId}/remove_labels/`, data),
    assign: (projectId, boardId, columnId, taskId, data) => api.post(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/${taskId}/assign/`, data),
    filter: (projectId, boardId, columnId, data) => api.post(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/filter_tasks/`, data)
  },
  
  // Comments
  comments: {
    getByTask: (projectId, boardId, columnId, taskId) => api.get(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/${taskId}/comments/`),
    create: (projectId, boardId, columnId, taskId, data) => api.post(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/${taskId}/comments/`, data),
    update: (projectId, boardId, columnId, taskId, commentId, data) => api.patch(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/${taskId}/comments/${commentId}/`, data),
    delete: (projectId, boardId, columnId, taskId, commentId) => api.delete(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/${taskId}/comments/${commentId}/`)
  },
  
  // Labels
  labels: {
    getByProject: (projectId) => api.get(`/projects/${projectId}/labels/`),
    create: (projectId, data) => api.post(`/projects/${projectId}/labels/`, data),
    update: (projectId, labelId, data) => api.patch(`/projects/${projectId}/labels/${labelId}/`, data),
    delete: (projectId, labelId) => api.delete(`/projects/${projectId}/labels/${labelId}/`)
  },
  
  // Attachments
  attachments: {
    getByTask: (projectId, boardId, columnId, taskId) => api.get(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/${taskId}/attachments/`),
    upload: (projectId, boardId, columnId, taskId, formData) => api.post(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/${taskId}/attachments/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),
    delete: (projectId, boardId, columnId, taskId, attachmentId) => api.delete(`/projects/${projectId}/boards/${boardId}/columns/${columnId}/tasks/${taskId}/attachments/${attachmentId}/`)
  },
  
  // Notifications
  notifications: {
    getAll: () => api.get('/notifications/'),
    markAsRead: (id) => api.post(`/notifications/${id}/mark_read/`),
    markAllAsRead: () => api.post('/notifications/mark_all_read/')
  },
  
  // Analytics
  analytics: {
    getProjectMetrics: (projectId) => api.get(`/analytics/projects/${projectId}/metrics/summary/`),
    getTaskDistribution: (projectId) => api.get(`/analytics/projects/${projectId}/metrics/task-distribution/`),
    getBurndownData: (projectId) => api.get(`/analytics/projects/${projectId}/metrics/burndown/`),
    getUserProductivity: (projectId) => api.get(`/analytics/projects/${projectId}/productivity/rankings/`),
    getActivityLog: (projectId, params) => api.get(`/analytics/projects/${projectId}/activities/`, { params })
  }
};

export default apiService;
