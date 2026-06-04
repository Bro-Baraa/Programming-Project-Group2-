// ============================================
// Stage Monitoring Tool - API Client
// Communicates with the FastAPI backend
// ============================================

const API_BASE_URL = (() => {
  const host = window.location.hostname || 'localhost';
  const port = window.location.port;

  // Production (80/443): backend + frontend served from same origin
  if (port === '80' || port === '443') {
    return `${window.location.protocol}//${window.location.host}`;
  }
  // Dev: frontend on 8080 (or file://), backend on 8001
  return `http://${host}:8001`;
})();
console.log('[API] API_BASE_URL resolved to:', API_BASE_URL);

// Token storage — wrapped in try/catch for file:// protocol where localStorage may fail
function safeStorage(key, value = undefined) {
  try {
    if (value === undefined) {
      return localStorage.getItem(key);
    }
    if (value === null) {
      localStorage.removeItem(key);
    } else {
      localStorage.setItem(key, value);
    }
  } catch (e) {
    console.warn('[Auth] localStorage not available:', e.message);
    return null;
  }
}

function getToken() {
  return safeStorage('stageMonitoringToken');
}

function setToken(token) {
  safeStorage('stageMonitoringToken', token || null);
}

function getCurrentUser() {
  const json = safeStorage('stageMonitoringUser');
  if (!json) return null;
  try {
    return JSON.parse(json);
  } catch {
    safeStorage('stageMonitoringUser', null);
    return null;
  }
}

function setCurrentUser(user) {
  safeStorage('stageMonitoringUser', user ? JSON.stringify(user) : null);
}

// 401 redirect guard — voorkomt meerdere redirects tegelijk
let _redirectingToLogin = false;

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
  
  const response = await fetch(url, config);
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
    
    // Handle auth errors
    if (response.status === 401) {
      if (!_redirectingToLogin) {
        _redirectingToLogin = true;
        setToken(null);
        setCurrentUser(null);
        window.location.href = 'index.html?view=login';
      }
      throw new Error('Sessie verlopen, opnieuw inloggen...');
    }
    
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }
  
  // Handle empty responses
  if (response.status === 204) {
    return null;
  }
  
  return response.json();
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
  
  register(userData) {
    return apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  },
  
  getMe() {
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
  list(status = null) {
    const params = status ? `?status=${encodeURIComponent(status)}` : '';
    return apiRequest(`/internships${params}`);
  },
  
  get(id) {
    return apiRequest(`/internships/${id}`);
  },
  
  create(data) {
    return apiRequest('/internships', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  uploadAgreement(id, file) {
    const formData = new FormData();
    formData.append('file', file);
    
    return apiRequest(`/internships/${id}/agreement`, {
      method: 'POST',
      body: formData
    });
  },
  
  getLogbooks(internshipId) {
    return apiRequest(`/internships/${internshipId}/logbooks`);
  },

  getLogbookWeeks(internshipId) {
    return apiRequest(`/internships/${internshipId}/logbooks/weeks`);
  },
  
  createLogbook(internshipId, data) {
    return apiRequest(`/internships/${internshipId}/logbooks`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  updateLogbook(logbookId, data) {
    return apiRequest(`/internships/logbooks/${logbookId}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  },
  
  getEvaluations(internshipId) {
    return apiRequest(`/internships/${internshipId}/evaluations`);
  },
  
  createEvaluation(internshipId, data) {
    return apiRequest(`/internships/${internshipId}/evaluations`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  getFeedback(internshipId) {
    return apiRequest(`/internships/${internshipId}/feedback`);
  },
  
  createFeedback(internshipId, data) {
    return apiRequest(`/internships/${internshipId}/feedback`, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  getDashboardStats() {
    return apiRequest('/internships/stats/dashboard');
  },

  getFinalReport(internshipId) {
    return apiRequest(`/internships/${internshipId}/final-report`);
  },

  submitLogbook(logbookId) {
    return apiRequest(`/internships/logbooks/${logbookId}/submit`, {
      method: 'POST'
    });
  }
};

// ============================================
// Competencies API
// ============================================

// ============================================
// Competency Profile API
// ============================================

const CompetencyProfileAPI = {
  list(activeOnly = false) {
    return apiRequest(`/competencies/profiles?active_only=${activeOnly}`);
  },

  create(data) {
    return apiRequest('/competencies/profiles', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  update(id, data) {
    return apiRequest(`/competencies/profiles/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  },

  delete(id) {
    return apiRequest(`/competencies/profiles/${id}`, {
      method: 'DELETE'
    });
  }
};

// ============================================
// Competencies API
// ============================================

const CompetenciesAPI = {
  list(profileId = null, activeOnly = true, search = null, skip = 0, limit = 50) {
    const params = new URLSearchParams();
    if (profileId) params.append('profile_id', String(profileId));
    params.append('active_only', String(activeOnly));
    if (search) params.append('search', search);
    params.append('skip', String(skip));
    params.append('limit', String(limit));
    return apiRequest(`/competencies?${params.toString()}`);
  },

  create(data) {
    return apiRequest('/competencies', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  createBulk(data) {
    return apiRequest('/competencies/bulk', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  update(id, data) {
    return apiRequest(`/competencies/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  },

  delete(id) {
    return apiRequest(`/competencies/${id}`, {
      method: 'DELETE'
    });
  },

  deactivate(id) {
    return apiRequest(`/competencies/${id}/deactivate`, {
      method: 'POST'
    });
  },

  checkWeights(profileId = null) {
    const params = new URLSearchParams();
    if (profileId) params.append('profile_id', String(profileId));
    return apiRequest(`/competencies/check-weights?${params.toString()}`);
  }
};

// ============================================
// Proposals
// ============================================

const ProposalsAPI = {
  review(internshipId, status, feedback = null) {
    const body = { status };
    if (feedback) body.feedback = feedback;
    return apiRequest(`/internships/${internshipId}/proposal`, {
      method: 'PATCH',
      body: JSON.stringify(body)
    });
  },

  edit(internshipId, data = {}) {
    return apiRequest(`/internships/${internshipId}/proposal/edit`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  },

  resubmit(internshipId, newDescription, extra = {}) {
    const body = { new_description: newDescription, ...extra };
    return apiRequest(`/internships/${internshipId}/resubmit`, {
      method: 'POST',
      body: JSON.stringify(body)
    });
  },

  withdraw(internshipId) {
    return apiRequest(`/internships/${internshipId}/proposal`, {
      method: 'DELETE'
    });
  }
};

// ============================================
// Evaluations
// ============================================

const EvaluationsAPI = {
  update(evaluationId, data) {
    return apiRequest(`/internships/evaluations/${evaluationId}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  }
};

// ============================================
// Evaluation Rules
// ============================================

const EvaluationRulesAPI = {
  update(evaluationId, ruleId, data) {
    return apiRequest(`/internships/evaluations/${evaluationId}/rules/${ruleId}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  }
};

// ============================================
// Agreements (validate)
// ============================================

async function downloadFile(url, filename) {
  const token = getToken();
  const response = await fetch(url, {
    headers: token ? { Authorization: `Bearer ${token}` } : {}
  });
  if (!response.ok) {
    throw new Error(`Download failed: ${response.status}`);
  }
  const blob = await response.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = blobUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(blobUrl);
}

const AgreementsAPI = {
  validate(internshipId, status, insuranceVerified = null) {
    const body = { status };
    if (insuranceVerified !== null) body.insurance_verified = insuranceVerified;
    return apiRequest(`/internships/${internshipId}/agreement`, {
      method: 'PATCH',
      body: JSON.stringify(body)
    });
  },

  download(internshipId) {
    const url = `${API_BASE_URL}/internships/${internshipId}/agreement/download`;
    return downloadFile(url, `stage_overeenkomst_${internshipId}.pdf`);
  }
};

// ============================================
// Reports API
// ============================================

const ReportsAPI = {
  listAgreements() {
    return apiRequest('/internships/reports/agreements');
  }
};

// ============================================
// Users API
// ============================================

const UsersAPI = {
  async list(role = null, search = null, activeOnly = true, skip = 0, limit = 50) {
    const params = new URLSearchParams();
    if (role) params.append('role', role);
    if (search) params.append('search', search);
    if (!activeOnly) params.append('active_only', 'false');
    params.append('skip', String(skip));
    params.append('limit', String(limit));
    return apiRequest(`/users?${params.toString()}`);
  },

  async get(id) {
    return apiRequest(`/users/${id}`);
  },

  async create(data) {
    return apiRequest('/users', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  async update(id, data) {
    return apiRequest(`/users/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  },

  async delete(id) {
    return apiRequest(`/users/${id}`, {
      method: 'DELETE'
    });
  }
};

// ============================================
// Audit Log API
// ============================================

const AuditAPI = {
  list(action = null, userEmail = null, entityType = null, skip = 0, limit = 50) {
    const params = new URLSearchParams();
    if (action) params.append('action', action);
    if (userEmail) params.append('user_email', userEmail);
    if (entityType) params.append('entity_type', entityType);
    params.append('skip', String(skip));
    params.append('limit', String(limit));
    return apiRequest(`/audit?${params.toString()}`);
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