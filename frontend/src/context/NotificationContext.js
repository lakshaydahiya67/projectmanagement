import React, { createContext, useState, useEffect, useContext } from 'react';
import apiService from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import { AuthContext } from './AuthContext';

export const NotificationContext = createContext();

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const { user } = useContext(AuthContext);
  
  // Connect to notifications WebSocket
  const { lastMessage } = useWebSocket(
    user ? `/ws/notifications/${user.id}/` : null,
    {
      onOpen: () => console.log('Notifications WebSocket connected'),
      onClose: () => console.log('Notifications WebSocket disconnected'),
      onError: (e) => console.error('Notifications WebSocket error:', e),
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
        setNotifications(data.results || []);
        updateUnreadCount(data.results || []);
      } catch (error) {
        console.error('Failed to fetch notifications:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchNotifications();
  }, [user]);
  
  // Handle incoming WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        const data = JSON.parse(lastMessage.data);
        
        if (data.type === 'notification') {
          // Add new notification to the list
          setNotifications(prevNotifications => [data.notification, ...prevNotifications]);
          setUnreadCount(prevCount => prevCount + 1);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    }
  }, [lastMessage]);
  
  // Update unread count
  const updateUnreadCount = (notificationsList) => {
    const unread = notificationsList.filter(notification => !notification.read).length;
    setUnreadCount(unread);
  };
  
  // Mark a notification as read
  const markAsRead = async (notificationId) => {
    try {
      await apiService.notifications.markAsRead(notificationId);
      
      setNotifications(notifications.map(notification => 
        notification.id === notificationId
          ? { ...notification, read: true }
          : notification
      ));
      
      setUnreadCount(prevCount => Math.max(0, prevCount - 1));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };
  
  // Mark all notifications as read
  const markAllAsRead = async () => {
    try {
      await apiService.notifications.markAllAsRead();
      
      setNotifications(notifications.map(notification => ({
        ...notification,
        read: true
      })));
      
      setUnreadCount(0);
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  };
  
  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        loading,
        markAsRead,
        markAllAsRead
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};
