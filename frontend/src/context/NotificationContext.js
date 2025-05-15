import React, { createContext, useState, useEffect, useContext } from 'react';
import apiService from '../services/api';
import { useNotificationWebSocket } from '../hooks/useWebSocket';
import { AuthContext } from './AuthContext';

export const NotificationContext = createContext();

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const { user } = useContext(AuthContext);
  
  // Connect to notifications WebSocket using the hook that handles authentication and reconnection
  const { isConnected } = useNotificationWebSocket(
    (data) => {
      console.log('Received notification:', data);
      if (data.type === 'notification') {
        // Add new notification to the list
        setNotifications(prevNotifications => [data.notification, ...prevNotifications]);
        setUnreadCount(prevCount => prevCount + 1);
      }
    }
  );
  
  // Fetch notifications on mount
  useEffect(() => {
    const fetchNotifications = async () => {
      if (!user) {
        setLoading(false);
        return;
      }
      
      try {
        setLoading(true);
        const { data } = await apiService.notifications.getAll();
        setNotifications(data.results || data || []);
        updateUnreadCount(data.results || data || []);
      } catch (error) {
        console.error('Failed to fetch notifications:', error);
        // If the API fails, don't break the UI
        setNotifications([]);
        setUnreadCount(0);
      } finally {
        setLoading(false);
      }
    };
    
    fetchNotifications();
  }, [user]);
  
  // Update unread count
  const updateUnreadCount = (notificationsList) => {
    const unread = notificationsList.filter(notification => !notification.read).length;
    setUnreadCount(unread);
  };
  
  // Mark single notification as read
  const markAsRead = async (notificationId) => {
    try {
      await apiService.notifications.markAsRead(notificationId);
      
      // Update the local state
      setNotifications(prevNotifications => 
        prevNotifications.map(notification => 
          notification.id === notificationId 
            ? { ...notification, read: true } 
            : notification
        )
      );
      
      // Update unread count
      setUnreadCount(prevCount => Math.max(0, prevCount - 1));
      
      return true;
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
      
      // Continue with UI update even if API fails
      setNotifications(prevNotifications => 
        prevNotifications.map(notification => 
          notification.id === notificationId 
            ? { ...notification, read: true } 
            : notification
        )
      );
      
      setUnreadCount(prevCount => Math.max(0, prevCount - 1));
      
      return false;
    }
  };
  
  // Mark all notifications as read
  const markAllAsRead = async () => {
    try {
      await apiService.notifications.markAllAsRead();
      
      // Update local state
      setNotifications(prevNotifications => 
        prevNotifications.map(notification => ({ ...notification, read: true }))
      );
      
      // Reset unread count
      setUnreadCount(0);
      
      return true;
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
      
      // Continue with UI update even if API fails
      setNotifications(prevNotifications => 
        prevNotifications.map(notification => ({ ...notification, read: true }))
      );
      
      setUnreadCount(0);
      
      return false;
    }
  };
  
  return (
    <NotificationContext.Provider value={{
      notifications,
      unreadCount,
      loading,
      markAsRead,
      markAllAsRead,
      isConnected
    }}>
      {children}
    </NotificationContext.Provider>
  );
};
