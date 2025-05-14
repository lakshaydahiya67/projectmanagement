import React, { useState, useEffect } from 'react';
import apiService from '../../services/api';
import { 
  MagnifyingGlassIcon, 
  CheckIcon, 
  XMarkIcon,
  UserCircleIcon 
} from '@heroicons/react/24/outline';

const UserSelector = ({ projectId, initialSelectedUsers = [], onSave, onCancel }) => {
  const [users, setUsers] = useState([]);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  
  // Initialize with the initially selected users
  useEffect(() => {
    setSelectedUsers(initialSelectedUsers);
  }, [initialSelectedUsers]);
  
  // Fetch project members
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        setLoading(true);
        const { data } = await apiService.projects.getMembers(projectId);
        setUsers(data);
      } catch (err) {
        console.error('Error fetching project members:', err);
        setError('Failed to load members');
      } finally {
        setLoading(false);
      }
    };
    
    fetchUsers();
  }, [projectId]);
  
  // Toggle user selection
  const toggleUser = (user) => {
    setSelectedUsers(prev => {
      const isSelected = prev.some(u => u.id === user.id);
      if (isSelected) {
        return prev.filter(u => u.id !== user.id);
      } else {
        return [...prev, user];
      }
    });
  };
  
  // Filter users based on search term
  const filteredUsers = users.filter(user => {
    const fullName = `${user.first_name || ''} ${user.last_name || ''}`.toLowerCase().trim();
    return (
      user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
      fullName.includes(searchTerm.toLowerCase()) ||
      (user.email && user.email.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  });
  
  // Save selected users
  const handleSave = () => {
    onSave(selectedUsers);
  };
  
  if (loading) {
    return <div className="text-center py-3">Loading members...</div>;
  }
  
  return (
    <div className="mt-2">
      {error && (
        <div className="text-sm text-red-500 mb-2">{error}</div>
      )}
      
      {/* Search input */}
      <div className="relative mb-3">
        <MagnifyingGlassIcon className="h-5 w-5 absolute left-2 top-1/2 transform -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search members..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-9 w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm dark:bg-gray-700 dark:text-white text-sm"
        />
      </div>
      
      {/* User list */}
      <div className="mb-3 max-h-48 overflow-y-auto">
        {filteredUsers.length === 0 ? (
          <div className="text-gray-500 dark:text-gray-400 text-sm text-center p-2">
            {searchTerm ? 'No matching members found' : 'No members available for this project'}
          </div>
        ) : (
          <div className="space-y-1">
            {filteredUsers.map(user => (
              <div 
                key={user.id}
                className={`flex items-center p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer ${
                  selectedUsers.some(u => u.id === user.id) 
                    ? 'bg-gray-100 dark:bg-gray-700' 
                    : ''
                }`}
                onClick={() => toggleUser(user)}
              >
                <div className="flex-shrink-0 mr-2">
                  {user.avatar ? (
                    <img
                      src={user.avatar}
                      alt={user.username}
                      className="h-8 w-8 rounded-full"
                    />
                  ) : (
                    <UserCircleIcon className="h-8 w-8 text-gray-500 dark:text-gray-400" />
                  )}
                </div>
                <div className="flex-grow">
                  <div className="text-sm font-medium text-gray-700 dark:text-gray-200">
                    {user.first_name && user.last_name
                      ? `${user.first_name} ${user.last_name}`
                      : user.username}
                  </div>
                  {user.email && (
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {user.email}
                    </div>
                  )}
                </div>
                {selectedUsers.some(u => u.id === user.id) && (
                  <CheckIcon className="h-5 w-5 text-green-500" />
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Actions */}
      <div className="mt-4 flex justify-end space-x-2">
        <button
          onClick={onCancel}
          className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center"
        >
          <XMarkIcon className="h-4 w-4 mr-1" />
          Cancel
        </button>
        <button
          onClick={handleSave}
          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center"
        >
          <CheckIcon className="h-4 w-4 mr-1" />
          Save
        </button>
      </div>
    </div>
  );
};

export default UserSelector;
