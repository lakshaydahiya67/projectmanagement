import React, { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import apiService from '../../services/api';
import LabelSelector from '../task/LabelSelector';
import UserSelector from '../task/UserSelector';
import DueDatePicker from '../task/DueDatePicker';

const TaskFormModal = ({ isOpen, onClose, projectId, boardId, columnId, initialOrder, taskId = null }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [task, setTask] = useState({
    title: '',
    description: '',
    priority: 'medium',
    due_date: null,
    column: columnId,
    order: initialOrder,
    labels: [],
    assignees: []
  });

  // Get task details for editing if taskId exists
  useEffect(() => {
    const fetchTask = async () => {
      if (!taskId) return;
      
      try {
        setLoading(true);
        const { data } = await apiService.tasks.getById(projectId, boardId, columnId, taskId);
        setTask({
          title: data.title,
          description: data.description || '',
          priority: data.priority || 'medium',
          due_date: data.due_date || null,
          column: data.column,
          order: data.order,
          labels: data.labels || [],
          assignees: data.assignees || []
        });
        setLoading(false);
      } catch (err) {
        console.error('Error fetching task:', err);
        setError('Failed to load task details');
        setLoading(false);
      }
    };
    
    fetchTask();
  }, [projectId, boardId, columnId, taskId]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setTask(prev => ({ ...prev, [name]: value }));
  };

  const handlePriorityChange = (priority) => {
    setTask(prev => ({ ...prev, priority }));
  };

  const handleLabelsChange = (selectedLabels) => {
    setTask(prev => ({ ...prev, labels: selectedLabels }));
  };

  const handleAssigneesChange = (selectedUsers) => {
    setTask(prev => ({ ...prev, assignees: selectedUsers }));
  };

  const handleDueDateChange = (date) => {
    setTask(prev => ({ ...prev, due_date: date }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!task.title.trim()) {
      setError('Title is required');
      return;
    }
    
    try {
      setLoading(true);
      
      const payload = {
        title: task.title.trim(),
        description: task.description.trim() || null,
        priority: task.priority,
        due_date: task.due_date,
        column: columnId,
        order: initialOrder,
        label_ids: task.labels.map(label => label.id),
        assignee_ids: task.assignees.map(user => user.id)
      };
      
      if (taskId) {
        // Update existing task
        await apiService.tasks.update(projectId, boardId, columnId, taskId, payload);
      } else {
        // Create new task
        await apiService.tasks.create(projectId, boardId, columnId, payload);
      }
      
      setLoading(false);
      onClose();
    } catch (err) {
      console.error('Error saving task:', err);
      setError('Failed to save task');
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/40" aria-hidden="true" />
      
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <Dialog.Panel className="w-full max-w-md bg-white dark:bg-gray-800 rounded-lg shadow-xl">
          <div className="flex justify-between items-center border-b border-gray-200 dark:border-gray-700 p-4">
            <Dialog.Title className="text-lg font-medium text-gray-900 dark:text-gray-100">
              {taskId ? 'Edit Task' : 'Add New Task'}
            </Dialog.Title>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
          
          <form onSubmit={handleSubmit} className="p-4 space-y-4">
            {error && (
              <div className="text-sm text-red-500 p-2 bg-red-50 dark:bg-red-900/20 rounded">
                {error}
              </div>
            )}
            
            <div>
              <label htmlFor="title" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Title*
              </label>
              <input
                id="title"
                name="title"
                type="text"
                value={task.title}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 
                  focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Task title"
              />
            </div>
            
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Description
              </label>
              <textarea
                id="description"
                name="description"
                rows={3}
                value={task.description}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 
                  focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                placeholder="Task description (supports Markdown)"
              />
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                Supports markdown formatting
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Priority
              </label>
              <div className="flex space-x-2">
                {['low', 'medium', 'high', 'urgent'].map((priority) => (
                  <button
                    key={priority}
                    type="button"
                    onClick={() => handlePriorityChange(priority)}
                    className={`px-3 py-1 rounded-md text-sm font-medium capitalize
                      ${task.priority === priority 
                        ? 'ring-2 ring-offset-2 ring-blue-500 ' + 
                          (priority === 'low' ? 'bg-blue-100 text-blue-800' : 
                           priority === 'medium' ? 'bg-yellow-100 text-yellow-800' : 
                           priority === 'high' ? 'bg-orange-100 text-orange-800' : 
                           'bg-red-100 text-red-800')
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300'
                      }`}
                  >
                    {priority}
                  </button>
                ))}
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Due Date
              </label>
              <DueDatePicker 
                selectedDate={task.due_date} 
                onChange={handleDueDateChange} 
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Labels
              </label>
              <LabelSelector
                projectId={projectId}
                selectedLabels={task.labels}
                onChange={handleLabelsChange}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Assignees
              </label>
              <UserSelector
                projectId={projectId}
                selectedUsers={task.assignees}
                onChange={handleAssigneesChange}
              />
            </div>
            
            <div className="flex justify-end mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
              <button
                type="button"
                onClick={onClose}
                className="mr-2 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 
                  dark:hover:bg-gray-700 rounded-md"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 
                  rounded-md shadow-sm disabled:bg-blue-400 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing
                  </span>
                ) : (
                  taskId ? 'Update Task' : 'Create Task'
                )}
              </button>
            </div>
          </form>
        </Dialog.Panel>
      </div>
    </Dialog>
  );
};

export default TaskFormModal;
