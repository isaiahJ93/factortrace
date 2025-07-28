// services/api.js - Production Backend Integration Layer

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://api.factortrace.com';
const WS_URL = process.env.REACT_APP_WS_URL || 'wss://api.factortrace.com';

// Token management (integrate with your auth system)
const getAuthToken = () => {
  // This should get token from your auth provider (Auth0, Cognito, etc.)
  return localStorage.getItem('auth_token');
};

// Request interceptor for common headers
const apiRequest = async (url, options = {}) => {
  const defaultHeaders = {
    'Authorization': `Bearer ${getAuthToken()}`,
    'X-Client-Version': '1.0.0',
    'X-Request-ID': crypto.randomUUID(),
  };

  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Unknown error' }));
    throw new APIError(response.status, error.message, error.code);
  }

  return response;
};

// Custom error class for better error handling
class APIError extends Error {
  constructor(status, message, code) {
    super(message);
    this.status = status;
    this.code = code;
    this.retryable = status >= 500 || status === 429;
  }
}

// Emission Management APIs
export const emissionAPI = {
  // Fetch emissions for current user
  async getEmissions(scope = 3) {
    const response = await apiRequest(`/api/v1/emissions?scope=${scope}`);
    return response.json();
  },

  // Get single emission details
  async getEmission(emissionId) {
    const response = await apiRequest(`/api/v1/emissions/${emissionId}`);
    return response.json();
  },

  // Update emission
  async updateEmission(emissionId, data) {
    const response = await apiRequest(`/api/v1/emissions/${emissionId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return response.json();
  },
};

// Evidence Upload APIs
export const evidenceAPI = {
  // Upload evidence with progress tracking
  async uploadEvidence(emissionId, file, metadata, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();

      // Add file and metadata
      formData.append('file', file);
      formData.append('emissionId', emissionId);
      formData.append('evidenceType', metadata.evidenceType);
      formData.append('timestamp', new Date().toISOString());
      
      // Calculate checksum before upload
      calculateFileChecksum(file).then(checksum => {
        formData.append('checksum', checksum);
        formData.append('compliance', JSON.stringify(metadata.compliance));

        // Track upload progress
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const progress = Math.round((e.loaded / e.total) * 100);
            onProgress(progress);
          }
        });

        // Handle completion
        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const response = JSON.parse(xhr.responseText);
              resolve(response);
            } catch (e) {
              reject(new Error('Invalid response format'));
            }
          } else {
            try {
              const error = JSON.parse(xhr.responseText);
              reject(new APIError(xhr.status, error.message, error.code));
            } catch (e) {
              reject(new APIError(xhr.status, 'Upload failed', 'UNKNOWN'));
            }
          }
        });

        // Handle errors
        xhr.addEventListener('error', () => {
          reject(new APIError(0, 'Network error', 'NETWORK_ERROR'));
        });

        // Set headers
        xhr.open('POST', `${API_BASE_URL}/api/v1/emissions/${emissionId}/evidence`);
        xhr.setRequestHeader('Authorization', `Bearer ${getAuthToken()}`);
        xhr.setRequestHeader('X-Client-Version', '1.0.0');
        xhr.setRequestHeader('X-Request-ID', crypto.randomUUID());

        // Send request
        xhr.send(formData);
      });
    });
  },

  // Get evidence list for emission
  async getEvidence(emissionId) {
    const response = await apiRequest(`/api/v1/emissions/${emissionId}/evidence`);
    return response.json();
  },

  // Delete evidence
  async deleteEvidence(emissionId, evidenceId) {
    await apiRequest(`/api/v1/emissions/${emissionId}/evidence/${evidenceId}`, {
      method: 'DELETE',
    });
  },

  // Get signed URL for direct upload (S3, GCS, etc.)
  async getUploadUrl(emissionId, fileMetadata) {
    const response = await apiRequest(`/api/v1/emissions/${emissionId}/evidence/upload-url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(fileMetadata),
    });
    return response.json();
  },
};

// Audit Trail APIs
export const auditAPI = {
  // Send audit log entry
  async log(action, details) {
    // Fire and forget - don't block UI on audit logging
    apiRequest('/api/v1/audit/logs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action,
        details,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight,
        },
      }),
    }).catch(error => {
      // Log to console but don't throw - audit shouldn't break functionality
      console.error('[Audit Log Failed]', error);
      // Could also send to a backup logging service
    });
  },
};

// WebSocket connection for real-time updates
export class EmissionWebSocket {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.listeners = new Map();
  }

  connect() {
    try {
      this.ws = new WebSocket(`${WS_URL}/emissions/sync?token=${getAuthToken()}`);

      this.ws.onopen = () => {
        console.log('[WS] Connected');
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.emit(data.type, data.payload);
        } catch (e) {
          console.error('[WS] Invalid message format', e);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WS] Error', error);
      };

      this.ws.onclose = () => {
        console.log('[WS] Disconnected');
        this.reconnect();
      };
    } catch (error) {
      console.error('[WS] Connection failed', error);
      this.reconnect();
    }
  }

  reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WS] Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    console.log(`[WS] Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect();
    }, this.reconnectDelay);

    // Exponential backoff
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, 30000);
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event).add(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).delete(callback);
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`[WS] Error in event listener for ${event}`, error);
        }
      });
    }
  }

  send(type, payload) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type, payload }));
    } else {
      console.error('[WS] Cannot send - connection not open');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

// Utility functions
async function calculateFileChecksum(file) {
  const buffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

// Export singleton WebSocket instance
export const emissionWS = new EmissionWebSocket();

// React Query integration (if using)
export const queryKeys = {
  emissions: (scope) => ['emissions', scope],
  emission: (id) => ['emission', id],
  evidence: (emissionId) => ['evidence', emissionId],
};

// Usage example with React Query:
/*
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { emissionAPI, evidenceAPI, queryKeys } from './services/api';

// In your component:
const { data: emissions } = useQuery(
  queryKeys.emissions(3),
  () => emissionAPI.getEmissions(3)
);

const uploadMutation = useMutation(
  ({ emissionId, file, metadata }) => 
    evidenceAPI.uploadEvidence(emissionId, file, metadata, setProgress),
  {
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries(queryKeys.emissions(3));
      queryClient.invalidateQueries(queryKeys.evidence(variables.emissionId));
    },
  }
);
*/