// ============================================
// Stage Monitoring Tool - API Integrated Version
// Connects to the FastAPI backend
// ============================================

// View configuration
// Role values MUST match backend User.role values exactly
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
let allInternships = [];           // All internships visible to current user
let selectedInternshipId = null;   // User-selected internship (from URL param)
let currentCompetencies = [];
let currentLogbooks = [];
let currentEvaluations = [];
let currentFeedback = [];

// Convenience: get the internship the user has selected
function getSelectedInternship() {
  if (selectedInternshipId) {
    const found = allInternships.find(i => i.id == selectedInternshipId);
    if (found) return found;
  }
  return allInternships[0] || null;
}

// Back-compat alias — replace gradually
let currentInternship = null;

// ============================================
// Utility Functions
// ============================================

function formatDate(dateStr) {
  if (!dateStr) return '-';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('nl-BE', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return dateStr;
  }
}



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
    window.location.href = 'index.html';
  } catch (error) {
    hideLoading(submitBtn);
    showToast(error.message, 'error', 5000);
  }
}

function handleLogout() {
  AuthAPI.logout();
  showToast('Uitgelogd', 'info');
  window.location.href = 'index.html?view=login';
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
  if (viewParam && typeof viewParam === 'string' && views.includes(viewParam)) {
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
    // Resolve selected internship from URL param
    const urlParams = new URLSearchParams(window.location.search);
    const internshipParam = urlParams.get('internship');
    if (internshipParam) selectedInternshipId = parseInt(internshipParam);

    // Load ALL internships visible to this user
    allInternships = await InternshipsAPI.list();

    // Populate internship selector (for roles that see multiple)
    populateInternshipSelector(role);

    // Set current internship (back-compat)
    currentInternship = getSelectedInternship();

    // Load internship-specific data for the selected one
    if (currentInternship) {
      [currentLogbooks, currentEvaluations, currentFeedback] = await Promise.all([
        InternshipsAPI.getLogbooks(currentInternship.id),
        InternshipsAPI.getEvaluations(currentInternship.id),
        InternshipsAPI.getFeedback(currentInternship.id)
      ]);
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

// Populate the internship selector dropdown
function populateInternshipSelector(role) {
  const wrapper = document.getElementById('internship-selector-wrapper');
  const select = document.getElementById('internship-select');
  if (!wrapper || !select) return;

  // Only show selector for roles that might see multiple internships
  // (committee, teacher, mentor always see multiple; student might have resubmissions)
  const showSelector = allInternships.length > 1 || role !== 'student';

  if (!showSelector || allInternships.length === 0) {
    wrapper.style.display = 'none';
    return;
  }

  wrapper.style.display = 'block';
  select.innerHTML = '';

  allInternships.forEach(i => {
    const option = document.createElement('option');
    option.value = i.id;
    const label = i.student
      ? `${i.student.first_name} ${i.student.last_name} — ${i.company?.name || 'Onbekend'} (${i.status})`
      : `Stage ${i.id} — ${i.status}`;
    option.textContent = label;
    select.appendChild(option);
  });

  // Pre-select from URL param or first item
  const targetId = selectedInternshipId || allInternships[0]?.id;
  if (targetId) select.value = targetId;
}

// Handle internship selection change
function handleInternshipChange() {
  const select = document.getElementById('internship-select');
  if (!select) return;
  const newId = parseInt(select.value);
  if (newId === selectedInternshipId) return;

  selectedInternshipId = newId;
  currentInternship = getSelectedInternship();

  // Update URL without reloading page
  const url = new URL(window.location.href);
  url.searchParams.set('internship', newId);
  window.history.replaceState({}, '', url);

  // Re-render current view with new internship data
  renderView();
}

// Refresh internship data from API and update all references
async function refreshInternshipData() {
  try {
    allInternships = await InternshipsAPI.list();
    currentInternship = getSelectedInternship();

    // Update selector if visible
    const role = AuthAPI.getRole();
    populateInternshipSelector(role);

    if (currentInternship) {
      [currentLogbooks, currentEvaluations, currentFeedback] = await Promise.all([
        InternshipsAPI.getLogbooks(currentInternship.id),
        InternshipsAPI.getEvaluations(currentInternship.id),
        InternshipsAPI.getFeedback(currentInternship.id)
      ]);
    }
  } catch (error) {
    console.error('Failed to refresh internship data:', error);
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
    if (view === 'opvolging') {
      renderTeacherLogbooks();
    }
    if (view === 'evaluatie') {
      wireEvaluationForm();
    }
  }

  // MENTOR
  if (role === 'mentor') {
    if (view === 'validatie') {
      renderMentorLogbooks();
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
    const companyName = currentInternship.company?.name || 'Onbekend';
    const startDate = formatDate(currentInternship.start_date);
    const endDate = formatDate(currentInternship.end_date);
    const hasAgreement = currentInternship.agreement != null;

    hero.innerHTML = `
      <h2>Mijn Stage</h2>
      <p><strong>Bedrijf:</strong> ${companyName}</p>
      <p><strong>Periode:</strong> ${startDate} - ${endDate}</p>
      <p><strong>Status:</strong> <span class="status-pill status-${currentInternship.status.toLowerCase().replace(/\s+/g, '-')}">${currentInternship.status}</span></p>
      <p><strong>Overeenkomst:</strong> ${hasAgreement ? '✓ Ontvangen' : '✗ Nog niet'}</p>
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

  // Update feedback section
  const feedbackDiv = document.getElementById('student-feedback');
  if (feedbackDiv) {
    if (currentFeedback.length > 0) {
      feedbackDiv.innerHTML = currentFeedback.map(fb => `
        <div style="margin-bottom: 0.75rem; padding: 0.75rem; background: rgba(0,121,140,0.08); border-radius: 8px;">
          <p style="margin: 0 0 0.25rem 0;"><strong>${fb.from_user?.first_name || 'Onbekend'} ${fb.from_user?.last_name || ''}</strong> (${formatDate(fb.created_at)})</p>
          <p style="margin: 0; color: var(--ink-soft);">${fb.message}</p>
        </div>
      `).join('');
    } else {
      feedbackDiv.innerHTML = '<p class="hint">Je hebt nog geen feedback ontvangen.</p>';
    }
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
      company_address: document.getElementById('company-address').value || null,
      company_sector: document.getElementById('company-sector').value || null,
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
    const week = document.getElementById('log-week')?.value;

    showLoading(saveBtn, 'Opslaan...');

    try {
      await InternshipsAPI.createLogbook(currentInternship.id, {
        week_number: parseInt(week),
        tasks: document.getElementById('log-tasks').value,
        reflection: document.getElementById('log-reflection').value,
        issues: document.getElementById('log-issues').value,
        status: 'draft'
      });

      hideLoading(saveBtn);
      showToast('Logboek opgeslagen als concept', 'info');

      // Refresh data
      currentLogbooks = await InternshipsAPI.getLogbooks(currentInternship.id);
    } catch (error) {
      hideLoading(saveBtn);
      showToast(error.message, 'error');
    }
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
        issues: document.getElementById('log-issues').value,
        status: 'submitted'
      });

      hideLoading(submitBtn);
      showToast(`Logboek week ${week} ingediend!`, 'success');

      // Refresh data
      currentLogbooks = await InternshipsAPI.getLogbooks(currentInternship.id);
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

  // Check status - only allowed when proposal is approved (Goedgekeurd)
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

  // Check if agreement already exists (backend returns agreement object when present)
  const hasAgreement = currentInternship.agreement != null;

  // Update status display
  const statusText = document.getElementById('agreement-status-text');
  if (hasAgreement && statusText) {
    statusText.innerHTML = '<span class="status-approved">Ontvangen</span>';
    form.innerHTML = `
      <div class="info-message success">
        <p>✓ Je overeenkomst is succesvol geüpload!</p>
      </div>
    `;
    return;
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

      // Refresh internship data to reflect new agreement status
      await refreshInternshipData();

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
        <td>${ev.eval_type === 'tussentijds' ? 'Tussentijds' : ev.eval_type === 'final' ? 'Final' : ev.eval_type}</td>
        <td>${ev.finalized ? formatDate(ev.finalized_at) : '-'}</td>
        <td>${ev.finalized ? 'Afgerond' : 'In behandeling'}</td>
        <td>${ev.finalized ? '<button class="btn small">Bekijken</button>' : '-'}</td>
      </tr>
    `).join('');
  } else if (tbody) {
    tbody.innerHTML = '<tr><td colspan="4">Geen evaluaties gevonden</td></tr>';
  }
}

// ============================================
// Committee Views
// ============================================

async function renderCommitteeProposals() {
  try {
    const tbody = document.querySelector('#proposals-table tbody');

    if (tbody) {
      tbody.innerHTML = allInternships.map(p => `
        <tr data-id="${p.id}" class="proposal-row" style="cursor: pointer;">
          <td>${p.student?.first_name || 'Onbekend'} ${p.student?.last_name || ''}</td>
          <td>${p.company?.name || 'Onbekend'}</td>
          <td>${new Date(p.created_at).toLocaleDateString('nl-BE')}</td>
          <td><span class="status-pill status-${p.status.toLowerCase().replace(/\s+/g, '-')}">${p.status}</span></td>
          <td>${p.agreement_uploaded ? '<span class="status-approved">Ontvangen</span>' : '<span class="status-pending">Nog niet</span>'}</td>
        </tr>
      `).join('');

      // Click handler: select internship and show detail panel
      tbody.querySelectorAll('.proposal-row').forEach(row => {
        row.addEventListener('click', () => {
          const id = parseInt(row.dataset.id);
          selectProposalForReview(id);
        });
      });
    }

    // If a proposal is already selected via URL param, show its detail
    if (selectedInternshipId) {
      const preselected = allInternships.find(i => i.id == selectedInternshipId);
      if (preselected) selectProposalForReview(preselected.id);
    }

  } catch (error) {
    showToast(error.message, 'error');
  }
}

function selectProposalForReview(internshipId) {
  const internship = allInternships.find(i => i.id == internshipId);
  if (!internship) return;

  // Update URL
  selectedInternshipId = internshipId;
  currentInternship = internship;
  const url = new URL(window.location.href);
  url.searchParams.set('internship', internshipId);
  window.history.replaceState({}, '', url);

  // Highlight selected row
  document.querySelectorAll('.proposal-row').forEach(r => {
    r.style.background = r.dataset.id == internshipId ? 'rgba(0, 121, 140, 0.1)' : '';
  });

  // Show detail panel
  const panel = document.getElementById('proposal-detail-panel');
  if (panel) panel.style.display = 'block';

  // Fill detail info
  document.getElementById('selected-student-name').textContent =
    `${internship.student?.first_name || ''} ${internship.student?.last_name || ''}`;
  document.getElementById('selected-company').textContent = internship.company?.name || 'Onbekend';
  document.getElementById('selected-status').textContent = internship.status;

  // Fetch and show proposal description
  document.getElementById('selected-description').textContent = 'Laden...';
  InternshipsAPI.get(internship.id).then(full => {
    document.getElementById('selected-description').textContent =
      full.proposal?.description || 'Geen omschrijving beschikbaar.';
  }).catch(() => {
    document.getElementById('selected-description').textContent = 'Kon omschrijving niet laden.';
  });

  // Wire action buttons
  const actionsDiv = document.getElementById('review-actions');
  if (actionsDiv) {
    actionsDiv.innerHTML = `
      <button id="btn-approve" class="btn" style="background: linear-gradient(125deg, var(--good), #3c9d78);">✓ Goedkeuren</button>
      <button id="btn-reject" class="btn" style="background: linear-gradient(125deg, var(--bad), #ff6b6b);">✗ Afkeuren</button>
      <button id="btn-changes" class="btn alt">⚠ Aanpassingen Vereist</button>
    `;

    document.getElementById('btn-approve')?.addEventListener('click', () => doReview(internship.id, 'Goedgekeurd'));
    document.getElementById('btn-reject')?.addEventListener('click', () => doReview(internship.id, 'Afgekeurd'));
    document.getElementById('btn-changes')?.addEventListener('click', () => doReview(internship.id, 'Aanpassingen Vereist'));
  }
}

async function doReview(internshipId, decision) {
  const feedback = document.getElementById('feedback-box')?.value || null;

  if (decision === 'Aanpassingen Vereist' && !feedback) {
    showToast('Feedback is verplicht bij "Aanpassingen Vereist"', 'warning');
    return;
  }

  try {
    await ProposalsAPI.review(internshipId, decision, feedback);
    showToast(`Voorstel ${decision.toLowerCase()}!`, 'success');
    // Refresh data
    allInternships = await InternshipsAPI.list();
    renderCommitteeProposals();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function renderCommitteeOverview() {
  try {
    const stats = await InternshipsAPI.getDashboardStats();

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
      tbody.innerHTML = allInternships.map(p => `
        <tr>
          <td>${p.student?.first_name || 'Onbekend'}</td>
          <td>${p.company?.name || 'Onbekend'}</td>
          <td>${formatDate(p.start_date)} - ${formatDate(p.end_date)}</td>
          <td><span class="status-pill status-${p.status.toLowerCase().replace(/\s+/g, '-')}">${p.status}</span></td>
          <td>${p.agreement != null ? '<span class="status-approved">Ontvangen</span>' : '<span class="status-pending">Nog niet</span>'}</td>
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

  if (!currentInternship) {
    content.innerHTML = `
      <div class="panel card reveal">
        <h2>Geen stage geselecteerd</h2>
        <p>Selecteer eerst een stage via het navigatiemenu links.</p>
      </div>
    `;
    return;
  }

  // Fetch existing evaluations for this internship
  InternshipsAPI.getEvaluations(currentInternship.id).then(evaluations => {
    currentEvaluations = evaluations;

    // If there are existing draft evaluations, use the first one; otherwise create on save
    const existingEval = evaluations.find(e => !e.finalized);

    if (container && currentCompetencies.length > 0) {
      container.innerHTML = currentCompetencies.map(comp => {
        // Find rule for this competency if evaluation exists
        let rule = null;
        if (existingEval && existingEval.rules) {
          rule = existingEval.rules.find(r => r.competency_id === comp.id);
        }
        return `
          <div class="eval-row" data-comp-id="${comp.id}">
            <label>${comp.name} (${comp.weight}%)</label>
            <div class="score-inputs">
              <select class="score-select" data-comp="${comp.id}" ${existingEval?.finalized ? 'disabled' : ''}>
                <option value="1" ${rule?.score == 1 ? 'selected' : ''}>1 - Onvoldoende</option>
                <option value="2" ${rule?.score == 2 ? 'selected' : ''}>2 - Matig</option>
                <option value="3" ${rule?.score == 3 ? 'selected' : ''}>3 - Voldoende</option>
                <option value="4" ${rule?.score == 4 ? 'selected' : ''}>4 - Goed</option>
                <option value="5" ${rule?.score == 5 ? 'selected' : ''}>5 - Uitstekend</option>
              </select>
              <input type="text" class="feedback-input" placeholder="Feedback..." value="${rule?.evaluator_feedback || ''}" ${existingEval?.finalized ? 'disabled' : ''} />
            </div>
            <textarea class="student-desc-input" rows="2" placeholder="Student beschrijving..." ${existingEval?.finalized ? 'disabled' : ''}>${rule?.student_description || ''}</textarea>
          </div>
        `;
      }).join('');
    }
  }).catch(err => {
    console.error('Failed to load evaluations:', err);
  });

  const evalForm = document.getElementById('eval-form');
  const finalizeBtn = document.getElementById('finalize-eval');

  // Save scores (creates evaluation if needed, then updates each rule)
  evalForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = evalForm.querySelector('button[type="submit"]');
    const evalType = document.getElementById('eval-type')?.value || 'tussentijds';

    if (!currentInternship) {
      showToast('Geen stage geselecteerd', 'error');
      return;
    }

    showLoading(submitBtn, 'Opslaan...');

    try {
      // Step 1: Create evaluation (if no existing draft)
      let evaluation = currentEvaluations.find(e => !e.finalized && e.eval_type === evalType);
      if (!evaluation) {
        evaluation = await InternshipsAPI.createEvaluation(currentInternship.id, {
          eval_type: evalType
        });
        currentEvaluations.push(evaluation);
      }

      // Step 2: Update each rule with score, feedback, and student description
      const rows = container.querySelectorAll('.eval-row');
      for (const row of rows) {
        const compId = parseInt(row.dataset.compId);
        const score = parseInt(row.querySelector('.score-select')?.value);
        const feedback = row.querySelector('.feedback-input')?.value || null;
        const studentDesc = row.querySelector('.student-desc-input')?.value || null;

        // Find the rule ID for this competency
        const rule = evaluation.rules?.find(r => r.competency_id === compId);
        if (rule) {
          await EvaluationRulesAPI.update(evaluation.id, rule.id, {
            score,
            evaluator_feedback: feedback,
            student_description: studentDesc
          });
        }
      }

      hideLoading(submitBtn);
      showToast('Evaluatie opgeslagen!', 'success');
    } catch (error) {
      hideLoading(submitBtn);
      showToast(error.message, 'error');
    }
  });

  // Finalize evaluation
  finalizeBtn?.addEventListener('click', async () => {
    if (!confirm('Evaluatie definitief afsluiten? Dit kan niet ongedaan gemaakt worden.')) return;

    if (!currentInternship) {
      showToast('Geen stage geselecteerd', 'error');
      return;
    }

    // First save current scores
    const submitBtn = evalForm.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.click();

    // Then find the evaluation and finalize it
    const evalType = document.getElementById('eval-type')?.value || 'tussentijds';
    const evaluation = currentEvaluations.find(e => !e.finalized && e.eval_type === evalType);

    if (!evaluation) {
      showToast('Geen evaluatie gevonden om af te sluiten', 'error');
      return;
    }

    showLoading(finalizeBtn, 'Bezig...');

    try {
      // The backend finalize endpoint is POST /evaluations/{id}/finalize
      await apiRequest(`/evaluations/${evaluation.id}/finalize`, { method: 'POST' });
      hideLoading(finalizeBtn);
      showToast('Evaluatie definitief afgesloten!', 'success');
    } catch (error) {
      hideLoading(finalizeBtn);
      showToast(error.message, 'error');
    }
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

// ============================================
// Teacher & Mentor Logbook Views
// ============================================

function renderTeacherLogbooks() {
  const tbody = document.querySelector('#teacher-logbooks-table tbody');
  if (!tbody) return;

  if (!currentInternship) {
    tbody.innerHTML = '<tr><td colspan="5">Selecteer een stage via het navigatiemenu.</td></tr>';
    return;
  }

  if (currentLogbooks.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5">Geen logboeken gevonden voor deze stage.</td></tr>';
    return;
  }

  tbody.innerHTML = currentLogbooks.map(lb => `
    <tr>
      <td>${lb.week_number}</td>
      <td>${lb.tasks || '-'}</td>
      <td>${lb.reflection || '-'}</td>
      <td><span class="status-pill status-${lb.status}">${lb.status === 'submitted' ? 'Ingediend' : 'Concept'}</span></td>
      <td>${lb.mentor_validated ? '✓ Gevalideerd' : 'In afwachting'}</td>
    </tr>
  `).join('');

  // Wire feedback button
  const sendBtn = document.getElementById('teacher-send-feedback');
  sendBtn?.addEventListener('click', async () => {
    const msg = document.getElementById('teacher-feedback-msg')?.value;
    if (!msg) {
      showToast('Geen feedback ingevuld', 'warning');
      return;
    }
    if (!currentInternship) {
      showToast('Geen stage geselecteerd', 'error');
      return;
    }
    try {
      await InternshipsAPI.createFeedback(currentInternship.id, {
        message: msg,
        to_user_id: currentInternship.student_id
      });
      showToast('Feedback verstuurd!', 'success');
      document.getElementById('teacher-feedback-msg').value = '';
    } catch (error) {
      showToast(error.message, 'error');
    }
  });
}

function renderMentorLogbooks() {
  const tbody = document.querySelector('#mentor-logbooks-table tbody');
  if (!tbody) return;

  if (!currentInternship) {
    tbody.innerHTML = '<tr><td colspan="5">Selecteer een stage via het navigatiemenu.</td></tr>';
    return;
  }

  if (currentLogbooks.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5">Geen logboeken gevonden voor deze stage.</td></tr>';
    return;
  }

  tbody.innerHTML = currentLogbooks.map(lb => `
    <tr data-logbook-id="${lb.id}">
      <td>${lb.week_number}</td>
      <td>${lb.tasks || '-'}</td>
      <td>${lb.reflection || '-'}</td>
      <td><span class="status-pill status-${lb.status}">${lb.status === 'submitted' ? 'Ingediend' : 'Concept'}</span></td>
      <td>
        ${lb.mentor_validated
          ? '<span class="status-approved">✓ Gevalideerd</span>'
          : `<button class="btn small validate-logbook-btn" data-id="${lb.id}">Valideren</button>`
        }
      </td>
    </tr>
  `).join('');

  // Wire validate buttons
  tbody.querySelectorAll('.validate-logbook-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const logbookId = parseInt(btn.dataset.id);
      showLoading(btn, 'Bezig...');
      try {
        await apiRequest(`/internships/logbooks/${logbookId}`, {
          method: 'PATCH',
          body: JSON.stringify({ mentor_validated: true })
        });
        hideLoading(btn);
        showToast('Logboek gevalideerd!', 'success');
        // Refresh logbooks
        currentLogbooks = await InternshipsAPI.getLogbooks(currentInternship.id);
        renderMentorLogbooks();
      } catch (error) {
        hideLoading(btn);
        showToast(error.message, 'error');
      }
    });
  });
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
window.selectProposalForReview = selectProposalForReview;
window.doReview = doReview;

// ============================================
// Initialization
// ============================================

function init() {
  const urlParams = new URLSearchParams(window.location.search);
  const view = urlParams.get('view');
  const internshipParam = urlParams.get('internship');
  if (internshipParam) selectedInternshipId = parseInt(internshipParam);
  
  if (view === 'login' || !AuthAPI.isLoggedIn()) {
    renderLogin();
  } else {
    updateUIForUser(AuthAPI.getUser());
    renderMainApp();
  }
  
  // Event listeners
  document.getElementById('view-select')?.addEventListener('change', () => {
    renderView();
  });
  
  document.getElementById('internship-select')?.addEventListener('change', handleInternshipChange);
  
  document.getElementById('logout-btn')?.addEventListener('click', handleLogout);
}

// Start
init();