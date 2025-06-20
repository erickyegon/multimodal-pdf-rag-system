const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

console.log('API_BASE_URL:', API_BASE_URL); // Debug log

class ApiClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;

    // Validate base URL
    if (!this.baseURL || this.baseURL === 'undefined') {
      console.error('API_BASE_URL is undefined. Check your .env file');
      this.baseURL = 'http://localhost:8000'; // Fallback
    }
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;

    console.log('Making request to:', url); // Debug log

    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Remove Content-Type for FormData
    if (config.body instanceof FormData) {
      delete config.headers['Content-Type'];
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Chat endpoints
  async sendChatMessage(query, options = {}) {
    return this.request('/api/v1/chat/chat', {
      method: 'POST',
      body: JSON.stringify({
        query,
        context_type: options.contentTypes || ['text', 'table', 'image'],
        include_charts: options.includeCharts !== false
      }),
    });
  }

  // Document endpoints
  async getDocuments() {
    return this.request('/api/v1/upload/documents', {
      method: 'GET',
    });
  }

  async deleteDocument(documentId) {
    return this.request(`/api/v1/upload/documents/${documentId}`, {
      method: 'DELETE',
    });
  }



  // Upload endpoints
  async uploadFile(file, onProgress) {
    const formData = new FormData();
    formData.append('file', file);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const progress = (event.loaded / event.total) * 100;
          onProgress(progress);
        }
      });

      xhr.onload = () => {
        if (xhr.status === 200) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new Error(`Upload failed: ${xhr.statusText}`));
        }
      };

      xhr.onerror = () => reject(new Error('Upload failed'));

      xhr.open('POST', `${this.baseURL}/api/v1/upload/upload`);
      xhr.send(formData);
    });
  }

  // Analytics endpoints
  async runAnalytics(query, generateChart = true) {
    return this.request('/api/v1/analytics/analytics', {
      method: 'POST',
      body: JSON.stringify({
        query,
        generate_chart: generateChart
      }),
    });
  }

  // Health check
  async healthCheck() {
    return this.request('/health');
  }
}

export default new ApiClient();