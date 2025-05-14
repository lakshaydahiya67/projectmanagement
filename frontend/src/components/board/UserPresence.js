import React from 'react';
import { UserCircleIcon } from '@heroicons/react/24/solid';

const UserPresence = ({ viewers = [] }) => {
  if (!viewers || viewers.length === 0) {
    return null;
  }

  return (
    <div className="flex items-center">
      <span className="text-sm text-gray-500 dark:text-gray-400 mr-2">
        {viewers.length} {viewers.length === 1 ? 'person' : 'people'} viewing
      </span>
      
      <div className="flex -space-x-2 overflow-hidden">
        {viewers.slice(0, 5).map(viewer => (
          <div 
            key={viewer.id} 
            className="relative"
            title={viewer.full_name || viewer.username}
          >
            {viewer.avatar ? (
              <img
                className="h-6 w-6 rounded-full border-2 border-white dark:border-gray-800"
                src={viewer.avatar}
                alt={viewer.full_name || viewer.username}
              />
            ) : (
              <div className="h-6 w-6 rounded-full bg-gray-200 dark:bg-gray-700 border-2 border-white dark:border-gray-800 flex items-center justify-center">
                <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                  {(viewer.full_name || viewer.username)?.charAt(0).toUpperCase()}
                </span>
              </div>
            )}
            <span className="absolute bottom-0 right-0 block h-2 w-2 rounded-full bg-green-400 ring-1 ring-white dark:ring-gray-800" />
          </div>
        ))}
        
        {viewers.length > 5 && (
          <div className="h-6 w-6 rounded-full bg-gray-200 dark:bg-gray-700 border-2 border-white dark:border-gray-800 flex items-center justify-center">
            <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
              +{viewers.length - 5}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserPresence;
