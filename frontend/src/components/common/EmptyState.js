import React from 'react';

const EmptyState = ({ icon, title, description, action }) => {
  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg py-8 px-4 text-center">
      <div className="flex flex-col items-center">
        {icon && (
          <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-200">
            {icon}
          </div>
        )}
        
        <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
          {title}
        </h3>
        
        {description && (
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto">
            {description}
          </p>
        )}
        
        {action && (
          <div className="mt-4">
            <button
              type="button"
              onClick={action.onClick}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {action.label}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmptyState;
