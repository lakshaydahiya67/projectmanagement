import React, { useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import './App.css';
import axios from 'axios';
import { AuthProvider } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { NotificationProvider } from './context/NotificationContext';
import { AuthContext } from './context/AuthContext';
import Header from './components/layout/Header';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import ProjectDashboard from './components/dashboard/ProjectDashboard';
import BoardView from './components/board/BoardView';
import TaskDetail from './components/task/TaskDetail';
import AnalyticsDashboard from './components/analytics/AnalyticsDashboard';
import ActivityLogsPage from './components/activitylogs/ActivityLogsPage';

// Configure axios defaults
axios.defaults.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
axios.defaults.withCredentials = true; // For handling CSRF tokens

// Add axios interceptor for JWT token refresh
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If error is 401 and we haven't tried to refresh the token yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Try to refresh the token
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) throw new Error('No refresh token');
        
        const response = await axios.post('/auth/token/refresh/', { refresh: refreshToken });
        localStorage.setItem('access_token', response.data.access);
        
        // Update the original request with the new token
        originalRequest.headers['Authorization'] = `Bearer ${response.data.access}`;
        return axios(originalRequest);
      } catch (err) {
        // If refresh fails, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(error);
      }
    }
    
    return Promise.reject(error);
  }
);

// Add axios interceptor to include JWT token in requests
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useContext(AuthContext);
  const location = useLocation();
  
  if (loading) {
    return <div className="flex items-center justify-center h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  
  return children;
};

// Main Layout with Header
const MainLayout = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900">
      <Header />
      <main className="pt-16">
        {children}
      </main>
    </div>
  );
};

function AppContent() {
  return (
    <Routes>
      {/* Auth Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      {/* Protected Routes */}
      <Route path="/" element={
        <ProtectedRoute>
          <MainLayout>
            <Navigate to="/dashboard" replace />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <MainLayout>
            <ProjectDashboard />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/projects/:projectId" element={
        <ProtectedRoute>
          <MainLayout>
            <ProjectDashboard />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/projects/:projectId/boards/:boardId" element={
        <ProtectedRoute>
          <MainLayout>
            <BoardView />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/projects/:projectId/boards/:boardId/tasks/:taskId" element={
        <ProtectedRoute>
          <MainLayout>
            <TaskDetail />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/analytics" element={
        <ProtectedRoute>
          <MainLayout>
            <AnalyticsDashboard />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/analytics/:projectId" element={
        <ProtectedRoute>
          <MainLayout>
            <AnalyticsDashboard />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/activity-logs" element={
        <ProtectedRoute>
          <MainLayout>
            <ActivityLogsPage />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/projects/:projectId/activity" element={
        <ProtectedRoute>
          <MainLayout>
            <ActivityLogsPage />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      {/* Catch-all route */}
      <Route path="*" element={
        <MainLayout>
          <div className="flex items-center justify-center h-screen">
            <div className="text-center">
              <h1 className="text-4xl font-bold text-gray-800 dark:text-white">404</h1>
              <p className="text-lg text-gray-600 dark:text-gray-300">Page not found</p>
              <button 
                onClick={() => window.location.href = '/dashboard'} 
                className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Return to Dashboard
              </button>
            </div>
          </div>
        </MainLayout>
      } />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <ThemeProvider>
        <AuthProvider>
          <NotificationProvider>
            <AppContent />
          </NotificationProvider>
        </AuthProvider>
      </ThemeProvider>
    </Router>
  );
}

export default App;
