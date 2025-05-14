import axios from 'axios';

const API_URL = '/api/analytics';

/**
 * Service for interacting with activity logs API
 */
const activityLogService = {
  /**
   * Get activity logs with optional filters
   * @param {Object} filters - Filter parameters
   * @param {number} page - Page number
   * @returns {Promise<Object>} Activity logs response with results and pagination info
   */
  getActivityLogs: async (filters = {}, page = 1) => {
    const params = new URLSearchParams();
    params.append('page', page);
    
    // Add all filters to the params
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, value);
      }
    });
    
    const response = await axios.get(`${API_URL}/activity-logs/?${params.toString()}`);
    return response.data;
  },
  
  /**
   * Get project-specific activity logs
   * @param {string} projectId - UUID of the project
   * @param {Object} filters - Filter parameters
   * @param {number} page - Page number 
   * @returns {Promise<Object>} Activity logs for the project
   */
  getProjectActivityLogs: async (projectId, filters = {}, page = 1) => {
    const params = new URLSearchParams();
    params.append('page', page);
    params.append('project', projectId);
    
    // Add all filters to the params
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, value);
      }
    });
    
    const response = await axios.get(`${API_URL}/projects/${projectId}/activities/?${params.toString()}`);
    return response.data;
  },
  
  /**
   * Parse and format activity log data for display
   * @param {Object} log - Activity log item
   * @returns {Object} Formatted activity log
   */
  formatActivityLog: (log) => {
    // Determine the appropriate icon
    let icon = '📄';
    if (log.entity_type_display) {
      const entityType = log.entity_type_display.toLowerCase();
      if (entityType.includes('task')) icon = '📝';
      else if (entityType.includes('project')) icon = '📁';
      else if (entityType.includes('comment')) icon = '💬';
      else if (entityType.includes('user')) icon = '👤';
    }
    
    // Format description if not provided
    const description = log.details?.description || 
      `${log.action_type_display} a ${log.entity_type_display}`;
    
    return {
      ...log,
      icon,
      formattedDescription: description,
    };
  }
};

export default activityLogService; 