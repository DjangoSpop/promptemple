/**
 * SSE (Server-Sent Events) Client
 * Real-time streaming communication for AI validation and feedback
 *
 * Features:
 * - Auto-reconnection with exponential backoff
 * - Event type handling
 * - Error recovery
 * - Connection state management
 * - Heartbeat/keepalive support
 */

class SSEClient {
  /**
   * Create SSE client
   * @param {string} url - SSE endpoint URL
   * @param {Object} options - Configuration options
   */
  constructor(url, options = {}) {
    this.url = url;
    this.options = {
      reconnect: true,
      reconnectInterval: 1000,
      maxReconnectInterval: 30000,
      reconnectDecay: 1.5,
      heartbeatTimeout: 45000,
      withCredentials: true,
      headers: {},
      ...options
    };

    this.eventSource = null;
    this.reconnectAttempts = 0;
    this.reconnectTimer = null;
    this.heartbeatTimer = null;
    this.eventHandlers = new Map();
    this.state = 'disconnected'; // disconnected, connecting, connected

    // Bind methods
    this.handleOpen = this.handleOpen.bind(this);
    this.handleError = this.handleError.bind(this);
    this.handleMessage = this.handleMessage.bind(this);
  }

  /**
   * Connect to SSE endpoint
   */
  connect() {
    if (this.state === 'connected' || this.state === 'connecting') {
      console.warn('SSEClient: Already connected or connecting');
      return;
    }

    this.state = 'connecting';
    this.emit('connecting');

    try {
      // Build URL with query parameters
      const url = new URL(this.url, window.location.origin);

      // Add auth token if available
      const token = this.getAuthToken();
      if (token) {
        url.searchParams.set('token', token);
      }

      // Create EventSource
      this.eventSource = new EventSource(url.toString(), {
        withCredentials: this.options.withCredentials
      });

      // Event listeners
      this.eventSource.addEventListener('open', this.handleOpen);
      this.eventSource.addEventListener('error', this.handleError);
      this.eventSource.addEventListener('message', this.handleMessage);

      // Custom event types
      this.eventSource.addEventListener('validation', (e) => {
        this.emit('validation', JSON.parse(e.data));
      });

      this.eventSource.addEventListener('progress', (e) => {
        this.emit('progress', JSON.parse(e.data));
      });

      this.eventSource.addEventListener('complete', (e) => {
        this.emit('complete', JSON.parse(e.data));
      });

      this.eventSource.addEventListener('error_event', (e) => {
        this.emit('error_event', JSON.parse(e.data));
      });

      this.eventSource.addEventListener('heartbeat', (e) => {
        this.resetHeartbeat();
      });

    } catch (error) {
      console.error('SSEClient: Connection error', error);
      this.handleError(error);
    }
  }

  /**
   * Handle connection open
   */
  handleOpen() {
    console.log('SSEClient: Connected');
    this.state = 'connected';
    this.reconnectAttempts = 0;
    this.emit('connected');
    this.resetHeartbeat();
  }

  /**
   * Handle connection error
   * @param {Event} error - Error event
   */
  handleError(error) {
    console.error('SSEClient: Error', error);
    this.state = 'disconnected';
    this.emit('error', error);

    // Attempt reconnection
    if (this.options.reconnect) {
      this.reconnect();
    }
  }

  /**
   * Handle incoming message
   * @param {MessageEvent} event - Message event
   */
  handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      this.emit('message', data);
      this.resetHeartbeat();
    } catch (error) {
      console.error('SSEClient: Failed to parse message', error);
    }
  }

  /**
   * Reconnect with exponential backoff
   */
  reconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    // Calculate backoff interval
    const interval = Math.min(
      this.options.reconnectInterval * Math.pow(this.options.reconnectDecay, this.reconnectAttempts),
      this.options.maxReconnectInterval
    );

    this.reconnectAttempts++;

    console.log(`SSEClient: Reconnecting in ${interval}ms (attempt ${this.reconnectAttempts})`);
    this.emit('reconnecting', { attempt: this.reconnectAttempts, interval });

    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, interval);
  }

  /**
   * Reset heartbeat timer
   */
  resetHeartbeat() {
    if (this.heartbeatTimer) {
      clearTimeout(this.heartbeatTimer);
    }

    this.heartbeatTimer = setTimeout(() => {
      console.warn('SSEClient: Heartbeat timeout');
      this.disconnect();
      if (this.options.reconnect) {
        this.reconnect();
      }
    }, this.options.heartbeatTimeout);
  }

  /**
   * Disconnect from SSE endpoint
   */
  disconnect() {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.heartbeatTimer) {
      clearTimeout(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    this.state = 'disconnected';
    this.emit('disconnected');
  }

  /**
   * Register event handler
   * @param {string} event - Event name
   * @param {Function} handler - Event handler
   */
  on(event, handler) {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, []);
    }
    this.eventHandlers.get(event).push(handler);
  }

  /**
   * Unregister event handler
   * @param {string} event - Event name
   * @param {Function} handler - Event handler
   */
  off(event, handler) {
    if (!this.eventHandlers.has(event)) return;

    const handlers = this.eventHandlers.get(event);
    const index = handlers.indexOf(handler);
    if (index > -1) {
      handlers.splice(index, 1);
    }
  }

  /**
   * Emit event
   * @param {string} event - Event name
   * @param {*} data - Event data
   */
  emit(event, data) {
    if (!this.eventHandlers.has(event)) return;

    this.eventHandlers.get(event).forEach(handler => {
      try {
        handler(data);
      } catch (error) {
        console.error(`SSEClient: Error in ${event} handler`, error);
      }
    });
  }

  /**
   * Get authentication token
   * @returns {string|null} Auth token
   */
  getAuthToken() {
    // Try to get JWT token from cookie
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'jwt-auth') {
        return value;
      }
    }

    // Try localStorage
    const token = localStorage.getItem('authToken');
    if (token) {
      return token;
    }

    return null;
  }

  /**
   * Get connection state
   * @returns {string} Connection state
   */
  getState() {
    return this.state;
  }

  /**
   * Check if connected
   * @returns {boolean} Connection status
   */
  isConnected() {
    return this.state === 'connected';
  }
}

/**
 * Template Validation SSE Client
 * Specialized client for template AI validation streaming
 */
class TemplateValidationClient extends SSEClient {
  /**
   * Start validation for a template
   * @param {string} templateId - Template ID
   * @param {Object} options - Validation options
   */
  startValidation(templateId, options = {}) {
    const url = `/api/v2/optimization/stream/${templateId}/`;
    this.url = url;
    this.connect();
  }

  /**
   * Handle validation progress
   * @param {Function} callback - Progress callback
   */
  onProgress(callback) {
    this.on('progress', callback);
  }

  /**
   * Handle validation complete
   * @param {Function} callback - Complete callback
   */
  onComplete(callback) {
    this.on('complete', callback);
  }

  /**
   * Handle validation error
   * @param {Function} callback - Error callback
   */
  onError(callback) {
    this.on('error_event', callback);
  }

  /**
   * Handle validation result
   * @param {Function} callback - Validation callback
   */
  onValidation(callback) {
    this.on('validation', callback);
  }
}

/**
 * Create SSE client for endpoint
 * @param {string} url - SSE endpoint URL
 * @param {Object} options - Configuration options
 * @returns {SSEClient} SSE client instance
 */
function createSSEClient(url, options = {}) {
  return new SSEClient(url, options);
}

/**
 * Create template validation client
 * @param {string} templateId - Template ID
 * @param {Object} options - Configuration options
 * @returns {TemplateValidationClient} Validation client instance
 */
function createTemplateValidationClient(templateId, options = {}) {
  const client = new TemplateValidationClient('', options);
  if (templateId) {
    client.startValidation(templateId, options);
  }
  return client;
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    SSEClient,
    TemplateValidationClient,
    createSSEClient,
    createTemplateValidationClient
  };
}

// Global access
window.SSEClient = SSEClient;
window.TemplateValidationClient = TemplateValidationClient;
window.createSSEClient = createSSEClient;
window.createTemplateValidationClient = createTemplateValidationClient;
