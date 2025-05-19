import { useEffect, useState, useCallback, useContext } from 'react';
import ReconnectingWebSocket from 'reconnecting-websocket';
import { AuthContext } from '../context/AuthContext';

export const useWebSocket = (url, onMessage) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const { refreshToken } = useContext(AuthContext);

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
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;

    const setupSocket = async () => {
      try {
        // Get a fresh token before connecting
        let token = localStorage.getItem('access_token');
        
        // If token looks expired based on JWT structure (check exp field)
        if (token) {
          const tokenParts = token.split('.');
          if (tokenParts.length === 3) {
            const payload = JSON.parse(atob(tokenParts[1]));
            const expiration = payload.exp * 1000; // Convert to milliseconds
            
            // Get token expiry threshold from env or default to 5 minutes
            const expiryThresholdMins = parseInt(process.env.REACT_APP_TOKEN_EXPIRY_THRESHOLD_MINS || '5');
            
            // If token is expired or about to expire
            if (Date.now() >= expiration - expiryThresholdMins * 60 * 1000) {
              token = await refreshToken();
            }
          }
        }
        
      if (!token) {
        setError('Authentication token not found');
        return;
      }

      // Include token in the URL for authentication
      const socketUrl = `${url}?token=${token}`;
        
        // Use ReconnectingWebSocket instead of regular WebSocket
        ws = new ReconnectingWebSocket(socketUrl, [], {
          connectionTimeout: 10000,
          maxRetries: 10,
          minReconnectionDelay: 1000,
          maxReconnectionDelay: 30000,
          reconnectionDelayGrowFactor: 1.3,
        });

      ws.onopen = () => {
        setIsConnected(true);
        setError(null);
          reconnectAttempts = 0;
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

        ws.onclose = async (event) => {
        setIsConnected(false);
        console.log('WebSocket connection closed:', event.code, event.reason);
        
        // Clear heartbeat interval
        if (heartbeatInterval) {
          clearInterval(heartbeatInterval);
            heartbeatInterval = null;
        }
        
          // Token might be expired
          if (event.code === 1006 || event.code === 1011) {
            reconnectAttempts++;
            
            // Try refreshing token if it seems like an authentication issue
            if (reconnectAttempts <= maxReconnectAttempts) {
              try {
                await refreshToken();
                // Allow reconnection logic in ReconnectingWebSocket to handle it
              } catch (err) {
                console.error('Failed to refresh token:', err);
              }
            }
        }
      };

      setSocket(ws);
      } catch (err) {
        console.error('Error setting up WebSocket:', err);
        setError(`WebSocket setup error: ${err.message}`);
      }
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
  }, [url, onMessage, refreshToken]);

  return { isConnected, error, sendMessage };
};

// Get WebSocket base URL from environment variables
const getWebSocketBaseUrl = () => {
  // Always use the environment variable
  return process.env.REACT_APP_WEBSOCKET_URL;
};

// Specialized hooks for different WebSocket connections
export const useBoardWebSocket = (boardId, onMessage) => {
  const wsBaseUrl = getWebSocketBaseUrl();
  const wsUrl = `${wsBaseUrl}/boards/${boardId}/`;
  return useWebSocket(wsUrl, onMessage);
};

export const useProjectWebSocket = (projectId, onMessage) => {
  const wsBaseUrl = getWebSocketBaseUrl();
  const wsUrl = `${wsBaseUrl}/projects/${projectId}/`;
  return useWebSocket(wsUrl, onMessage);
};

export const useNotificationWebSocket = (onMessage) => {
  const wsBaseUrl = getWebSocketBaseUrl();
  const wsUrl = `${wsBaseUrl}/notifications/`;
  return useWebSocket(wsUrl, onMessage);
};
