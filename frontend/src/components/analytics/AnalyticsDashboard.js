import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import apiService from '../../services/api';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const AnalyticsDashboard = () => {
  const { projectId } = useParams();
  const [metrics, setMetrics] = useState(null);
  const [burndownData, setBurndownData] = useState(null);
  const [taskDistribution, setTaskDistribution] = useState(null);
  const [userProductivity, setUserProductivity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch analytics data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Get project metrics
        const metricsResponse = await apiService.analytics.getProjectMetrics(projectId);
        setMetrics(metricsResponse.data);

        // Get burndown chart data
        const burndownResponse = await apiService.analytics.getBurndownData(projectId);
        setBurndownData(burndownResponse.data);

        // Get task distribution data
        const distributionResponse = await apiService.analytics.getTaskDistribution(projectId);
        setTaskDistribution(distributionResponse.data);

        // Get user productivity data
        const productivityResponse = await apiService.analytics.getUserProductivity(projectId);
        setUserProductivity(productivityResponse.data);
      } catch (err) {
        console.error('Error fetching analytics data:', err);
        setError('Failed to load analytics data');
      } finally {
        setLoading(false);
      }
    };

    if (projectId) {
      fetchData();
    }
  }, [projectId]);

  if (loading) {
    return <div className="flex justify-center items-center h-64">Loading analytics data...</div>;
  }

  if (error) {
    return <div className="text-red-500 text-center p-4">{error}</div>;
  }

  // Burndown chart configuration
  const burndownChartData = {
    labels: burndownData?.burndown_data?.map(item => item.date) || [],
    datasets: [
      {
        label: 'Actual Remaining Tasks',
        data: burndownData?.burndown_data?.map(item => item.remaining_tasks) || [],
        borderColor: 'rgba(255, 99, 132, 1)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        fill: true,
      },
      {
        label: 'Ideal Burndown',
        data: burndownData?.burndown_data?.map(item => item.ideal_remaining) || [],
        borderColor: 'rgba(54, 162, 235, 1)',
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderDash: [5, 5],
        fill: false,
      }
    ]
  };

  // Task distribution chart configuration
  const taskDistributionChartData = {
    labels: taskDistribution?.columns?.map(item => item.name) || [],
    datasets: [
      {
        label: 'Tasks per Column',
        data: taskDistribution?.columns?.map(item => item.task_count) || [],
        backgroundColor: [
          'rgba(255, 99, 132, 0.6)',
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(153, 102, 255, 0.6)',
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(153, 102, 255, 1)',
        ],
        borderWidth: 1,
      }
    ]
  };

  // User productivity chart configuration
  const productivityChartData = {
    labels: userProductivity?.users?.map(item => item.user_name) || [],
    datasets: [
      {
        label: 'Completed Tasks',
        data: userProductivity?.users?.map(item => item.total_tasks_completed) || [],
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
      },
      {
        label: 'Created Tasks',
        data: userProductivity?.users?.map(item => item.total_tasks_created) || [],
        backgroundColor: 'rgba(153, 102, 255, 0.6)',
        borderColor: 'rgba(153, 102, 255, 1)',
        borderWidth: 1,
      },
      {
        label: 'Comments',
        data: userProductivity?.users?.map(item => item.total_comments) || [],
        backgroundColor: 'rgba(255, 159, 64, 0.6)',
        borderColor: 'rgba(255, 159, 64, 1)',
        borderWidth: 1,
      }
    ]
  };

  // Priority distribution chart
  const priorityData = {
    labels: ['Low', 'Medium', 'High', 'Urgent'],
    datasets: [
      {
        label: 'Tasks by Priority',
        data: [
          taskDistribution?.priorities?.low || 0,
          taskDistribution?.priorities?.medium || 0,
          taskDistribution?.priorities?.high || 0,
          taskDistribution?.priorities?.urgent || 0,
        ],
        backgroundColor: [
          'rgba(54, 162, 235, 0.6)',
          'rgba(255, 206, 86, 0.6)',
          'rgba(255, 159, 64, 0.6)',
          'rgba(255, 99, 132, 0.6)',
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(255, 159, 64, 1)',
          'rgba(255, 99, 132, 1)',
        ],
        borderWidth: 1,
      }
    ]
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Project Analytics</h1>
      
      {/* Summary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
          <h3 className="text-gray-500 dark:text-gray-400 text-sm font-medium">Total Tasks</h3>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">{metrics?.summary?.total_tasks || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
          <h3 className="text-gray-500 dark:text-gray-400 text-sm font-medium">Completed Tasks</h3>
          <p className="text-3xl font-bold text-green-600 dark:text-green-400">{metrics?.summary?.total_tasks_completed || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
          <h3 className="text-gray-500 dark:text-gray-400 text-sm font-medium">Overdue Tasks</h3>
          <p className="text-3xl font-bold text-red-600 dark:text-red-400">{metrics?.summary?.total_tasks_overdue || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
          <h3 className="text-gray-500 dark:text-gray-400 text-sm font-medium">Project Completion</h3>
          <div className="flex items-center">
            <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
              {metrics?.summary?.completion_rate || 0}%
            </p>
            <div className="ml-4 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
              <div
                className="bg-blue-600 dark:bg-blue-500 h-2.5 rounded-full"
                style={{ width: `${metrics?.summary?.completion_rate || 0}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Burndown Chart */}
      <div className="mb-8">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Burndown Chart</h2>
          <div className="h-80">
            <Line 
              data={burndownChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  y: {
                    beginAtZero: true,
                    title: {
                      display: true,
                      text: 'Remaining Tasks'
                    }
                  },
                  x: {
                    title: {
                      display: true,
                      text: 'Date'
                    }
                  }
                }
              }}
            />
          </div>
        </div>
      </div>
      
      {/* Task Distribution and Priority Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Task Distribution</h2>
          <div className="h-80">
            <Bar
              data={taskDistributionChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  y: {
                    beginAtZero: true,
                    title: {
                      display: true,
                      text: 'Number of Tasks'
                    }
                  }
                }
              }}
            />
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Priority Distribution</h2>
          <div className="h-80 flex items-center justify-center">
            <div style={{ width: '70%', height: '100%' }}>
              <Pie
                data={priorityData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: {
                      position: 'bottom',
                    }
                  }
                }}
              />
            </div>
          </div>
        </div>
      </div>
      
      {/* User Productivity Chart */}
      <div className="mb-8">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow">
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">Team Productivity</h2>
          <div className="h-80">
            <Bar
              data={productivityChartData}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  y: {
                    beginAtZero: true,
                    title: {
                      display: true,
                      text: 'Count'
                    }
                  }
                }
              }}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
