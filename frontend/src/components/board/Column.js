import React from 'react';
import Task from './Task';
import { Draggable } from 'react-beautiful-dnd';
import { PlusIcon } from '@heroicons/react/24/outline';
import { useState } from 'react';
import TaskFormModal from './TaskFormModal';

const Column = ({ column, tasks, provided, projectId, boardId }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  return (
    <div
      ref={provided.innerRef}
      {...provided.droppableProps}
      className="bg-gray-100 dark:bg-gray-800 rounded-lg min-w-[300px] w-[300px] h-full flex flex-col"
    >
      <div className="p-3 font-medium border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
        <div className="flex items-center">
          <h3 className="text-lg font-semibold">{column.name}</h3>
          <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
            {tasks.length}
            {column.wip_limit && <span>/{column.wip_limit}</span>}
          </span>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="p-1 rounded-full hover:bg-gray-200 dark:hover:bg-gray-700"
          title="Add task"
        >
          <PlusIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        </button>
      </div>
      
      <div className="flex-grow overflow-y-auto p-2">
        {tasks.map((task, index) => (
          <Draggable
            key={task.id}
            draggableId={`task-${task.id}`}
            index={index}
          >
            {(provided, snapshot) => (
              <Task
                task={task}
                provided={provided}
                isDragging={snapshot.isDragging}
                projectId={projectId}
                boardId={boardId}
                columnId={column.id}
              />
            )}
          </Draggable>
        ))}
        {provided.placeholder}
      </div>
      
      {isModalOpen && (
        <TaskFormModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          projectId={projectId}
          boardId={boardId}
          columnId={column.id}
          initialOrder={tasks.length}
        />
      )}
    </div>
  );
};

export default Column;
