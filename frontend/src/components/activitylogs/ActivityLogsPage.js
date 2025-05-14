import React from 'react';
import { useParams } from 'react-router-dom';
import ActivityLogList from './ActivityLogList';

const ActivityLogsPage = () => {
  const { projectId } = useParams();
  
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">
        {projectId ? 'Project Activity' : 'Activity Logs'}
      </h1>
      
      <ActivityLogList />
    </div>
  );
};

export default ActivityLogsPage; 