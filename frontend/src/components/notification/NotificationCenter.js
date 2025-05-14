import React, { useState, useEffect } from 'react';
import { useNotificationWebSocket } from '../../hooks/useWebSocket';
import apiService from '../../services/api';
import { BellIcon, CheckIcon } from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import { Link } from 'react-router-dom';

const NotificationCenter = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);

  // Handle WebSocket messages for notifications
  const handleWebSocketMessage = (data) => {
    if (data.type === 'notification') {
      // Add the new notification to the list
      setNotifications(prev => [data.notification, ...prev]);
      setUnreadCount(prev => prev + 1);
    }
  };

  // Initialize WebSocket connection
  const { isConnected } = useNotificationWebSocket(handleWebSocketMessage);

  // Fetch notifications
  useEffect(() => {
    const fetchNotifications = async () => {
      try {
        setLoading(true);
        const { data } = await apiService.notifications.getAll();
        setNotifications(data);
        setUnreadCount(data.filter(notification => !notification.is_read).length);
      } catch (err) {
        console.error('Error fetching notifications:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchNotifications();
  }, []);

  // Mark notification as read
  const handleMarkAsRead = async (notificationId) => {
    try {
      await apiService.notifications.markAsRead(notificationId);
      
      // Update local state
      setNotifications(prev => 
        prev.map(notification => 
          notification.id === notificationId 
            ? { ...notification, is_read: true } 
            : notification
        )
      );
      
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('Error marking notification as read:', err);
    }
  };

  // Mark all notifications as read
  const handleMarkAllAsRead = async () => {
    try {
      await apiService.notifications.markAllAsRead();
      
      // Update local state
      setNotifications(prev => 
        prev.map(notification => ({ ...notification, is_read: true }))
      );
      
      setUnreadCount(0);
    } catch (err) {
      console.error('Error marking all notifications as read:', err);
    }
  };

  // Render notification content based on type
  const renderNotificationContent = (notification) => {
    switch (notification.notification_type) {
      case 'task_assigned':
        return (
          <Link 
            to={`/projects/${notification.content_object?.column?.board?.project?.id}/boards/${notification.content_object?.column?.board?.id}/tasks/${notification.content_object?.id}`}
            className="block hover:bg-gray-50 dark:hover:bg-gray-800"
            onClick={() => handleMarkAsRead(notification.id)}
          >
            <div className="px-4 py-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {notification.title}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {notification.message}
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                {format(new Date(notification.created_at), 'MMM d, h:mm a')}
              </p>
            </div>
          </Link>
        );
        
      case 'comment_added':
        return (
          <Link 
            to={`/projects/${notification.content_object?.column?.board?.project?.id}/boards/${notification.content_object?.column?.board?.id}/tasks/${notification.content_object?.id}`}
            className="block hover:bg-gray-50 dark:hover:bg-gray-800"
            onClick={() => handleMarkAsRead(notification.id)}
          >
            <div className="px-4 py-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {notification.title}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {notification.message}
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                {format(new Date(notification.created_at), 'MMM d, h:mm a')}
              </p>
            </div>
          </Link>
        );
        
      case 'deadline_approaching':
      case 'deadline_missed':
        return (
          <Link 
            to={`/projects/${notification.content_object?.column?.board?.project?.id}/boards/${notification.content_object?.column?.board?.id}/tasks/${notification.content_object?.id}`}
            className="block hover:bg-gray-50 dark:hover:bg-gray-800"
            onClick={() => handleMarkAsRead(notification.id)}
          >
            <div className="px-4 py-3">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {notification.title}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {notification.message}
              </p>
              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                {format(new Date(notification.created_at), 'MMM d, h:mm a')}
              </p>
            </div>
          </Link>
        );
        
      default:
        return (
          <div className="px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800">
            <p className="text-sm font-medium text-gray-900 dark:text-white">
              {notification.title}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {notification.message}
            </p>
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
              {format(new Date(notification.created_at), 'MMM d, h:mm a')}
            </p>
          </div>
        );
    }
  };

  return (
    <div className="relative">
      {/* Notification Bell */}
      <button
        type="button"
        className="relative p-1 text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-white focus:outline-none focus:text-gray-800 dark:focus:text-white"
        onClick={() => setIsOpen(!isOpen)}
      >
        <BellIcon className="h-6 w-6" />
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 -mt-1 -mr-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-medium text-white">
            {unreadCount}
          </span>
        )}
      </button>
      
      {/* Notification Dropdown */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 rounded-md shadow-lg bg-white dark:bg-gray-900 ring-1 ring-black ring-opacity-5 divide-y divide-gray-100 dark:divide-gray-800 focus:outline-none z-50">
          <div className="px-4 py-3 flex justify-between items-center">
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
              Notifications
            </h3>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllAsRead}
                className="flex items-center text-sm text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
              >
                <CheckIcon className="h-4 w-4 mr-1" />
                Mark all as read
              </button>
            )}
          </div>
          
          <div className="max-h-96 overflow-y-auto">
            {loading ? (
              <div className="px-4 py-3 text-center text-gray-500 dark:text-gray-400">
                Loading notifications...
              </div>
            ) : notifications.length === 0 ? (
              <div className="px-4 py-3 text-center text-gray-500 dark:text-gray-400">
                No notifications
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-800">
                {notifications.map(notification => (
                  <div 
                    key={notification.id} 
                    className={`${!notification.is_read ? 'bg-blue-50 dark:bg-blue-900/20' : ''}`}
                  >
                    {renderNotificationContent(notification)}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationCenter;
