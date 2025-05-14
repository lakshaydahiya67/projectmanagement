import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ClockIcon, 
  UserGroupIcon, 
  CheckCircleIcon, 
  ArrowRightIcon 
} from '@heroicons/react/24/outline';
import { format, parseISO } from 'date-fns';

const ProjectCard = ({ project }) => {
  // Function to format date
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return format(parseISO(dateString), 'MMM d, yyyy');
    } catch (error) {
      return 'Invalid date';
    }
  };
  
  // Get completion percentage
  const completionPercentage = project.stats?.completion_percentage || 0;
  
  // Activity level based on recent updates
  const getActivityLevel = () => {
    if (!project.stats?.recent_activity_count) return 'Low';
    const count = project.stats.recent_activity_count;
    if (count > 20) return 'High';
    if (count > 5) return 'Medium';
    return 'Low';
  };
  
  // Activity level to color mapping
  const activityColorClass = {
    'High': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    'Medium': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    'Low': 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
  };
  
  return (
    <Link 
      to={`/projects/${project.id}`}
      className="block bg-white dark:bg-gray-800 overflow-hidden shadow-md rounded-lg hover:shadow-lg transition-shadow duration-300"
    >
      {/* Project header with color indicator */}
      <div 
        className="h-2"
        style={{ backgroundColor: project.color || '#3B82F6' }}
      ></div>
      
      <div className="p-5">
        {/* Project name and privacy badge */}
        <div className="flex items-start justify-between">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white truncate">
            {project.name}
          </h3>
          {project.is_private && (
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
              Private
            </span>
          )}
        </div>
        
        {/* Description */}
        {project.description && (
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
            {project.description}
          </p>
        )}
        
        {/* Project stats */}
        <div className="mt-4">
          <div className="flex items-center text-sm text-gray-500 dark:text-gray-400 space-y-1 flex-col items-start">
            <div className="flex items-center">
              <UserGroupIcon className="h-4 w-4 mr-1" />
              <span>{project.stats?.member_count || 0} members</span>
            </div>
            
            <div className="flex items-center">
              <CheckCircleIcon className="h-4 w-4 mr-1" />
              <span>{project.stats?.completed_tasks || 0}/{project.stats?.total_tasks || 0} tasks completed</span>
            </div>
            
            <div className="flex items-center">
              <ClockIcon className="h-4 w-4 mr-1" />
              <span>Updated {formatDate(project.updated_at)}</span>
            </div>
          </div>
        </div>
        
        {/* Progress bar */}
        <div className="mt-4">
          <div className="flex items-center">
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Progress
            </span>
            <span className="ml-auto text-sm text-gray-500 dark:text-gray-400">
              {completionPercentage}%
            </span>
          </div>
          <div className="mt-1 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full"
              style={{ width: `${completionPercentage}%` }}
            ></div>
          </div>
        </div>
        
        {/* Footer with activity level and view link */}
        <div className="mt-4 flex items-center justify-between">
          <span
            className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${activityColorClass[getActivityLevel()]}`}
          >
            {getActivityLevel()} Activity
          </span>
          
          <span className="inline-flex items-center text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300">
            View Project <ArrowRightIcon className="ml-1 h-4 w-4" />
          </span>
        </div>
      </div>
    </Link>
  );
};

export default ProjectCard;
