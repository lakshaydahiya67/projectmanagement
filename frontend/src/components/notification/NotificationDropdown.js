import React, { useContext } from 'react';
import { Link } from 'react-router-dom';
import { NotificationContext } from '../../context/NotificationContext';
import { 
  CheckCircleIcon, 
  ExclamationCircleIcon, 
  InformationCircleIcon, 
  BellIcon,
  XMarkIcon,
  CheckIcon
} from '@heroicons/react/24/outline';
import { formatDistanceToNow } from 'date-fns';

const NotificationDropdown = ({ onClose }) => {
  const { notifications, unreadCount, markAsRead, markAllAsRead, loading } = useContext(NotificationContext);
  
  const handleClickOutside = (e) => {
    // Close the dropdown if clicking outside
    if (!e.target.closest('.notification-dropdown')) {
      onClose();
    }
  };
  
  // Add click outside listener
  React.useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);
  
  // Get icon for notification type
  const getNotificationIcon = (type) => {
    switch (type) {
      case 'task_assigned':
      case 'task_completed':
      case 'mention':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'deadline_approaching':
      case 'task_overdue':
        return <ExclamationCircleIcon className="h-5 w-5 text-red-500" />;
      case 'comment':
      case 'project_invitation':
      case 'project_update':
        return <InformationCircleIcon className="h-5 w-5 text-blue-500" />;
      default:
        return <BellIcon className="h-5 w-5 text-gray-500" />;
    }
  };
  
  // Format the time of notification
  const formatNotificationTime = (timestamp) => {
    return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
  };
  
  // Get notification URL
  const getNotificationUrl = (notification) => {
    const { type, data } = notification;
    
    switch (type) {
      case 'task_assigned':
      case 'task_completed':
      case 'deadline_approaching':
      case 'task_overdue':
      case 'comment':
        return `/projects/${data.project_id}/boards/${data.board_id}/columns/${data.column_id}/tasks/${data.task_id}`;
      case 'project_invitation':
      case 'project_update':
        return `/projects/${data.project_id}`;
      case 'mention':
        if (data.task_id) {
          return `/projects/${data.project_id}/boards/${data.board_id}/columns/${data.column_id}/tasks/${data.task_id}`;
        }
        return `/projects/${data.project_id}`;
      default:
        return '#';
    }
  };
  
  // Handle notification click
  const handleNotificationClick = (notification) => {
    if (!notification.read) {
      markAsRead(notification.id);
    }
    onClose();
  };
  
  return (
    <div className="notification-dropdown origin-top-right absolute right-0 mt-2 w-96 rounded-md shadow-lg py-1 bg-white dark:bg-gray-800 ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Notifications
            {unreadCount > 0 && (
              <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                {unreadCount} new
              </span>
            )}
          </h3>
          <div className="flex space-x-2">
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-blue-700 dark:text-blue-300 bg-blue-100 dark:bg-blue-900 hover:bg-blue-200 dark:hover:bg-blue-800 focus:outline-none"
                title="Mark all as read"
              >
                <CheckIcon className="h-4 w-4 mr-1" />
                Mark all read
              </button>
            )}
            <button
              onClick={onClose}
              className="rounded-md text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 focus:outline-none"
              title="Close notifications"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
      
      <div className="max-h-96 overflow-y-auto">
        {loading ? (
          <div className="text-center py-6">
            <svg className="animate-spin h-6 w-6 mx-auto text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">Loading notifications...</p>
          </div>
        ) : notifications.length === 0 ? (
          <div className="text-center py-6">
            <BellIcon className="h-12 w-12 mx-auto text-gray-400 dark:text-gray-500" />
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">No notifications yet</p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-200 dark:divide-gray-700">
            {notifications.map((notification) => (
              <li
                key={notification.id}
                className={`${
                  !notification.read
                    ? 'bg-blue-50 dark:bg-blue-900 dark:bg-opacity-20'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                }`}
              >
                <Link
                  to={getNotificationUrl(notification)}
                  className="block px-4 py-3"
                  onClick={() => handleNotificationClick(notification)}
                >
                  <div className="flex items-start">
                    <div className="flex-shrink-0 mt-0.5">
                      {getNotificationIcon(notification.type)}
                    </div>
                    <div className="ml-3 flex-1">
                      <p className="text-sm text-gray-900 dark:text-white">{notification.message}</p>
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        {formatNotificationTime(notification.created_at)}
                      </p>
                    </div>
                    {!notification.read && (
                      <div className="ml-2 flex-shrink-0">
                        <span className="inline-block h-2 w-2 rounded-full bg-blue-500"></span>
                      </div>
                    )}
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
      
      <div className="p-2 border-t border-gray-200 dark:border-gray-700 text-center">
        <Link
          to="/notifications"
          className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
          onClick={onClose}
        >
          View all notifications
        </Link>
      </div>
    </div>
  );
};

export default NotificationDropdown;
