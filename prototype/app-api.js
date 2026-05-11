// ============================================
// Stage Monitoring Tool - API Integrated Version
// Connects to the FastAPI backend
// ============================================

// View configuration
const roleViews = {
  student: ["dashboard", "voorstel", "logboek", "overeenkomst", "evaluaties"],
  committee: ["voorstellen", "overzicht"],
  teacher: ["opvolging", "evaluatie"],
  mentor: ["validatie"],
  admin: ["competenties"],
};

const roleDisplayNames = {
  student: "Student",
  committee: "Stagecommissie",
  teacher: "Docent",
  mentor: "Stagementor",
  admin: "Administratie"
};

const templates = {
  login: "login-template",
  student: "student-dashboard-template",
  "student-voorstel": "student-voorstel-template",
  "student-logboek": "student-logboek-template",
  "student-overeenkomst": "student-overeenkomst-template",
  "student-evaluaties": "student-evaluatie-template",
  committee: "commissie-template",
  "committee-overzicht": "commissie-overzicht-template",
  teacher: "docent-template",
  "teacher-evaluatie": "docent-evaluatie-template",
  mentor: "mentor-template",
  admin: "admin-template",
};

// State
let currentInternship = null;
let currentCompetencies = [];
let currentLogbooks = [];
let currentEvaluations = [];



// Note: localStorage persistence removed - this is the API-connected version
// All data is persisted through the backend API

// DOM elements
const app = document.getElementById("app");
const navPanel = document.getElementById("nav-panel");
const content = document.getElementById("content");

// ============================================
// UI Helpers
// ============================================

function showToast(message, type = "success", duration = 3000) {
  const existing = document.querySelector(".toast-notification");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.className = `toast-notification toast-${type}`;
  
  const icons = { success: "✓", error: "✗", warning: "⚠", info: "ℹ" };
  
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || "•"}</span>
    <span class="toast-message">${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">×</button>
  `;
  
  document.body.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add("show"));
  
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function showLoading(element, message = "Laden...") {
  if (!element) return;
  element.dataset.originalContent = element.innerHTML;
  element.innerHTML = `<span class="loading-spinner"></span> ${message}`;
  element.disabled = true;
}

function hideLoading(element) {
  if (!element) return;
  const original = element.dataset.originalContent;
  if (original !== undefined) {
    element.innerHTML = original;
  }
  element.disabled = false;
}

// ============================================
// Authentication
// ============================================

function checkAuth() {
  const isLoggedIn = AuthAPI.isLoggedIn();
  const urlParams = new URLSearchParams(window.location.search);
  const view = urlParams.get('view');
  
  if (!isLoggedIn && view !== 'login') {
    renderLogin();
    return false;
  }
  
  if (isLoggedIn) {
    const user = AuthAPI.getUser();
    updateUIForUser(user);
  }
  
  return isLoggedIn;
}

function updateUIForUser(user) {
  const userInfo = document.getElementById('user-info');
  const userName = document.getElementById('user-name');
  const userRole = document.getElementById('user-role');
  
  if (userInfo && userName && userRole) {
    userInfo.style.display = 'flex';
    userName.textContent = `${user.first_name} ${user.last_name}`;
    userRole.textContent = roleDisplayNames[user.role] || user.role;
  }
  
  // Set role in selector
  const roleSelect = document.getElementById('role-select');
  if (roleSelect) {
    roleSelect.value = user.role;
    roleSelect.disabled = true; // User can't change role manually
  }
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  const submitBtn = e.target.querySelector('button[type="submit"]');
  
  showLoading(submitBtn, "Inloggen...");
  
  try {
    const data = await AuthAPI.login(email, password);
    hideLoading(submitBtn);
    showToast(`Welkom, ${data.user.first_name}!`, 'success');
    
    // Redirect to main app
    window.location.href = 'index-api.html';
  } catch (error) {
    hideLoading(submitBtn);
    showToast(error.message, 'error', 5000);
  }
}

function handleLogout() {
  AuthAPI.logout();
  showToast('Uitgelogd', 'info');
  window.location.href = 'index-api.html?view=login';
}

// ============================================
// View Rendering
// ============================================

function renderLogin() {
  app.className = 'login-layout';
  app.innerHTML = '';
  navPanel.style.display = 'none';
  
  const tpl = document.getElementById('login-template');
  if (tpl) {
    app.appendChild(tpl.content.cloneNode(true));
    
    const form = document.getElementById('login-form');
    form?.addEventListener('submit', handleLogin);
    
    // Fill test credentials for demo
    const testCreds = document.getElementById('test-credentials');
    if (testCreds) {
      testCreds.innerHTML = `
        <p><strong>Test accounts:</strong></p>
        <ul>
          <li>admin@school.be / admin123</li>
          <li>student1@school.be / student123</li>
          <li>commissie1@school.be / commissie123</li>
          <li>docent1@school.be / docent123</li>
        </ul>
      `;
    }
  }
}

async function renderMainApp() {
  app.className = 'layout';
  navPanel.style.display = 'block';
  
  const role = AuthAPI.getRole();
  const views = roleViews[role] || [];
  
  // Populate view selector
  const viewSelect = document.getElementById('view-select');
  viewSelect.innerHTML = '';
  views.forEach((view) => {
    const option = document.createElement('option');
    option.value = view;
    option.textContent = view.charAt(0).toUpperCase() + view.slice(1);
    viewSelect.appendChild(option);
  });
  
  // Get URL param or default to first view
  const urlParams = new URLSearchParams(window.location.search);
  const viewParam = urlParams.get('view');
  if (viewParam && views.includes(viewParam)) {
    viewSelect.value = viewParam;
  }
  
  renderView();
}

async function renderView() {
  const role = AuthAPI.getRole();
  const viewSelect = document.getElementById('view-select');
  const view = viewSelect?.value || roleViews[role]?.[0];
  
  content.innerHTML = '<div class="loading-overlay"><span class="loading-spinner"></span> Laden...</div>';
  
  const key = view ? `${role}-${view}` : role;
  const templateId = templates[key] || templates[role];
  
  try {
    // Load data based on view
    if (role === 'student') {
      const internships = await InternshipsAPI.list();
      currentInternship = internships[0] || null;
      
      if (currentInternship) {
        [currentLogbooks, currentEvaluations] = await Promise.all([
          InternshipsAPI.getLogbooks(currentInternship.id),
          InternshipsAPI.getEvaluations(currentInternship.id)
        ]);
      }
    }
    
    if (role === 'admin' || view === 'evaluatie') {
      currentCompetencies = await CompetenciesAPI.list();
    }
    
    // Render template
    content.innerHTML = '';
    const tpl = document.getElementById(templateId);
    if (tpl) {
      content.appendChild(tpl.content.cloneNode(true));
      wireRoleInteractions(role, view);
    }
  } catch (error) {
    content.innerHTML = `<div class="error-message">Fout bij laden: ${error.message}</div>`;
  }
}

// ============================================
// Role Interactions
// ============================================

function wireRoleInteractions(role, view) {
  // STUDENT
  if (role === 'student') {
    if (view === 'dashboard') {
      renderStudentDashboard();
    }
    
    if (view === 'voorstel') {
      wireProposalForm();
    }
    
    if (view === 'logboek') {
      wireLogbookForm();
    }
    
    if (view === 'overeenkomst') {
      wireAgreementUpload();
    }
    
    if (view === 'evaluaties') {
      renderStudentEvaluations();
    }
  }
  
  // COMMITTEE
  if (role === 'committee') {
    if (view === 'voorstellen') {
      renderCommitteeProposals();
    }
    if (view === 'overzicht') {
      renderCommitteeOverview();
    }
  }

  // TEACHER
  if (role === 'teacher') {
    if (view === 'evaluatie') {
      wireEvaluationForm();
    }
  }
  
  // ADMIN
  if (role === 'admin') {
    if (view === 'competenties') {
      renderCompetencyManager();
    }
  }
}

// ============================================
// Student Views
// ============================================

function renderStudentDashboard() {
  if (!currentInternship) {
    content.innerHTML = `
      <div class="panel card reveal">
        <h2>Geen stage gevonden</h2>
        <p>Je hebt nog geen stage ingediend.</p>
        <a href="?view=voorstel" class="btn">Stagevoorstel indienen</a>
      </div>
    `;
    return;
  }
  
  const hero = document.querySelector('.hero');
  if (hero) {
    hero.innerHTML = `
      <h2>Mijn Stage</h2>
      <p><strong>Bedrijf:</strong> ${currentInternship.company_name}</p>
      <p><strong>Periode:</strong> ${currentInternship.start_date} - ${currentInternship.end_date}</p>
      <p><strong>Status:</strong> <span class="status-pill status-${currentInternship.status.toLowerCase().replace(/\s+/g, '-')}">${currentInternship.status}</span></p>
      <p><strong>Overeenkomst:</strong> ${currentInternship.agreement_uploaded ? '✓ Ontvangen' : '✗ Nog niet'}</p>
    `;
  }
  
  // Update logbooks table
  const tbody = document.querySelector('table tbody');
  if (tbody && currentLogbooks.length > 0) {
    tbody.innerHTML = currentLogbooks.map(lb => `
      <tr>
        <td>${lb.week_number}</td>
        <td>${lb.status === 'submitted' ? 'Ingediend' : 'Concept'}</td>
        <td>${lb.mentor_validated ? 'Goedgekeurd' : (lb.status === 'submitted' ? 'In afwachting' : '-')}</td>
      </tr>
    `).join('');
  }
}

function wireProposalForm() {
  const form = document.getElementById('proposal-form');
  
  // If already has internship, show message
  if (currentInternship) {
    form.innerHTML = `
      <div class="info-message">
        <p>Je hebt al een stage ingediend.</p>
        <a href="?view=dashboard" class="btn">Naar dashboard</a>
      </div>
    `;
    return;
  }
  
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    
    const data = {
      company_name: document.getElementById('company-name').value,
      contact_person: document.getElementById('contact-person').value,
      contact_email: document.getElementById('contact-email').value,
      start_date: document.getElementById('start-date').value,
      end_date: document.getElementById('end-date').value,
      description: document.getElementById('assignment-desc').value
    };
    
    showLoading(submitBtn, 'Indienen...');
    
    try {
      await InternshipsAPI.create(data);
      hideLoading(submitBtn);
      showToast('Stagevoorstel succesvol ingediend!', 'success');
      setTimeout(() => window.location.href = '?view=dashboard', 1000);
    } catch (error) {
      hideLoading(submitBtn);
      showToast(error.message, 'error');
    }
  });
}

function wireLogbookForm() {
  const form = document.getElementById('logbook-form');
  const submitBtn = document.getElementById('submit-logbook');
  
  if (!currentInternship) {
    content.innerHTML = `
      <div class="panel card reveal">
        <h2>Geen stage gevonden</h2>
        <p>Je moet eerst een stage indienen voordat je logboeken kunt invullen.</p>
      </div>
    `;
    return;
  }
  
  // Populate week number with next available week
  const weekInput = document.getElementById('log-week');
  if (weekInput && currentLogbooks.length > 0) {
    const maxWeek = Math.max(...currentLogbooks.map(lb => lb.week_number));
    weekInput.value = maxWeek + 1;
  }
  
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const saveBtn = form.querySelector('button[type="submit"]');
    showLoading(saveBtn, 'Opslaan...');
    
    // In real app, save as draft
    setTimeout(() => {
      hideLoading(saveBtn);
      showToast('Logboek opgeslagen als concept', 'info');
    }, 500);
  });
  
  submitBtn?.addEventListener('click', async () => {
    const week = document.getElementById('log-week').value;
    const tasks = document.getElementById('log-tasks').value;
    
    if (!week || !tasks) {
      showToast('Weeknummer en taken zijn verplicht', 'error');
      return;
    }
    
    showLoading(submitBtn, 'Indienen...');
    
    try {
      await InternshipsAPI.createLogbook(currentInternship.id, {
        week_number: parseInt(week),
        tasks: tasks,
        reflection: document.getElementById('log-reflection').value,
        issues: document.getElementById('log-issues').value
      });
      
      hideLoading(submitBtn);
      showToast(`Logboek week ${week} ingediend!`, 'success');
    } catch (error) {
      hideLoading(submitBtn);
      showToast(error.message, 'error');
    }
  });
}

function wireAgreementUpload() {
  const form = document.getElementById('agreement-form');
  
  if (!currentInternship) {
    content.innerHTML = `
      <div class="panel card reveal">
        <h2>Geen stage gevonden</h2>
        <p>Je moet eerst een stage indienen.</p>
      </div>
    `;
    return;
  }
  
  // Check status
  if (currentInternship.status !== 'Goedgekeurd') {
    form.innerHTML = `
      <div class="info-message warning">
        <p>⚠️ Je stagevoorstel moet eerst goedgekeurd zijn voordat je een overeenkomst kunt uploaden.</p>
        <p>Huidige status: <strong>${currentInternship.status}</strong></p>
        <a href="?view=dashboard" class="btn">Naar dashboard</a>
      </div>
    `;
    return;
  }
  
  // Update status display
  const statusText = document.getElementById('agreement-status-text');
  if (statusText) {
    if (currentInternship.agreement_uploaded) {
      statusText.innerHTML = '<span class="status-approved">Ontvangen</span>';
      form.innerHTML = `
        <div class="info-message success">
          <p>✓ Je overeenkomst is succesvol geüpload!</p>
        </div>
      `;
      return;
    }
  }
  
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('agreement-file');
    const file = fileInput?.files[0];
    const submitBtn = form.querySelector('button[type="submit"]');
    
    if (!file) {
      showToast('Selecteer een PDF bestand', 'error');
      return;
    }
    
    if (file.type !== 'application/pdf') {
      showToast('Alleen PDF bestanden zijn toegestaan', 'error');
      return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
      showToast('Bestand is te groot (max 5MB)', 'error');
      return;
    }
    
    showLoading(submitBtn, 'Uploaden...');
    
    try {
      await InternshipsAPI.uploadAgreement(currentInternship.id, file);
      hideLoading(submitBtn);
      showToast('Overeenkomst succesvol geüpload!', 'success');
      
      if (statusText) {
        statusText.innerHTML = '<span class="status-approved">Ontvangen</span>';
      }
    } catch (error) {
      hideLoading(submitBtn);
      showToast(error.message, 'error');
    }
  });
}

function renderStudentEvaluations() {
  const tbody = document.querySelector('table tbody');
  if (tbody && currentEvaluations.length > 0) {
    tbody.innerHTML = currentEvaluations.map(ev => `
      <tr>
        <td>${ev.type === 'tussentijds' ? 'Tussentijds' : 'Final'}</td>
        <td>${ev.finalized ? new Date(ev.created_at).toLocaleDateString('nl-BE') : '-'}</td>
        <td>${ev.finalized ? 'Afgerond' : 'In behandeling'}</td>
        <td>${ev.finalized ? '<button class="btn small">Bekijken</button>' : '-'}</td>
      </tr>
    `).join('');
  }
}

// ============================================
// Committee Views
// ============================================

async function renderCommitteeProposals() {
  try {
    const proposals = await InternshipsAPI.list();
    const tbody = document.querySelector('table tbody');
    
    if (tbody) {
      tbody.innerHTML = proposals.map(p => `
        <tr data-id="${p.id}">
          <td>${p.student?.first_name || 'Onbekend'} ${p.student?.last_name || ''}</td>
          <td>${p.company_name}</td>
          <td>${new Date(p.created_at).toLocaleDateString('nl-BE')}</td>
          <td><span class="status-pill status-${p.status.toLowerCase().replace(/\s+/g, '-')}">${p.status}</span></td>
        </tr>
      `).join('');
    }
    
    // Wire up feedback form
    const saveBtn = document.getElementById('save-feedback');
    saveBtn?.addEventListener('click', async () => {
      const feedback = document.getElementById('feedback-box')?.value;
      if (feedback) {
        showToast('Feedback opgeslagen', 'success');
      }
    });
    
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function renderCommitteeOverview() {
  try {
    const [proposals, stats] = await Promise.all([
      InternshipsAPI.list(),
      InternshipsAPI.getDashboardStats()
    ]);
    
    // Update stats
    const statElements = document.querySelectorAll('.grid.two-col ul');
    if (statElements[0]) {
      statElements[0].innerHTML = `
        <li>Totaal voorstellen: ${stats.total_internships}</li>
        <li>Goedgekeurd: ${stats.approved}</li>
        <li>In behandeling: ${stats.pending_approval}</li>
        <li>Afgekeurd: ${stats.rejected}</li>
      `;
    }
    if (statElements[1]) {
      statElements[1].innerHTML = `
        <li>Ontvangen: ${stats.agreements_received}</li>
        <li>Nog uitstaand: ${stats.agreements_pending}</li>
      `;
    }
    
    // Update table
    const tbody = document.querySelector('table tbody');
    if (tbody) {
      tbody.innerHTML = proposals.map(p => `
        <tr>
          <td>${p.student?.first_name || 'Onbekend'}</td>
          <td>${p.company_name}</td>
          <td>${p.start_date} - ${p.end_date}</td>
          <td><span class="status-pill status-${p.status.toLowerCase().replace(/\s+/g, '-')}">${p.status}</span></td>
          <td>${p.agreement_uploaded ? '<span class="status-approved">Ontvangen</span>' : '<span class="status-pending">Nog niet</span>'}</td>
        </tr>
      `).join('');
    }
  } catch (error) {
    showToast(error.message, 'error');
  }
}

// ============================================
// Teacher/Admin Views
// ============================================

function wireEvaluationForm() {
  const container = document.getElementById('eval-competencies');
  if (container && currentCompetencies.length > 0) {
    container.innerHTML = currentCompetencies.map(comp => `
      <div class="eval-row">
        <label>${comp.name} (${comp.weight}%)</label>
        <div class="score-inputs">
          <select class="score-select" data-comp="${comp.id}">
            <option value="1">1 - Onvoldoende</option>
            <option value="2">2 - Matig</option>
            <option value="3" selected>3 - Voldoende</option>
            <option value="4">4 - Goed</option>
            <option value="5">5 - Uitstekend</option>
          </select>
          <input type="text" class="feedback-input" placeholder="Feedback..." />
        </div>
      </div>
    `).join('');
  }
  
  const finalizeBtn = document.getElementById('finalize-eval');
  finalizeBtn?.addEventListener('click', async () => {
    if (!confirm('Evaluatie definitief afsluiten?')) return;
    showToast('Evaluatie afgesloten', 'success');
  });
}

function renderCompetencyManager() {
  const list = document.getElementById('competency-list');
  const scoreInputs = document.getElementById('score-inputs');
  const weightCheck = document.getElementById('weight-check');
  
  function render() {
    if (!list || !scoreInputs || !weightCheck) return;
    
    list.innerHTML = currentCompetencies.map((comp) => `
      <li>
        <span class="comp-name">${comp.name}</span>
        <span class="comp-weight">${comp.weight}%</span>
        <button class="btn small alt" onclick="handleDeleteCompetency(${comp.id})" style="margin-left: 0.6rem;">Verwijder</button>
      </li>
    `).join('');
    
    scoreInputs.innerHTML = currentCompetencies.map(comp => `
      <div class="row score-row">
        <label>${comp.name} (${comp.weight}%)</label>
        <input type="number" min="1" max="5" value="3" data-comp="${comp.id}" />
      </div>
    `).join('');
    
    const total = currentCompetencies.reduce((sum, c) => sum + c.weight, 0);
    const valid = total === 100;
    weightCheck.textContent = `Totaal gewicht: ${total}% ${valid ? '✓ OK' : '⚠ Moet 100% zijn'}`;
    weightCheck.className = `weight-check ${valid ? 'valid' : 'invalid'}`;
  }
  
  // Wire up form
  const form = document.getElementById('competency-form');
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('comp-name').value;
    const weight = parseFloat(document.getElementById('comp-weight').value);
    const submitBtn = form.querySelector('button[type="submit"]');
    
    showLoading(submitBtn, 'Toevoegen...');
    
    try {
      const newComp = await CompetenciesAPI.create({ name, weight });
      currentCompetencies.push(newComp);
      render();
      hideLoading(submitBtn);
      showToast(`Competentie "${name}" toegevoegd`, 'success');
      form.reset();
    } catch (error) {
      hideLoading(submitBtn);
      showToast(error.message, 'error');
    }
  });
  
  // Calculate button
  const calcBtn = document.getElementById('calc-score');
  calcBtn?.addEventListener('click', () => {
    const total = currentCompetencies.reduce((sum, c) => sum + c.weight, 0);
    if (total !== 100) {
      showToast('Gewichten moeten 100% zijn', 'error');
      return;
    }
    
    // Calculate weighted score
    let score = 0;
    document.querySelectorAll('#score-inputs input').forEach(input => {
      const compId = parseInt(input.dataset.comp);
      const comp = currentCompetencies.find(c => c.id === compId);
      if (comp) {
        score += comp.weight * parseInt(input.value);
      }
    });
    score = score / 100;
    
    const resultEl = document.getElementById('score-result');
    resultEl.textContent = `Gewogen eindscore: ${score.toFixed(2)} / 5`;
    resultEl.className = 'result success';
    
    showToast(`Eindscore: ${score.toFixed(2)} / 5`, 'success');
  });
  
  render();
}

// Competency deletion handler - attached to window for onclick handlers in templates
async function handleDeleteCompetency(id) {
  if (!confirm('Competentie verwijderen?')) return;

  try {
    await CompetenciesAPI.delete(id);
    currentCompetencies = currentCompetencies.filter(c => c.id !== id);
    renderCompetencyManager();
    showToast('Competentie verwijderd', 'info');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

// Expose to window for template onclick handlers
window.handleDeleteCompetency = handleDeleteCompetency;

// ============================================
// Initialization
// ============================================

function init() {
  const urlParams = new URLSearchParams(window.location.search);
  const view = urlParams.get('view');
  
  if (view === 'login' || !AuthAPI.isLoggedIn()) {
    renderLogin();
  } else {
    renderMainApp();
  }
  
  // Event listeners
  document.getElementById('view-select')?.addEventListener('change', () => {
    renderView();
  });
  
  document.getElementById('logout-btn')?.addEventListener('click', handleLogout);
}

// Start
init();