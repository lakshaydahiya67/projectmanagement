import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import apiService from '../../services/api';
import { 
  PlusIcon, 
  ChartBarIcon, 
  ClockIcon, 
  FolderIcon, 
  UsersIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import ProjectCard from '../common/ProjectCard';
import EmptyState from '../common/EmptyState';

const ProjectDashboard = () => {
  const [projects, setProjects] = useState([]);
  const [recentBoards, setRecentBoards] = useState([]);
  const [upcomingTasks, setUpcomingTasks] = useState([]);
  const [projectStats, setProjectStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  const navigate = useNavigate();
  
  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Fetch projects - this is the minimum required endpoint
        try {
          const projectsResponse = await apiService.projects.getAll();
          // Ensure projects is always an array
          if (Array.isArray(projectsResponse.data)) {
            setProjects(projectsResponse.data);
          } else if (projectsResponse.data && Array.isArray(projectsResponse.data.results)) {
            setProjects(projectsResponse.data.results);
          } else if (projectsResponse.data && typeof projectsResponse.data === 'object') {
            // Try to find any array property that might contain projects
            const possibleArrays = Object.values(projectsResponse.data).filter(val => Array.isArray(val));
            if (possibleArrays.length > 0) {
              setProjects(possibleArrays[0]);
            } else {
              console.error('API returned projects in an unexpected format:', projectsResponse.data);
              setProjects([]);
            }
          } else {
            console.error('API returned projects in an unexpected format:', projectsResponse.data);
            setProjects([]);
          }
        } catch (err) {
          console.error('Error fetching projects:', err);
          setError('Failed to load projects. Please try again later.');
          setProjects([]);
        }
        
        // Try to fetch recent boards, but don't block the dashboard if it fails
        try {
          const recentBoardsResponse = await apiService.boards.getRecent();
          setRecentBoards(recentBoardsResponse.data || []);
        } catch (err) {
          console.error('Error fetching recent boards:', err);
          // Don't set an error, just use empty array
          setRecentBoards([]);
        }
        
        // Try to fetch upcoming tasks, but don't block the dashboard if it fails
        try {
          const upcomingTasksResponse = await apiService.tasks.getUpcoming();
          setUpcomingTasks(upcomingTasksResponse.data || []);
        } catch (err) {
          console.error('Error fetching upcoming tasks:', err);
          // Don't set an error, just use empty array
          setUpcomingTasks([]);
        }
        
        // Try to fetch project stats, but don't block the dashboard if it fails
        try {
          const projectStatsResponse = await apiService.projects.getStats();
          setProjectStats(projectStatsResponse.data || null);
        } catch (err) {
          console.error('Error fetching project stats:', err);
          // Don't set an error, just use null
          setProjectStats(null);
        }
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchDashboardData();
  }, []);
  
  // Filter projects based on search term - ensure projects is an array before filtering
  const filteredProjects = Array.isArray(projects) ? projects.filter(project =>
    project.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    project.description?.toLowerCase().includes(searchTerm.toLowerCase())
  ) : [];
  
  // Handle project creation
  const handleCreateProject = async (projectData) => {
    try {
      const { data } = await apiService.projects.create(projectData);
      setProjects([...projects, data]);
      setShowCreateModal(false);
      navigate(`/projects/${data.id}`);
    } catch (err) {
      console.error('Error creating project:', err);
      setError('Failed to create project. Please try again.');
    }
  };
  
  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };
  
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <ArrowPathIcon className="animate-spin h-8 w-8 text-blue-500" />
        <span className="ml-2">Loading dashboard...</span>
      </div>
    );
  }
  
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 sm:mb-0">Dashboard</h1>
        <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
          <div className="relative">
            <input
              type="text"
              placeholder="Search projects..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
            />
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <PlusIcon className="h-5 w-5 mr-1" />
            New Project
          </button>
        </div>
      </div>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <span>{error}</span>
          <button
            className="float-right font-bold"
            onClick={() => setError(null)}
          >
            &times;
          </button>
        </div>
      )}
      
      {/* Stats Overview */}
      {projectStats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-blue-100 dark:bg-blue-900 rounded-md p-3">
                  <FolderIcon className="h-6 w-6 text-blue-600 dark:text-blue-200" />
                </div>
                <div className="ml-5">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    Total Projects
                  </dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900 dark:text-white">
                    {projectStats.total_projects || projects.length}
                  </dd>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-green-100 dark:bg-green-900 rounded-md p-3">
                  <UsersIcon className="h-6 w-6 text-green-600 dark:text-green-200" />
                </div>
                <div className="ml-5">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    Active Team Members
                  </dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900 dark:text-white">
                    {projectStats.active_members || 0}
                  </dd>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-yellow-100 dark:bg-yellow-900 rounded-md p-3">
                  <ChartBarIcon className="h-6 w-6 text-yellow-600 dark:text-yellow-200" />
                </div>
                <div className="ml-5">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    Tasks Completed
                  </dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900 dark:text-white">
                    {projectStats.completed_tasks || 0}
                  </dd>
                </div>
              </div>
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0 bg-red-100 dark:bg-red-900 rounded-md p-3">
                  <ClockIcon className="h-6 w-6 text-red-600 dark:text-red-200" />
                </div>
                <div className="ml-5">
                  <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                    Upcoming Tasks
                  </dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900 dark:text-white">
                    {projectStats.upcoming_tasks || upcomingTasks.length || 0}
                  </dd>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Projects */}
      <div className="mb-10">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Your Projects</h2>
        {filteredProjects.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredProjects.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        ) : (
          <EmptyState 
            icon={<FolderIcon className="h-12 w-12" />}
            title="No projects found"
            description={
              searchTerm 
                ? "No projects match your search criteria." 
                : "You don't have any projects yet. Create your first project to get started."
            }
            action={
              searchTerm 
                ? {
                    label: "Clear search",
                    onClick: () => setSearchTerm('')
                  }
                : {
                    label: "Create Project",
                    onClick: () => setShowCreateModal(true)
                  }
            }
          />
        )}
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Recent Boards */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Recently Visited Boards</h2>
          {recentBoards.length > 0 ? (
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
              <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                {recentBoards.map((board) => (
                  <li key={board.id}>
                    <Link 
                      to={`/projects/${board.project.id}/boards/${board.id}`}
                      className="block hover:bg-gray-50 dark:hover:bg-gray-700"
                    >
                      <div className="px-4 py-4 sm:px-6">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-10 w-10 bg-blue-100 dark:bg-blue-900 rounded-md flex items-center justify-center">
                              <span className="text-blue-600 dark:text-blue-200 font-medium">
                                {board.name.substring(0, 2).toUpperCase()}
                              </span>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900 dark:text-white">
                                {board.name}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                {board.project?.name}
                              </div>
                            </div>
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            Last visited {formatDate(board.last_visited)}
                          </div>
                        </div>
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <EmptyState 
              icon={<FolderIcon className="h-12 w-12" />}
              title="No recent boards"
              description="You haven't visited any boards recently."
            />
          )}
        </div>
        
        {/* Upcoming Tasks */}
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Upcoming Tasks</h2>
          {upcomingTasks.length > 0 ? (
            <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
              <ul className="divide-y divide-gray-200 dark:divide-gray-700">
                {upcomingTasks.map((task) => (
                  <li key={task.id}>
                    <Link 
                      to={`/projects/${task.project.id}/boards/${task.board.id}?task=${task.id}`}
                      className="block hover:bg-gray-50 dark:hover:bg-gray-700"
                    >
                      <div className="px-4 py-4 sm:px-6">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <div className={`flex-shrink-0 h-10 w-10 ${
                              task.priority === 'HIGH' ? 'bg-red-100 dark:bg-red-900' :
                              task.priority === 'MEDIUM' ? 'bg-yellow-100 dark:bg-yellow-900' :
                              'bg-green-100 dark:bg-green-900'
                            } rounded-md flex items-center justify-center`}>
                              <span className={`${
                                task.priority === 'HIGH' ? 'text-red-600 dark:text-red-200' :
                                task.priority === 'MEDIUM' ? 'text-yellow-600 dark:text-yellow-200' :
                                'text-green-600 dark:text-green-200'
                              } font-medium`}>
                                {task.priority.substring(0, 1)}
                              </span>
                            </div>
                            <div className="ml-4">
                              <div className="text-sm font-medium text-gray-900 dark:text-white">
                                {task.title}
                              </div>
                              <div className="text-sm text-gray-500 dark:text-gray-400">
                                {task.board?.name}
                              </div>
                            </div>
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            Due {formatDate(task.due_date)}
                          </div>
                        </div>
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <EmptyState 
              icon={<ClockIcon className="h-12 w-12" />}
              title="No upcoming tasks"
              description="You don't have any upcoming tasks due soon."
            />
          )}
        </div>
      </div>
      
      {/* Create Project Modal */}
      {showCreateModal && (
        <CreateProjectModal 
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateProject}
        />
      )}
    </div>
  );
};

// Create Project Modal Component
const CreateProjectModal = ({ onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_private: false
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({
      ...formData,
      [name]: type === 'checkbox' ? checked : value
    });
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      setError('Project name is required');
      return;
    }
    
    try {
      setIsLoading(true);
      setError('');
      await onSubmit(formData);
    } catch (err) {
      setError('Failed to create project');
      setIsLoading(false);
    }
  };
  
  return (
    <div className="fixed inset-0 overflow-y-auto z-50" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" aria-hidden="true" onClick={onClose}></div>
        
        <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div className="bg-white dark:bg-gray-800 px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="sm:flex sm:items-start">
              <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white" id="modal-title">
                  Create New Project
                </h3>
                <div className="mt-4">
                  {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                      {error}
                    </div>
                  )}
                  
                  <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                      <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Project Name *
                      </label>
                      <input
                        type="text"
                        id="name"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                        required
                      />
                    </div>
                    <div className="mb-4">
                      <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Description
                      </label>
                      <textarea
                        id="description"
                        name="description"
                        rows="3"
                        value={formData.description}
                        onChange={handleChange}
                        className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 dark:border-gray-600 rounded-md dark:bg-gray-700 dark:text-white"
                      />
                    </div>
                    <div className="mb-4 flex items-center">
                      <input
                        type="checkbox"
                        id="is_private"
                        name="is_private"
                        checked={formData.is_private}
                        onChange={handleChange}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor="is_private" className="ml-2 block text-sm text-gray-700 dark:text-gray-300">
                        Private project
                      </label>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isLoading}
              className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
            >
              {isLoading ? 'Creating...' : 'Create Project'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 dark:border-gray-600 shadow-sm px-4 py-2 bg-white dark:bg-gray-800 text-base font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProjectDashboard;
