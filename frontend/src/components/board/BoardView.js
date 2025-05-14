import React, { useState, useEffect } from 'react';
import { DragDropContext, Droppable } from 'react-beautiful-dnd';
import Column from './Column';
import { useBoardWebSocket } from '../../hooks/useWebSocket';
import apiService from '../../services/api';
import UserPresence from './UserPresence';

import { useParams } from 'react-router-dom';

const BoardView = () => {
  const { projectId, boardId } = useParams();
  const [board, setBoard] = useState(null);
  const [columns, setColumns] = useState([]);
  const [tasks, setTasks] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewers, setViewers] = useState([]);

  // Handle WebSocket messages
  const handleWebSocketMessage = (data) => {
    console.log('WebSocket message received:', data);
    
    switch(data.type) {
      case 'task_create_message':
        // Add task to the column
        setTasks(prev => {
          const columnTasks = [...(prev[data.column_id] || [])];
          columnTasks.push(data.task);
          return { ...prev, [data.column_id]: columnTasks };
        });
        break;
        
      case 'task_move_message':
        // Handle task movement between columns
        handleTaskMovement(data);
        break;
        
      case 'task_update_message':
        // Update task properties
        handleTaskUpdate(data.task_id, data.updates);
        break;
        
      case 'task_label_message':
        // Update task labels
        handleTaskLabelUpdate(data.task_id, data.labels);
        break;
      
      case 'current_viewers':
        // Update viewers list
        setViewers(data.viewers);
        break;
        
      case 'user_joined':
        // Add user to viewers list if not already there
        setViewers(prev => {
          if (!prev.find(v => v.id === data.user.id)) {
            return [...prev, data.user];
          }
          return prev;
        });
        break;
        
      case 'user_left':
        // Remove user from viewers list
        setViewers(prev => prev.filter(viewer => viewer.id !== data.user.id));
        break;
        
      default:
        console.log('Unhandled message type:', data.type);
    }
  };

  // Initialize WebSocket connection
  const { isConnected } = useBoardWebSocket(boardId, handleWebSocketMessage);

  // Handle task movement between columns
  const handleTaskMovement = (data) => {
    setTasks(prev => {
      // Create new state object
      const newState = { ...prev };
      
      // Remove from source column
      if (newState[data.source_column_id]) {
        newState[data.source_column_id] = newState[data.source_column_id].filter(
          task => task.id !== data.task_id
        );
      }
      
      // Add to destination column
      if (newState[data.destination_column_id]) {
        // Get the task data
        let taskToMove = null;
        for (const columnId in prev) {
          const task = prev[columnId].find(t => t.id === data.task_id);
          if (task) {
            taskToMove = { ...task, column: data.destination_column_id, order: data.order };
            break;
          }
        }
        
        if (taskToMove) {
          const destTasks = [...newState[data.destination_column_id]];
          destTasks.push(taskToMove);
          // Sort by order
          destTasks.sort((a, b) => a.order - b.order);
          newState[data.destination_column_id] = destTasks;
        }
      }
      
      return newState;
    });
  };

  // Handle task property updates
  const handleTaskUpdate = (taskId, updates) => {
    setTasks(prev => {
      const newState = { ...prev };
      
      // Find and update the task
      for (const columnId in newState) {
        const index = newState[columnId].findIndex(task => task.id === taskId);
        if (index !== -1) {
          newState[columnId] = [...newState[columnId]];
          newState[columnId][index] = {
            ...newState[columnId][index],
            ...updates
          };
          break;
        }
      }
      
      return newState;
    });
  };

  // Handle task label updates
  const handleTaskLabelUpdate = (taskId, labels) => {
    setTasks(prev => {
      const newState = { ...prev };
      
      // Find and update the task
      for (const columnId in newState) {
        const index = newState[columnId].findIndex(task => task.id === taskId);
        if (index !== -1) {
          newState[columnId] = [...newState[columnId]];
          newState[columnId][index] = {
            ...newState[columnId][index],
            labels
          };
          break;
        }
      }
      
      return newState;
    });
  };

  // Fetch board details
  useEffect(() => {
    const fetchBoard = async () => {
      try {
        setLoading(true);
        const { data } = await apiService.boards.getById(projectId, boardId);
        setBoard(data);
      } catch (err) {
        console.error('Error fetching board:', err);
        setError('Failed to load board details');
      }
    };
    
    fetchBoard();
  }, [projectId, boardId]);

  // Fetch columns
  useEffect(() => {
    const fetchColumns = async () => {
      try {
        const { data } = await apiService.columns.getAll(projectId, boardId);
        // Sort columns by order
        const sortedColumns = data.sort((a, b) => a.order - b.order);
        setColumns(sortedColumns);
        
        // Initialize tasks state with empty arrays for each column
        const tasksObj = {};
        for (const column of sortedColumns) {
          tasksObj[column.id] = [];
        }
        setTasks(tasksObj);
      } catch (err) {
        console.error('Error fetching columns:', err);
        setError('Failed to load board columns');
      }
    };
    
    if (board) {
      fetchColumns();
    }
  }, [projectId, boardId, board]);

  // Fetch tasks for each column
  useEffect(() => {
    const fetchTasks = async () => {
      try {
        const tasksObj = {};
        
        for (const column of columns) {
          const { data } = await apiService.tasks.getByColumn(projectId, boardId, column.id);
          tasksObj[column.id] = data.sort((a, b) => a.order - b.order);
        }
        
        setTasks(tasksObj);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching tasks:', err);
        setError('Failed to load tasks');
        setLoading(false);
      }
    };
    
    if (columns.length > 0) {
      fetchTasks();
    }
  }, [projectId, boardId, columns]);

  // Handle drag end
  const handleDragEnd = async (result) => {
    const { destination, source, draggableId } = result;
    
    // Dropped outside a droppable area or same position
    if (!destination || 
        (destination.droppableId === source.droppableId && 
         destination.index === source.index)) {
      return;
    }
    
    // Get task and columns
    const sourceColumnId = parseInt(source.droppableId);
    const destColumnId = parseInt(destination.droppableId);
    const taskId = parseInt(draggableId.replace('task-', ''));
    
    try {
      // Optimistic UI update first
      const newTaskMap = { ...tasks };
      
      // Remove from source column
      const sourceColumn = [...newTaskMap[sourceColumnId]];
      const [removedTask] = sourceColumn.splice(source.index, 1);
      newTaskMap[sourceColumnId] = sourceColumn;
      
      // Add to destination column
      const destColumn = [...newTaskMap[destColumnId]];
      destColumn.splice(destination.index, 0, { ...removedTask, column: destColumnId });
      newTaskMap[destColumnId] = destColumn;
      
      // Update order values for the destination column
      newTaskMap[destColumnId] = newTaskMap[destColumnId].map((task, idx) => ({
        ...task,
        order: idx
      }));
      
      setTasks(newTaskMap);
      
      // Send API request to update task position
      await apiService.tasks.move(
        projectId, 
        boardId, 
        sourceColumnId, 
        taskId, 
        {
          column: destColumnId,
          order: destination.index
        }
      );
    } catch (err) {
      console.error('Error moving task:', err);
      // Revert back on error by re-fetching
      const sourceResponse = await apiService.tasks.getByColumn(projectId, boardId, sourceColumnId);
      const destResponse = await apiService.tasks.getByColumn(projectId, boardId, destColumnId);
      
      setTasks(prev => ({
        ...prev,
        [sourceColumnId]: sourceResponse.data,
        [destColumnId]: destResponse.data
      }));
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
        <p className="text-gray-600 dark:text-gray-300">Loading board...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col justify-center items-center h-screen">
        <div className="bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded mb-4 max-w-md w-full">
          <div className="flex">
            <div className="py-1">
              <svg className="h-6 w-6 text-red-500 mr-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="font-bold">Error</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
        </div>
        <button 
          onClick={() => window.location.reload()} 
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between items-center mb-6 px-4">
        <h1 className="text-2xl font-bold">{board?.name}</h1>
        <UserPresence viewers={viewers} />
      </div>
      
      <DragDropContext onDragEnd={handleDragEnd}>
        <div className="flex-grow overflow-x-auto">
          <div className="flex h-full p-4 space-x-4">
            {columns.length === 0 ? (
              <div className="flex flex-col items-center justify-center w-full h-64 text-gray-500 dark:text-gray-400">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
                <p>No columns found in this board.</p>
                <button 
                  className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                  onClick={() => { /* Add a function to create a column */ }}
                >
                  Create a column
                </button>
              </div>
            ) : (
              columns.map((column) => (
                <Droppable key={column.id} droppableId={column.id.toString()}>
                  {(provided) => (
                    <Column
                      column={column}
                      tasks={tasks[column.id] || []}
                      provided={provided}
                      projectId={projectId}
                      boardId={boardId}
                    />
                  )}
                </Droppable>
              ))
            )}
          </div>
        </div>
      </DragDropContext>
      
      <div className="p-2 text-xs text-gray-500">
        {isConnected ? (
          <span className="text-green-500 font-medium">● Connected</span>
        ) : (
          <span className="text-red-500 font-medium">● Disconnected</span>
        )}
      </div>
    </div>
  );
};

export default BoardView;
