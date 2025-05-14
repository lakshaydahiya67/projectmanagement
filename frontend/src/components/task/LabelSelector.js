import React, { useState, useEffect } from 'react';
import apiService from '../../services/api';
import { PlusIcon, XMarkIcon, CheckIcon } from '@heroicons/react/24/outline';

const LabelSelector = ({ projectId, initialSelectedLabels = [], onSave, onCancel }) => {
  const [labels, setLabels] = useState([]);
  const [selectedLabels, setSelectedLabels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newLabel, setNewLabel] = useState({ name: '', color: '#3B82F6' });
  
  // Initialize with the initially selected labels
  useEffect(() => {
    setSelectedLabels(initialSelectedLabels);
  }, [initialSelectedLabels]);
  
  // Fetch available labels for the project
  useEffect(() => {
    const fetchLabels = async () => {
      try {
        setLoading(true);
        const { data } = await apiService.labels.getByProject(projectId);
        setLabels(data);
      } catch (err) {
        console.error('Error fetching labels:', err);
        setError('Failed to load labels');
      } finally {
        setLoading(false);
      }
    };
    
    fetchLabels();
  }, [projectId]);
  
  // Toggle a label selection
  const toggleLabel = (label) => {
    setSelectedLabels(prevSelected => {
      const isSelected = prevSelected.some(l => l.id === label.id);
      if (isSelected) {
        return prevSelected.filter(l => l.id !== label.id);
      } else {
        return [...prevSelected, label];
      }
    });
  };
  
  // Create a new label
  const handleCreateLabel = async () => {
    if (!newLabel.name.trim()) return;
    
    try {
      const { data } = await apiService.labels.create(projectId, newLabel);
      setLabels([...labels, data]);
      setSelectedLabels([...selectedLabels, data]);
      setNewLabel({ name: '', color: '#3B82F6' });
      setShowCreateForm(false);
    } catch (err) {
      console.error('Error creating label:', err);
      setError('Failed to create label');
    }
  };
  
  // Save selected labels
  const handleSave = () => {
    onSave(selectedLabels);
  };
  
  // Common label colors
  const colorOptions = [
    { name: 'Blue', value: '#3B82F6' },
    { name: 'Red', value: '#EF4444' },
    { name: 'Green', value: '#10B981' },
    { name: 'Yellow', value: '#F59E0B' },
    { name: 'Purple', value: '#8B5CF6' },
    { name: 'Pink', value: '#EC4899' },
    { name: 'Gray', value: '#6B7280' },
  ];
  
  if (loading) {
    return <div className="text-center py-3">Loading labels...</div>;
  }
  
  return (
    <div className="mt-2">
      {error && (
        <div className="text-sm text-red-500 mb-2">{error}</div>
      )}
      
      {/* Label list */}
      <div className="mb-3 max-h-48 overflow-y-auto">
        {labels.length === 0 ? (
          <div className="text-gray-500 dark:text-gray-400 text-sm">
            No labels available. Create one below.
          </div>
        ) : (
          <div className="space-y-1">
            {labels.map(label => (
              <div 
                key={label.id}
                className={`flex items-center p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer ${
                  selectedLabels.some(l => l.id === label.id) 
                    ? 'bg-gray-100 dark:bg-gray-700' 
                    : ''
                }`}
                onClick={() => toggleLabel(label)}
              >
                <div 
                  className="w-4 h-4 rounded-full mr-2"
                  style={{ backgroundColor: label.color }}
                />
                <span className="flex-grow text-sm text-gray-700 dark:text-gray-300">
                  {label.name}
                </span>
                {selectedLabels.some(l => l.id === label.id) && (
                  <CheckIcon className="h-4 w-4 text-green-500" />
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Create new label form */}
      {showCreateForm ? (
        <div className="mt-3 p-2 border border-gray-300 dark:border-gray-600 rounded">
          <div className="mb-2">
            <input
              type="text"
              placeholder="Label name"
              value={newLabel.name}
              onChange={(e) => setNewLabel({ ...newLabel, name: e.target.value })}
              className="w-full p-1 text-sm border border-gray-300 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white"
            />
          </div>
          
          <div className="mb-2">
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Color:</div>
            <div className="flex flex-wrap gap-1">
              {colorOptions.map((color) => (
                <div
                  key={color.value}
                  className={`w-6 h-6 rounded-full cursor-pointer border-2 ${
                    newLabel.color === color.value 
                      ? 'border-black dark:border-white' 
                      : 'border-transparent'
                  }`}
                  style={{ backgroundColor: color.value }}
                  onClick={() => setNewLabel({ ...newLabel, color: color.value })}
                  title={color.name}
                />
              ))}
            </div>
          </div>
          
          <div className="flex justify-between">
            <button
              onClick={() => setShowCreateForm(false)}
              className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateLabel}
              disabled={!newLabel.name.trim()}
              className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 disabled:opacity-50"
            >
              Create
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
        >
          <PlusIcon className="h-4 w-4 mr-1" />
          Create new label
        </button>
      )}
      
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

export default LabelSelector;
