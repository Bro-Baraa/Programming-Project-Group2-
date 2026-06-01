// ============================================
// Stage Monitoring Tool - API Client
// Communicates with the FastAPI backend
// ============================================

const API_BASE_URL = (() => {
  // Use the same host as the frontend page, but port 8001
  // This works for localhost:8080 → localhost:8001
  // and for remote access: framearch-juan:8080 → framearch-juan:8001
  // Fallback to localhost if opened via file:// (hostname is empty)
  const host = window.location.hostname || 'localhost';
  return `http://${host}:8001`;
})();

// Token storage — wrapped in try/catch for file:// protocol where localStorage may fail
function getToken() {
  try {
    return localStorage.getItem('stageMonitoringToken');
  } catch (e) {
    console.warn('[Auth] localStorage not available:', e.message);
    return null;
  }
}

function setToken(token) {
  try {
    if (token) {
      localStorage.setItem('stageMonitoringToken', token);
    } else {
      localStorage.removeItem('stageMonitoringToken');
    }
  } catch (e) {
    console.warn('[Auth] localStorage not available:', e.message);
  }
}

function getCurrentUser() {
  try {
    const userJson = localStorage.getItem('stageMonitoringUser');
    if (!userJson) return null;
    try {
      return JSON.parse(userJson);
    } catch {
      localStorage.removeItem('stageMonitoringUser');
      return null;
    }
  } catch (e) {
    console.warn('[Auth] localStorage not available:', e.message);
    return null;
  }
}

function setCurrentUser(user) {
  try {
    if (user) {
      localStorage.setItem('stageMonitoringUser', JSON.stringify(user));
    } else {
      localStorage.removeItem('stageMonitoringUser');
    }
  } catch (e) {
    console.warn('[Auth] localStorage not available:', e.message);
  }
}

// Generic API request
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  };
  
  // Add auth token if available
  const token = getToken();
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  
  // Handle FormData (remove Content-Type to let browser set it with boundary)
  if (options.body instanceof FormData) {
    delete config.headers['Content-Type'];
  }
  
  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
      
      // Handle auth errors
      if (response.status === 401) {
        setToken(null);
        setCurrentUser(null);
        window.location.href = 'index.html?view=login';
      }
      
      throw new Error(error.detail || `HTTP error! status: ${response.status}`);
    }
    
    // Handle empty responses
    if (response.status === 204) {
      return null;
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

// ============================================
// Auth API
// ============================================

const AuthAPI = {
  async login(email, password) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const url = `${API_BASE_URL}/auth/login`;
    console.log('[DEBUG] Login request to:', url);
    console.log('[DEBUG] Login email:', email);

    let response;
    try {
      response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: formData
      });
    } catch (networkError) {
      console.error('[DEBUG] Network error during login:', networkError);
      throw new Error('Kan geen verbinding maken met de server. Is de backend gestart?');
    }

    console.log('[DEBUG] Login response status:', response.status);

    if (!response.ok) {
      let errorText;
      try {
        const errorJson = await response.json();
        errorText = errorJson.detail || JSON.stringify(errorJson);
      } catch (e) {
        errorText = `HTTP ${response.status} - ${response.statusText}`;
      }
      console.error('[DEBUG] Login error:', errorText);
      throw new Error(errorText);
    }

    const data = await response.json();
    console.log('[DEBUG] Login success, user:', data.user?.email, 'role:', data.user?.role);
    setToken(data.access_token);
    setCurrentUser(data.user);
    return data;
  },
  
  async register(userData) {
    return apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  },
  
  async getMe() {
    return apiRequest('/auth/me');
  },
  
  logout() {
    setToken(null);
    setCurrentUser(null);
  },
  
  isLoggedIn() {
    return !!getToken();
  },
  
  getUser() {
    return getCurrentUser();
  },
  
  getRole() {
    const user = getCurrentUser();
    return user ? user.role : null;
  }
};

// ============================================
// Internships API
// ============================================

const InternshipsAPI = {
  async list(status = null) {
    const params = status ? `?status=${encodeURIComponent(status)}` : '';
    return apiRequest(`/internships${params}`);
  },
  
  async get(id) {
    return apiRequest(`/internships/${id}`);
  },
  
  async create(data) {
    return apiRequest('/internships', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  async uploadAgreement(id, file) {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiRequest(`/internships/${id}/agreement`, {
      method: 'POST',
      body: formData
    });
  },
  
  async getLogbooks(internshipId) {
    return apiRequest(`/internships/${internshipId}/logbooks`);
  },
  
  async createLogbook(internshipId, data) {
    return apiRequest(`/internships/${internshipId}/logbooks`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  async updateLogbook(logbookId, data) {
    return apiRequest(`/internships/logbooks/${logbookId}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  },
  
  async getEvaluations(internshipId) {
    return apiRequest(`/internships/${internshipId}/evaluations`);
  },
  
  async createEvaluation(internshipId, data) {
    return apiRequest(`/internships/${internshipId}/evaluations`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  async getFeedback(internshipId) {
    return apiRequest(`/internships/${internshipId}/feedback`);
  },
  
  async createFeedback(internshipId, data) {
    return apiRequest(`/internships/${internshipId}/feedback`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  async getDashboardStats() {
    return apiRequest('/internships/stats/dashboard');
  },

  async getFinalReport(internshipId) {
    return apiRequest(`/internships/${internshipId}/final-report`);
  },

  async submitLogbook(logbookId) {
    return apiRequest(`/internships/logbooks/${logbookId}/submit`, {
      method: 'POST'
    });
  }
};

// ============================================
// Competencies API
// ============================================

const CompetenciesAPI = {
  async list(activeOnly = true) {
    return apiRequest(`/competencies?active_only=${activeOnly}`);
  },
  
  async create(data) {
    return apiRequest('/competencies', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  async update(id, data) {
    return apiRequest(`/competencies/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  },
  
  async delete(id) {
    return apiRequest(`/competencies/${id}`, {
      method: 'DELETE'
    });
  },
  
  async checkWeights() {
    return apiRequest('/competencies/check-weights');
  }
};

// ============================================
// Proposals
// ============================================

const ProposalsAPI = {
  async review(internshipId, status, feedback = null) {
    const body = { status };
    if (feedback) body.feedback = feedback;
    return apiRequest(`/internships/${internshipId}/proposal`, {
      method: 'PATCH',
      body: JSON.stringify(body)
    });
  },
  
  async resubmit(internshipId, newDescription, extra = {}) {
    const body = { new_description: newDescription, ...extra };
    return apiRequest(`/internships/${internshipId}/resubmit`, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  }
};

// ============================================
// Evaluation Rules
// ============================================

const EvaluationRulesAPI = {
  async update(evaluationId, ruleId, data) {
    return apiRequest(`/evaluations/${evaluationId}/rules/${ruleId}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  }
};

// ============================================
// Agreements (validate)
// ============================================

const AgreementsAPI = {
  async validate(internshipId, status, insuranceVerified = null) {
    const body = { status };
    if (insuranceVerified !== null) body.insurance_verified = insuranceVerified;
    return apiRequest(`/internships/${internshipId}/agreement`, {
      method: 'PATCH',
      body: JSON.stringify(body)
    });
  },
  
  async download(internshipId) {
    return `${API_BASE_URL}/internships/${internshipId}/agreement/download`;
  }
};

// ============================================
// Health Check
// ============================================

const HealthAPI = {
  async check() {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }
};

// API clients are available globally for browser use
// No module.exports needed - this is browser-only code