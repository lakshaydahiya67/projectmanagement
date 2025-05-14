import React, { useState } from 'react';
import apiService from '../../services/api';
import { 
  TrashIcon, 
  PencilSquareIcon, 
  UserCircleIcon, 
  ChatBubbleLeftRightIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import { format } from 'date-fns';
import { marked } from 'marked';

const CommentList = ({ comments, setComments, projectId, boardId, columnId, taskId }) => {
  const [replyingTo, setReplyingTo] = useState(null);
  const [replyContent, setReplyContent] = useState('');
  const [editingComment, setEditingComment] = useState(null);
  const [editedContent, setEditedContent] = useState('');
  
  // Handle showing reply form
  const handleShowReplyForm = (commentId) => {
    setReplyingTo(commentId);
    setReplyContent('');
  };
  
  // Handle submitting a reply
  const handleSubmitReply = async (commentId) => {
    if (!replyContent.trim()) return;
    
    try {
      const { data } = await apiService.comments.createReply(
        projectId, 
        boardId, 
        columnId, 
        taskId, 
        commentId, 
        { content: replyContent }
      );
      
      // Update comments state by finding the parent comment and adding reply
      setComments(comments.map(comment => {
        if (comment.id === commentId) {
          return {
            ...comment,
            replies: [...(comment.replies || []), data]
          };
        }
        return comment;
      }));
      
      setReplyingTo(null);
      setReplyContent('');
    } catch (error) {
      console.error('Error adding reply:', error);
    }
  };
  
  // Handle editing a comment
  const handleEditComment = (comment) => {
    setEditingComment(comment.id);
    setEditedContent(comment.content);
  };
  
  // Handle submitting edited comment
  const handleSubmitEdit = async (commentId) => {
    if (!editedContent.trim()) return;
    
    try {
      const { data } = await apiService.comments.update(
        projectId, 
        boardId, 
        columnId, 
        taskId, 
        commentId, 
        { content: editedContent }
      );
      
      // Update the comment in state
      setComments(comments.map(comment => {
        if (comment.id === commentId) {
          return { ...comment, content: data.content, updated_at: data.updated_at };
        }
        return comment;
      }));
      
      setEditingComment(null);
      setEditedContent('');
    } catch (error) {
      console.error('Error updating comment:', error);
    }
  };
  
  // Handle deleting a comment
  const handleDeleteComment = async (commentId) => {
    if (!window.confirm('Are you sure you want to delete this comment?')) return;
    
    try {
      await apiService.comments.delete(projectId, boardId, columnId, taskId, commentId);
      
      // Remove comment from state
      setComments(comments.filter(comment => comment.id !== commentId));
    } catch (error) {
      console.error('Error deleting comment:', error);
    }
  };
  
  // Format date for display
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return format(date, 'MMM d, yyyy h:mm a');
  };
  
  // Check if a comment was edited
  const wasEdited = (comment) => {
    const createdAt = new Date(comment.created_at).getTime();
    const updatedAt = new Date(comment.updated_at).getTime();
    return updatedAt > createdAt;
  };
  
  // Render a single comment
  const renderComment = (comment, isReply = false) => (
    <div
      key={comment.id}
      className={`mb-4 ${isReply ? 'ml-12 mt-2' : 'border-b border-gray-200 dark:border-gray-700 pb-4'}`}
    >
      <div className="flex">
        {/* Avatar */}
        <div className="flex-shrink-0 mr-3">
          {comment.author?.avatar ? (
            <img
              src={comment.author.avatar}
              alt={comment.author.username || 'User avatar'}
              className="h-10 w-10 rounded-full"
            />
          ) : (
            <UserCircleIcon className="h-10 w-10 text-gray-500 dark:text-gray-400" />
          )}
        </div>
        
        {/* Comment content */}
        <div className="flex-grow">
          <div className="flex items-start justify-between">
            <div>
              <h4 className="font-medium text-gray-900 dark:text-white">
                {comment.author?.full_name || comment.author?.username || 'Anonymous'}
              </h4>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {formatDate(comment.created_at)}
                {wasEdited(comment) && ' (edited)'}
              </p>
            </div>
            
            {/* Comment actions */}
            <div className="flex space-x-2">
              {!isReply && (
                <button
                  onClick={() => handleShowReplyForm(comment.id)}
                  className="text-gray-500 hover:text-blue-600 dark:hover:text-blue-400"
                  title="Reply"
                >
                  <ChatBubbleLeftRightIcon className="h-4 w-4" />
                </button>
              )}
              <button
                onClick={() => handleEditComment(comment)}
                className="text-gray-500 hover:text-blue-600 dark:hover:text-blue-400"
                title="Edit"
              >
                <PencilSquareIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => handleDeleteComment(comment.id)}
                className="text-gray-500 hover:text-red-600 dark:hover:text-red-400"
                title="Delete"
              >
                <TrashIcon className="h-4 w-4" />
              </button>
            </div>
          </div>
          
          {/* Comment text */}
          {editingComment === comment.id ? (
            <div className="mt-2">
              <textarea
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white"
                rows="3"
              />
              <div className="flex justify-end space-x-2 mt-2">
                <button
                  onClick={() => setEditingComment(null)}
                  className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
                >
                  <XMarkIcon className="h-4 w-4 mr-1" />
                  Cancel
                </button>
                <button
                  onClick={() => handleSubmitEdit(comment.id)}
                  className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center"
                >
                  <CheckIcon className="h-4 w-4 mr-1" />
                  Save
                </button>
              </div>
            </div>
          ) : (
            <div 
              className="prose dark:prose-invert max-w-none mt-1"
              dangerouslySetInnerHTML={{ __html: marked(comment.content) }}
            />
          )}
          
          {/* Reply form */}
          {replyingTo === comment.id && (
            <div className="mt-3">
              <textarea
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                placeholder="Write a reply..."
                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white"
                rows="2"
              />
              <div className="flex justify-end space-x-2 mt-2">
                <button
                  onClick={() => setReplyingTo(null)}
                  className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
                >
                  <XMarkIcon className="h-4 w-4 mr-1" />
                  Cancel
                </button>
                <button
                  onClick={() => handleSubmitReply(comment.id)}
                  disabled={!replyContent.trim()}
                  className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center"
                >
                  <ChatBubbleLeftRightIcon className="h-4 w-4 mr-1" />
                  Reply
                </button>
              </div>
            </div>
          )}
          
          {/* Replies */}
          {comment.replies && comment.replies.length > 0 && (
            <div className="mt-3">
              {comment.replies.map(reply => renderComment(reply, true))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
  
  return (
    <div className="comment-list">
      {comments.length === 0 ? (
        <p className="text-gray-500 dark:text-gray-400 italic">No comments yet</p>
      ) : (
        comments.map(comment => renderComment(comment))
      )}
    </div>
  );
};

export default CommentList;
