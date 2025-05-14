import React from 'react';
import { Link } from 'react-router-dom';
import { CalendarIcon, ChatBubbleLeftRightIcon, PaperClipIcon, UserCircleIcon } from '@heroicons/react/24/outline';
import { format } from 'date-fns';

const Task = ({ task, provided, isDragging, projectId, boardId, columnId }) => {
  const taskUrl = `/projects/${projectId}/boards/${boardId}/tasks/${task.id}`;
  const formattedDate = task.due_date ? format(new Date(task.due_date), 'MMM d') : null;
  const isOverdue = task.due_date && new Date(task.due_date) < new Date();
  
  // Priority colors
  const priorityColors = {
    low: 'bg-blue-100 text-blue-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-orange-100 text-orange-800',
    urgent: 'bg-red-100 text-red-800'
  };

  return (
    <div
      ref={provided.innerRef}
      {...provided.draggableProps}
      {...provided.dragHandleProps}
      className={`p-3 mb-2 bg-white dark:bg-gray-700 rounded-lg shadow-sm 
        ${isDragging ? 'shadow-lg' : ''} 
        border-l-4 ${task.priority ? `border-${task.priority === 'urgent' ? 'red' : task.priority === 'high' ? 'orange' : task.priority === 'medium' ? 'yellow' : 'blue'}-500` : 'border-gray-300'}`}
    >
      <Link to={taskUrl} className="block">
        <h3 className="font-medium text-gray-900 dark:text-white mb-2">{task.title}</h3>
        
        {task.description && (
          <p className="text-sm text-gray-500 dark:text-gray-300 mb-3 line-clamp-2">
            {task.description.replace(/#{1,6}|\*\*|\*|~~|`|>|---|___|\[|\]|\(|\)/g, '')}
          </p>
        )}
        
        {task.labels && task.labels.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {task.labels.map(label => (
              <span
                key={label.id}
                className="px-2 py-0.5 text-xs rounded-full"
                style={{ backgroundColor: label.color + '33', color: label.color }}
              >
                {label.name}
              </span>
            ))}
          </div>
        )}
        
        <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
          {task.priority && (
            <span className={`px-2 py-1 text-xs rounded-full ${priorityColors[task.priority]}`}>
              {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}
            </span>
          )}
          
          <div className="flex items-center space-x-2">
            {formattedDate && (
              <div className={`flex items-center ${isOverdue ? 'text-red-500 dark:text-red-400' : ''}`}>
                <CalendarIcon className="h-4 w-4 mr-1" />
                <span>{formattedDate}</span>
              </div>
            )}
            
            {task.attachments && task.attachments.length > 0 && (
              <div className="flex items-center">
                <PaperClipIcon className="h-4 w-4 mr-1" />
                <span>{task.attachments.length}</span>
              </div>
            )}
            
            {task.comments_count > 0 && (
              <div className="flex items-center">
                <ChatBubbleLeftRightIcon className="h-4 w-4 mr-1" />
                <span>{task.comments_count}</span>
              </div>
            )}
          </div>
        </div>
        
        {task.assignees && task.assignees.length > 0 && (
          <div className="mt-3 flex -space-x-2 overflow-hidden">
            {task.assignees.slice(0, 3).map(user => (
              <div key={user.id} className="inline-block h-6 w-6">
                {user.avatar ? (
                  <img
                    className="h-6 w-6 rounded-full ring-2 ring-white dark:ring-gray-800"
                    src={user.avatar}
                    alt={user.full_name || user.username}
                  />
                ) : (
                  <UserCircleIcon className="h-6 w-6 text-gray-500 bg-gray-200 dark:bg-gray-600 rounded-full" />
                )}
              </div>
            ))}
            
            {task.assignees.length > 3 && (
              <span className="flex items-center justify-center h-6 w-6 rounded-full bg-gray-200 dark:bg-gray-600 text-xs font-medium text-gray-500 dark:text-gray-300 ring-2 ring-white dark:ring-gray-800">
                +{task.assignees.length - 3}
              </span>
            )}
          </div>
        )}
      </Link>
    </div>
  );
};

export default Task;
