import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { marked } from 'marked';
import apiService from '../../services/api';
import { 
  PencilSquareIcon, TrashIcon, PaperClipIcon, 
  ChatBubbleLeftRightIcon, TagIcon, UserCircleIcon,
  CalendarIcon, ArrowUturnLeftIcon
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import CommentList from './CommentList';
import LabelSelector from './LabelSelector';
import UserSelector from './UserSelector';
import DueDatePicker from './DueDatePicker';

const TaskDetail = () => {
  const { projectId, boardId, columnId, taskId } = useParams();
  const navigate = useNavigate();
  const [task, setTask] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [updatedTask, setUpdatedTask] = useState({});
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showLabelSelector, setShowLabelSelector] = useState(false);
  const [showUserSelector, setShowUserSelector] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);

  // Fetch task details
  useEffect(() => {
    const fetchTask = async () => {
      try {
        setLoading(true);
        const { data } = await apiService.tasks.getById(projectId, boardId, columnId, taskId);
        setTask(data);
        setUpdatedTask({
          title: data.title,
          description: data.description,
          priority: data.priority
        });
        
        // Fetch comments
        const commentsRes = await apiService.comments.getByTask(projectId, boardId, columnId, taskId);
        setComments(commentsRes.data);
      } catch (err) {
        console.error('Error fetching task details:', err);
        setError('Failed to load task details');
      } finally {
        setLoading(false);
      }
    };
    
    if (projectId && boardId && columnId && taskId) {
      fetchTask();
    }
  }, [projectId, boardId, columnId, taskId]);

  // Handle input changes for task update
  const handleInputChange = (e) => {
    setUpdatedTask({
      ...updatedTask,
      [e.target.name]: e.target.value
    });
  };

  // Update task
  const handleUpdateTask = async () => {
    try {
      setLoading(true);
      const { data } = await apiService.tasks.update(projectId, boardId, columnId, taskId, updatedTask);
      setTask(data);
      setEditMode(false);
    } catch (err) {
      console.error('Error updating task:', err);
      setError('Failed to update task');
    } finally {
      setLoading(false);
    }
  };

  // Delete task
  const handleDeleteTask = async () => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      try {
        setLoading(true);
        await apiService.tasks.delete(projectId, boardId, columnId, taskId);
        navigate(`/projects/${projectId}/boards/${boardId}`);
      } catch (err) {
        console.error('Error deleting task:', err);
        setError('Failed to delete task');
        setLoading(false);
      }
    }
  };

  // Add comment
  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    
    try {
      const { data } = await apiService.comments.create(projectId, boardId, columnId, taskId, {
        content: newComment
      });
      
      setComments([...comments, data]);
      setNewComment('');
    } catch (err) {
      console.error('Error adding comment:', err);
      setError('Failed to add comment');
    }
  };

  // Handle label selection
  const handleLabelChange = async (selectedLabels) => {
    try {
      // Determine which labels to add and which to remove
      const currentLabelIds = task.labels.map(label => label.id);
      const selectedLabelIds = selectedLabels.map(label => label.id);
      
      const toAdd = selectedLabelIds.filter(id => !currentLabelIds.includes(id));
      const toRemove = currentLabelIds.filter(id => !selectedLabelIds.includes(id));
      
      if (toAdd.length > 0) {
        await apiService.tasks.addLabels(projectId, boardId, columnId, taskId, {
          label_ids: toAdd
        });
      }
      
      if (toRemove.length > 0) {
        await apiService.tasks.removeLabels(projectId, boardId, columnId, taskId, {
          label_ids: toRemove
        });
      }
      
      // Refresh task data
      const { data } = await apiService.tasks.getById(projectId, boardId, columnId, taskId);
      setTask(data);
    } catch (err) {
      console.error('Error updating labels:', err);
      setError('Failed to update labels');
    } finally {
      setShowLabelSelector(false);
    }
  };

  // Handle user assignment
  const handleAssignUsers = async (selectedUsers) => {
    try {
      await apiService.tasks.assign(projectId, boardId, columnId, taskId, {
        user_ids: selectedUsers.map(user => user.id)
      });
      
      // Refresh task data
      const { data } = await apiService.tasks.getById(projectId, boardId, columnId, taskId);
      setTask(data);
    } catch (err) {
      console.error('Error assigning users:', err);
      setError('Failed to assign users');
    } finally {
      setShowUserSelector(false);
    }
  };

  // Handle due date change
  const handleDueDateChange = async (date) => {
    try {
      await apiService.tasks.update(projectId, boardId, columnId, taskId, {
        due_date: date
      });
      
      // Refresh task data
      const { data } = await apiService.tasks.getById(projectId, boardId, columnId, taskId);
      setTask(data);
    } catch (err) {
      console.error('Error updating due date:', err);
      setError('Failed to update due date');
    } finally {
      setShowDatePicker(false);
    }
  };

  if (loading && !task) {
    return <div className="flex justify-center items-center h-screen">Loading task details...</div>;
  }

  if (error) {
    return <div className="text-red-500 text-center p-4">{error}</div>;
  }

  if (!task) {
    return <div className="text-center p-4">Task not found</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Back button */}
      <button
        onClick={() => navigate(`/projects/${projectId}/boards/${boardId}`)}
        className="flex items-center text-blue-600 hover:text-blue-800 mb-4"
      >
        <ArrowUturnLeftIcon className="h-4 w-4 mr-1" />
        Back to Board
      </button>
      
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        {/* Task header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-start">
          {editMode ? (
            <input
              name="title"
              value={updatedTask.title || ''}
              onChange={handleInputChange}
              className="text-2xl font-bold text-gray-900 dark:text-white w-full p-2 border border-gray-300 dark:border-gray-600 rounded"
            />
          ) : (
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white break-words">{task.title}</h1>
          )}
          
          <div className="flex space-x-2">
            <button
              onClick={() => setEditMode(!editMode)}
              className="p-2 text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
              title={editMode ? "Cancel" : "Edit task"}
            >
              <PencilSquareIcon className="h-5 w-5" />
            </button>
            <button
              onClick={handleDeleteTask}
              className="p-2 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
              title="Delete task"
            >
              <TrashIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
        
        {/* Task details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
          <div className="lg:col-span-2">
            {/* Description */}
            <div className="mb-6">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Description</h2>
              {editMode ? (
                <textarea
                  name="description"
                  value={updatedTask.description || ''}
                  onChange={handleInputChange}
                  rows="8"
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  placeholder="Task description (supports Markdown)"
                />
              ) : (
                <div 
                  className="prose dark:prose-invert max-w-none bg-gray-50 dark:bg-gray-700 p-4 rounded-lg"
                  dangerouslySetInnerHTML={{ __html: task.description ? marked(task.description) : '<p class="text-gray-500 dark:text-gray-400 italic">No description</p>' }}
                />
              )}
            </div>
            
            {/* Save button in edit mode */}
            {editMode && (
              <div className="mb-6">
                <button
                  onClick={handleUpdateTask}
                  disabled={loading}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50"
                >
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  onClick={() => {
                    setEditMode(false);
                    setUpdatedTask({
                      title: task.title,
                      description: task.description,
                      priority: task.priority
                    });
                  }}
                  className="px-4 py-2 ml-2 border border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                >
                  Cancel
                </button>
              </div>
            )}
            
            {/* Comments section */}
            <div>
              <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                <div className="flex items-center">
                  <ChatBubbleLeftRightIcon className="h-5 w-5 mr-2" />
                  Comments ({comments.length})
                </div>
              </h2>
              
              {/* Comment list */}
              <CommentList 
                comments={comments} 
                setComments={setComments} 
                projectId={projectId}
                boardId={boardId}
                columnId={columnId}
                taskId={taskId}
              />
              
              {/* Add comment */}
              <div className="mt-4">
                <textarea
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Write a comment..."
                  rows="3"
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
                <button
                  onClick={handleAddComment}
                  disabled={!newComment.trim()}
                  className="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50"
                >
                  Add Comment
                </button>
              </div>
            </div>
          </div>
          
          {/* Sidebar with task metadata */}
          <div className="lg:col-span-1 space-y-6">
            {/* Status and Column */}
            <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Status</h3>
              <div className="font-medium text-gray-900 dark:text-white">
                {task.column?.name || 'Unknown'}
              </div>
            </div>
            
            {/* Priority */}
            <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Priority</h3>
              {editMode ? (
                <select
                  name="priority"
                  value={updatedTask.priority || 'medium'}
                  onChange={handleInputChange}
                  className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              ) : (
                <div 
                  className={`inline-block px-2 py-1 rounded text-sm font-medium 
                    ${task.priority === 'urgent' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' : 
                      task.priority === 'high' ? 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200' : 
                      task.priority === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' : 
                      'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'}`}
                >
                  {task.priority ? task.priority.charAt(0).toUpperCase() + task.priority.slice(1) : 'Medium'}
                </div>
              )}
            </div>
            
            {/* Due Date */}
            <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Due Date</h3>
                <button 
                  className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                  onClick={() => setShowDatePicker(!showDatePicker)}
                >
                  <CalendarIcon className="h-4 w-4" />
                </button>
              </div>
              
              <div className="mt-2">
                {showDatePicker ? (
                  <DueDatePicker
                    initialDate={task.due_date ? new Date(task.due_date) : null}
                    onSave={handleDueDateChange}
                    onCancel={() => setShowDatePicker(false)}
                  />
                ) : (
                  <div className="font-medium text-gray-900 dark:text-white">
                    {task.due_date ? format(new Date(task.due_date), 'MMM d, yyyy h:mm a') : 'No due date'}
                  </div>
                )}
              </div>
            </div>
            
            {/* Assignees */}
            <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Assignees</h3>
                <button 
                  className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                  onClick={() => setShowUserSelector(!showUserSelector)}
                >
                  <UserCircleIcon className="h-4 w-4" />
                </button>
              </div>
              
              {showUserSelector ? (
                <UserSelector
                  projectId={projectId}
                  initialSelectedUsers={task.assignees || []}
                  onSave={handleAssignUsers}
                  onCancel={() => setShowUserSelector(false)}
                />
              ) : (
                <div className="mt-2">
                  {task.assignees && task.assignees.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {task.assignees.map(user => (
                        <div key={user.id} className="flex items-center bg-gray-200 dark:bg-gray-600 px-2 py-1 rounded-full">
                          {user.avatar ? (
                            <img src={user.avatar} alt={user.username} className="w-5 h-5 rounded-full mr-1" />
                          ) : (
                            <UserCircleIcon className="w-5 h-5 mr-1 text-gray-600 dark:text-gray-300" />
                          )}
                          <span className="text-sm text-gray-700 dark:text-gray-300">{user.full_name || user.username}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-gray-500 dark:text-gray-400 italic">Unassigned</div>
                  )}
                </div>
              )}
            </div>
            
            {/* Labels */}
            <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
              <div className="flex justify-between items-center">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Labels</h3>
                <button 
                  className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                  onClick={() => setShowLabelSelector(!showLabelSelector)}
                >
                  <TagIcon className="h-4 w-4" />
                </button>
              </div>
              
              {showLabelSelector ? (
                <LabelSelector
                  projectId={projectId}
                  initialSelectedLabels={task.labels || []}
                  onSave={handleLabelChange}
                  onCancel={() => setShowLabelSelector(false)}
                />
              ) : (
                <div className="mt-2">
                  {task.labels && task.labels.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {task.labels.map(label => (
                        <span
                          key={label.id}
                          className="px-2 py-1 text-xs rounded-full"
                          style={{ backgroundColor: label.color + '33', color: label.color }}
                        >
                          {label.name}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <div className="text-gray-500 dark:text-gray-400 italic">No labels</div>
                  )}
                </div>
              )}
            </div>
            
            {/* Attachments */}
            <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
                <div className="flex items-center">
                  <PaperClipIcon className="h-4 w-4 mr-1" />
                  Attachments
                </div>
              </h3>
              
              {task.attachments && task.attachments.length > 0 ? (
                <ul className="divide-y divide-gray-200 dark:divide-gray-600">
                  {task.attachments.map(attachment => (
                    <li key={attachment.id} className="py-2 flex justify-between items-center">
                      <a 
                        href={attachment.file}
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                      >
                        {attachment.filename}
                        <span className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                          ({(attachment.file_size / 1024).toFixed(1)} KB)
                        </span>
                      </a>
                      <button 
                        onClick={() => {/* Handle delete attachment */}}
                        className="text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="text-gray-500 dark:text-gray-400 italic">No attachments</div>
              )}
              
              <div className="mt-2">
                <label className="block text-center p-2 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer">
                  <span className="text-blue-600 dark:text-blue-400">Upload files</span>
                  <input type="file" className="hidden" />
                </label>
              </div>
            </div>
            
            {/* Task Info */}
            <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Info</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Created by: </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {task.created_by?.full_name || task.created_by?.username || 'Unknown'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Created at: </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {task.created_at ? format(new Date(task.created_at), 'MMM d, yyyy h:mm a') : 'Unknown'}
                  </span>
                </div>
                <div>
                  <span className="text-gray-500 dark:text-gray-400">Last updated: </span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {task.updated_at ? format(new Date(task.updated_at), 'MMM d, yyyy h:mm a') : 'Unknown'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaskDetail;
