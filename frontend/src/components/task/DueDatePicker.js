import React, { useState, useEffect, useRef } from 'react';
import { format, isValid, parseISO } from 'date-fns';
import { 
  CalendarIcon, 
  XMarkIcon, 
  CheckIcon 
} from '@heroicons/react/24/outline';

const DueDatePicker = ({ initialDate, onSave, onCancel }) => {
  const [showDatepicker, setShowDatepicker] = useState(true);
  const [selectedDate, setSelectedDate] = useState(null);
  const datePickerRef = useRef(null);
  
  // Initialize with the initial date if provided
  useEffect(() => {
    if (initialDate) {
      const date = typeof initialDate === 'string' ? parseISO(initialDate) : initialDate;
      setSelectedDate(isValid(date) ? date : null);
    }
  }, [initialDate]);
  
  // Format date for input
  const formatDateForInput = (date) => {
    if (!date) return '';
    return format(date, 'yyyy-MM-dd');
  };
  
  // Handle date change from input
  const handleDateChange = (e) => {
    const dateValue = e.target.value;
    if (dateValue) {
      const newDate = new Date(dateValue);
      setSelectedDate(isValid(newDate) ? newDate : null);
    } else {
      setSelectedDate(null);
    }
  };
  
  // Handle saving the selected date
  const handleSave = () => {
    onSave(selectedDate);
  };
  
  // Handle removing the due date
  const handleRemoveDueDate = () => {
    setSelectedDate(null);
  };
  
  return (
    <div className="mt-2">
      <div className="mb-3">
        <label htmlFor="due-date" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
          Due Date
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <CalendarIcon className="h-5 w-5 text-gray-400" aria-hidden="true" />
          </div>
          <input
            type="date"
            id="due-date"
            name="due-date"
            value={formatDateForInput(selectedDate)}
            onChange={handleDateChange}
            className="focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 sm:text-sm border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white py-2"
            placeholder="Select date"
          />
        </div>
        
        {selectedDate && (
          <div className="mt-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Selected: {format(selectedDate, 'MMMM d, yyyy')}
            </span>
            <button
              onClick={handleRemoveDueDate}
              className="ml-2 text-sm text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
            >
              Clear
            </button>
          </div>
        )}
      </div>
      
      {/* Help text */}
      <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
        Set a due date for this task. Tasks with upcoming due dates will appear in the dashboard.
      </p>
      
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

export default DueDatePicker;
