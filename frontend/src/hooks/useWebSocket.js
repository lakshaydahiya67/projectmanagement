import { useEffect, useState, useCallback } from 'react';

export const useWebSocket = (url, onMessage) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);

  // Function to send messages
  const sendMessage = useCallback((data) => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(data));
      return true;
    }
    return false;
  }, [socket]);

  // Setup WebSocket connection
  useEffect(() => {
    let ws = null;
    let heartbeatInterval = null;

    const setupSocket = () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setError('Authentication token not found');
        return;
      }

      // Include token in the URL for authentication
      const socketUrl = `${url}?token=${token}`;
      ws = new WebSocket(socketUrl);

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
        console.log('WebSocket connection established');
        
        // Setup heartbeat to keep connection alive
        heartbeatInterval = setInterval(() => {
          if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'heartbeat' }));
          }
        }, 30000); // Send heartbeat every 30 seconds
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };

      ws.onclose = (event) => {
        setIsConnected(false);
        console.log('WebSocket connection closed:', event.code, event.reason);
        
        // Clear heartbeat interval
        if (heartbeatInterval) {
          clearInterval(heartbeatInterval);
        }
        
        // Attempt to reconnect after delay unless it was a clean close
        if (event.code !== 1000) {
          setTimeout(() => {
            console.log('Attempting to reconnect WebSocket...');
            setupSocket();
          }, 5000); // Wait 5 seconds before reconnecting
        }
      };

      setSocket(ws);
    };

    setupSocket();

    // Cleanup on unmount
    return () => {
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
      }
      
      if (ws) {
        // Use code 1000 for normal closure
        ws.close(1000, 'Component unmounted');
      }
    };
  }, [url, onMessage]);

  return { isConnected, error, sendMessage };
};

// Specialized hooks for different WebSocket connections
export const useBoardWebSocket = (boardId, onMessage) => {
  const wsUrl = `ws://${window.location.host}/ws/boards/${boardId}/`;
  return useWebSocket(wsUrl, onMessage);
};

export const useProjectWebSocket = (projectId, onMessage) => {
  const wsUrl = `ws://${window.location.host}/ws/projects/${projectId}/`;
  return useWebSocket(wsUrl, onMessage);
};

export const useNotificationWebSocket = (onMessage) => {
  const wsUrl = `ws://${window.location.host}/ws/notifications/`;
  return useWebSocket(wsUrl, onMessage);
};
