const API_BASE_URL = '/api';

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
  } catch {
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

let _redirectingToLogin = false;

function formatError(error) {
  if (Array.isArray(error.detail)) {
    return error.detail.map(d => d.msg || String(d)).join(', ');
  }
  if (typeof error.detail === 'string') return error.detail;
  if (typeof error.detail === 'object' && error.detail !== null) {
    return JSON.stringify(error.detail);
  }
  return JSON.stringify(error);
}

async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  };

  const token = getToken();
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }

  if (options.body instanceof FormData) {
    delete config.headers['Content-Type'];
  }

  let response;
  try {
    response = await fetch(url, config);
  } catch {
    throw new Error('Kan geen verbinding maken met de server. Controleer je internetverbinding of probeer het later opnieuw.');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));

    if (response.status === 401) {
      if (!_redirectingToLogin) {
        _redirectingToLogin = true;
        setToken(null);
        setCurrentUser(null);
        window.location.href = 'index.html?view=login';
      }
      throw new Error('Sessie verlopen, opnieuw inloggen...');
    }

    throw new Error(formatError(error) || `HTTP error! status: ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

async function _postAuth(url, body, headers) {
  let response;
  try {
    response = await fetch(url, { method: 'POST', headers, body });
  } catch {
    throw new Error('Kan geen verbinding maken met de server. Is de backend gestart?');
  }

  if (!response.ok) {
    let errorText;
    try {
      errorText = formatError(await response.json());
    } catch {
      errorText = `HTTP ${response.status} - ${response.statusText}`;
    }
    throw new Error(errorText);
  }

  const data = await response.json();
  setToken(data.access_token);
  setCurrentUser(data.user);
  return data;
}

const AuthAPI = {
  login(email, password) {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    return _postAuth(`${API_BASE_URL}/auth/login`, formData, {
      'Content-Type': 'application/x-www-form-urlencoded'
    });
  },

  demoLogin(email) {
    return _postAuth(`${API_BASE_URL}/auth/demo-login`, JSON.stringify({ email }), {
      'Content-Type': 'application/json'
    });
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

const InternshipsAPI = {
  list(status = null, skip = 0, limit = 50) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('skip', String(skip));
    params.append('limit', String(limit));
    return apiRequest(`/internships?${params.toString()}`);
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

  getLogbookDays(internshipId) {
    return apiRequest(`/internships/${internshipId}/logbooks/days`);
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

  downloadFinalReport(internshipId) {
    return downloadFile(`${API_BASE_URL}/internships/${internshipId}/final-report/pdf`);
  },

  async exportPdf(internshipId, studentName) {
    const url = `${API_BASE_URL}/internships/${internshipId}/final-report/pdf`;
    const filename = `stage_rapport_${(studentName || 'student').replace(/\s+/g, '_').toLowerCase()}_${internshipId}.pdf`;
    return downloadFile(url, filename);
  },
  submitLogbook(logbookId) {
    return apiRequest(`/internships/logbooks/${logbookId}/submit`, {
      method: 'POST'
    });
  }
};

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

const ProposalsAPI = {
  review(internshipId, status, feedback = null, teacherId = null, mentorId = null) {
    const body = { status };
    if (feedback) body.feedback = feedback;
    if (teacherId) body.teacher_id = teacherId;
    if (mentorId) body.mentor_id = mentorId;
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

const EvaluationsAPI = {
  update(evaluationId, data) {
    return apiRequest(`/internships/evaluations/${evaluationId}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  }
};

const EvaluationRulesAPI = {
  update(evaluationId, ruleId, data) {
    return apiRequest(`/internships/evaluations/${evaluationId}/rules/${ruleId}`, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  }
};

async function downloadFile(url, fallbackFilename = null) {
  const response = await fetch(url, {
    headers: getToken() ? { Authorization: `Bearer ${getToken()}` } : {}
  });
  if (!response.ok) {
    throw new Error(`Download failed: ${response.status}`);
  }

  const disposition = response.headers.get('content-disposition');
  const filename = disposition?.match(/filename="?([^"]+)"?/)?.[1]
    || fallbackFilename || 'download';

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

const ReportsAPI = {
  listAgreements() {
    return apiRequest('/internships/reports/agreements');
  },

  exportCsv() {
    const url = `${API_BASE_URL}/internships/reports/export/csv`;
    return downloadFile(url, `stage_export_${new Date().toISOString().slice(0, 10)}.csv`);
  },

  exportExcel() {
    const url = `${API_BASE_URL}/internships/reports/export/excel`;
    return downloadFile(url, `stage_export_${new Date().toISOString().slice(0, 10)}.xlsx`);
  }
};

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
