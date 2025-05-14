import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { format, parseISO } from 'date-fns';
import {
  ChevronDownIcon,
  ChevronUpIcon,
  ArrowPathIcon,
  FunnelIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import activityLogService from '../../services/activityLogService';

const ActivityLogList = () => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [activityLogs, setActivityLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  
  // Pagination state
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Filter state
  const [filters, setFilters] = useState({
    action_type: '',
    user: '',
    entity_type: '',
    start_date: '',
    end_date: '',
    last_day: false,
    last_week: false,
    last_month: false,
  });
  
  useEffect(() => {
    fetchActivityLogs();
  }, [projectId, page, filters]);
  
  const fetchActivityLogs = async () => {
    try {
      setLoading(true);
      
      // Build filters object
      const activeFilters = {};
      Object.entries(filters).forEach(([key, value]) => {
        if (value) {
          activeFilters[key] = value;
        }
      });
      
      // Fetch logs
      let response;
      if (projectId) {
        response = await activityLogService.getProjectActivityLogs(projectId, activeFilters, page);
      } else {
        response = await activityLogService.getActivityLogs(activeFilters, page);
      }
      
      // Format logs for display
      const formattedLogs = response.results.map(log => activityLogService.formatActivityLog(log));
      
      setActivityLogs(formattedLogs);
      setTotalPages(Math.ceil(response.count / 10)); // Assuming 10 items per page
    } catch (err) {
      console.error('Error fetching activity logs:', err);
      setError('Failed to load activity logs');
    } finally {
      setLoading(false);
    }
  };
  
  const handleFilterChange = (name, value) => {
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
    setPage(1); // Reset to first page when filters change
  };
  
  const handleToggleFilters = () => {
    setShowFilters(!showFilters);
  };
  
  const clearFilters = () => {
    setFilters({
      action_type: '',
      user: '',
      entity_type: '',
      start_date: '',
      end_date: '',
      last_day: false,
      last_week: false,
      last_month: false,
    });
    setPage(1);
  };
  
  const getEntityTypeIcon = (entityType) => {
    // You can add more icons based on your entity types
    switch (entityType) {
      case 'task':
        return '📝';
      case 'project':
        return '📁';
      case 'comment':
        return '💬';
      case 'user':
        return '👤';
      case 'organization':
        return '🏢';
      case 'board':
        return '📊';
      case 'column':
        return '📋';
      case 'label':
        return '🏷️';
      default:
        return '📄';
    }
  };
  
  const getActionTypeColor = (actionType) => {
    switch (actionType) {
      case 'create':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'update':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'delete':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'comment':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      case 'assign':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'unassign':
        return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
      case 'move':
        return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200';
      case 'login':
        return 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-200';
      case 'logout':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };
  
  const formatDateTime = (dateTimeStr) => {
    if (!dateTimeStr) return 'Unknown';
    try {
      return format(parseISO(dateTimeStr), 'MMM d, yyyy h:mm a');
    } catch (e) {
      return dateTimeStr;
    }
  };
  
  const renderFilters = () => (
    <div className="bg-white dark:bg-gray-800 p-4 rounded-md shadow mb-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">Filters</h3>
        <button
          onClick={clearFilters}
          className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
        >
          Clear all
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Action Type Filter */}
        <div>
          <label htmlFor="action_type" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Action Type
          </label>
          <select
            id="action_type"
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 dark:bg-gray-700 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            value={filters.action_type}
            onChange={(e) => handleFilterChange('action_type', e.target.value)}
          >
            <option value="">All Actions</option>
            <option value="create">Create</option>
            <option value="update">Update</option>
            <option value="delete">Delete</option>
            <option value="comment">Comment</option>
            <option value="assign">Assign</option>
            <option value="unassign">Unassign</option>
            <option value="move">Move</option>
            <option value="login">Login</option>
            <option value="logout">Logout</option>
          </select>
        </div>
        
        {/* Entity Type Filter */}
        <div>
          <label htmlFor="entity_type" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Entity Type
          </label>
          <select
            id="entity_type"
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 dark:bg-gray-700 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            value={filters.entity_type}
            onChange={(e) => handleFilterChange('entity_type', e.target.value)}
          >
            <option value="">All Types</option>
            <option value="task">Task</option>
            <option value="project">Project</option>
            <option value="comment">Comment</option>
            <option value="user">User</option>
          </select>
        </div>
        
        {/* Time Period Shortcuts */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Time Period
          </label>
          <div className="flex flex-wrap gap-2">
            <button
              className={`px-3 py-1 text-xs rounded-full ${
                filters.last_day
                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                  : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
              }`}
              onClick={() => handleFilterChange('last_day', !filters.last_day)}
            >
              Last 24 Hours
            </button>
            <button
              className={`px-3 py-1 text-xs rounded-full ${
                filters.last_week
                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                  : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
              }`}
              onClick={() => handleFilterChange('last_week', !filters.last_week)}
            >
              Last 7 Days
            </button>
            <button
              className={`px-3 py-1 text-xs rounded-full ${
                filters.last_month
                  ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                  : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
              }`}
              onClick={() => handleFilterChange('last_month', !filters.last_month)}
            >
              Last 30 Days
            </button>
          </div>
        </div>
        
        {/* Date Range Filters */}
        <div>
          <label htmlFor="start_date" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Start Date
          </label>
          <input
            type="date"
            id="start_date"
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 dark:bg-gray-700 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            value={filters.start_date}
            onChange={(e) => handleFilterChange('start_date', e.target.value)}
          />
        </div>
        
        <div>
          <label htmlFor="end_date" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            End Date
          </label>
          <input
            type="date"
            id="end_date"
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 dark:border-gray-600 dark:bg-gray-700 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            value={filters.end_date}
            onChange={(e) => handleFilterChange('end_date', e.target.value)}
          />
        </div>
      </div>
    </div>
  );
  
  if (loading && activityLogs.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <ArrowPathIcon className="animate-spin h-8 w-8 text-blue-500" />
        <span className="ml-2 text-gray-600 dark:text-gray-300">Loading activity logs...</span>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900 p-4 rounded-md">
        <p className="text-red-800 dark:text-red-200">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
            Activity Log {projectId ? 'for Project' : ''}
          </h2>
          <div className="flex space-x-2">
            <button
              onClick={handleToggleFilters}
              className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <FunnelIcon className="h-4 w-4 mr-2" />
              Filters
              {showFilters ? (
                <ChevronUpIcon className="h-4 w-4 ml-1" />
              ) : (
                <ChevronDownIcon className="h-4 w-4 ml-1" />
              )}
            </button>
            <button
              onClick={fetchActivityLogs}
              className="inline-flex items-center px-3 py-2 border border-gray-300 dark:border-gray-600 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Refresh
            </button>
          </div>
        </div>
        
        {showFilters && renderFilters()}
        
        {activityLogs.length === 0 ? (
          <div className="text-center py-6">
            <p className="text-gray-500 dark:text-gray-400">No activity logs found.</p>
          </div>
        ) : (
          <>
            <div className="mt-2">
              <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                {activityLogs.map((log) => (
                  <li key={log.id} className="py-4">
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0 text-2xl">
                        {log.icon}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {log.user ? `${log.user.first_name} ${log.user.last_name}` : 'System'} 
                            <span className="mx-1 font-normal text-gray-500 dark:text-gray-400">
                              {log.description || `${log.action_type_display} a ${log.content_type_display}`}
                            </span>
                          </p>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getActionTypeColor(log.action_type)}`}>
                            {log.action_type_display}
                          </span>
                        </div>
                        <div className="mt-1 flex items-center text-sm text-gray-500 dark:text-gray-400">
                          <span>{formatDateTime(log.timestamp)}</span>
                          {log.details && Object.keys(log.details).length > 0 && (
                            <div className="ml-2 overflow-hidden text-xs">
                              {Object.entries(log.details).map(([key, value]) => (
                                key !== 'description' && (
                                  <span key={key} className="mx-1">
                                    <span className="font-medium">{key.replace('_', ' ')}:</span> {value.toString()}
                                  </span>
                                )
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-4">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className={`px-3 py-1 rounded-md text-sm ${
                    page === 1
                      ? 'bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-500 cursor-not-allowed'
                      : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'
                  }`}
                >
                  Previous
                </button>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className={`px-3 py-1 rounded-md text-sm ${
                    page === totalPages
                      ? 'bg-gray-100 text-gray-400 dark:bg-gray-800 dark:text-gray-500 cursor-not-allowed'
                      : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600'
                  }`}
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default ActivityLogList; 