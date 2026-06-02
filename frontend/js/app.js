// Stage Monitoring Tool

// Configuratie
// Role waarden moeten overeenkomen met backend User.role
const roleViews = {
  student: ["dashboard", "voorstel", "logboek", "overeenkomst", "evaluaties"],
  committee: ["voorstellen", "overeenkomsten", "overzicht"],
  teacher: ["opvolging", "evaluatie", "eindoverzicht"],
  mentor: ["validatie", "evaluatie"],
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
  "committee-overeenkomsten": "commissie-overeenkomsten-template",
  "committee-overzicht": "commissie-overzicht-template",
  teacher: "docent-template",
  "teacher-evaluatie": "docent-evaluatie-template",
  "teacher-eindoverzicht": "docent-eindoverzicht-template",
  mentor: "mentor-template",
  "mentor-evaluatie": "mentor-evaluatie-template",
  admin: "admin-template",
};

// Toestand
let allInternships = [];
let selectedInternshipId = null;
let currentCompetencies = [];
let currentLogbooks = [];
let currentEvaluations = [];
let currentFeedback = [];

// Geeft de geselecteerde stage terug
function getSelectedInternship() {
  return allInternships.find(i => i.id == selectedInternshipId) || allInternships[0] || null;
}

// Header en ambient grid tonen/verbergen
function toggleHeaderVisibility(show) {
  const topbar = document.querySelector('.topbar');
  const ambient = document.querySelector('.ambient');
  if (topbar) topbar.style.display = show ? 'flex' : 'none';
  if (ambient) ambient.style.display = show ? 'block' : 'none';
}

// Back-compat alias
let currentInternship = null;

// Hulpfuncties (formatDate, getStatusClass, showToast, showLoading, hideLoading)
// zijn verplaatst naar `js/ui-helpers.js` om dit bestand overzichtelijk te houden.

const app = document.getElementById("app");
const navPanel = document.getElementById("nav-panel");
const content = document.getElementById("content");

// Authenticatie

function updateUIForUser(user) {
  const userInfo = document.getElementById('user-info');
  const userName = document.getElementById('user-name');
  const userRole = document.getElementById('user-role');
  
  if (userInfo && userName && userRole) {
    userInfo.style.display = 'flex';
    userName.textContent = `${user.first_name} ${user.last_name}`;
    userRole.textContent = roleDisplayNames[user.role] || user.role;
  }
}

async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;
  const submitBtn = e.target.querySelector('button[type="submit"]');
  const errorEl = document.getElementById('login-error');

  console.log('[DEBUG] handleLogin called for email:', email);

  // Vorige fout wissen
  if (errorEl) {
    errorEl.textContent = '';
    errorEl.classList.remove('show');
  }

  showLoading(submitBtn, "Inloggen...");

  try {
    const data = await AuthAPI.login(email, password);
    console.log('[DEBUG] Login successful, redirecting...');
    hideLoading(submitBtn);
    showToast(`Welkom, ${data.user.first_name}!`, 'success');

    // Doorsturen naar hoofdapp
    window.location.href = 'index.html';
  } catch (error) {
    console.error('[DEBUG] Login error in handleLogin:', error.message);
    hideLoading(submitBtn);
    if (errorEl) {
      errorEl.textContent = error.message;
      errorEl.classList.add('show');
    } else {
      alert('Login fout: ' + error.message);
    }
  }
}

function handleLogout() {
  AuthAPI.logout();
  showToast('Uitgelogd', 'info');
  window.location.href = 'index.html?view=login';
}

// Weergave

function renderLogin() {
  app.className = 'login-layout';
  app.innerHTML = '';
  navPanel.style.display = 'none';
  document.body.classList.add('login-active');
  
  toggleHeaderVisibility(false);
  
  const tpl = document.getElementById('login-template');
  if (tpl) {
    app.appendChild(tpl.content.cloneNode(true));
    
    const form = document.getElementById('login-form');
    form?.addEventListener('submit', handleLogin);
    
    // Quick-login dropdown vullen vanuit seed data
    const quickLogin = document.getElementById('quick-login');
    if (quickLogin) {
      quickLogin.innerHTML = '<p class="hint">Test accounts laden...</p>';
      fetch(`${API_BASE_URL}/users/seed`)
        .then(r => r.ok ? r.json() : [])
        .then(accounts => {
          if (!accounts.length) {
            quickLogin.innerHTML = '<p class="hint">Geen test accounts beschikbaar</p>';
            return;
          }
          const options = accounts.map(a =>
            `<option value="${a.email}" data-password="${a.password}">${a.first_name} ${a.last_name} (${a.role})</option>`
          ).join('');
          quickLogin.innerHTML = `
            <label for="quick-login-select" style="display:block; margin-bottom:0.25rem; font-size:0.85rem; color:var(--ink-soft);">Kies een test account:</label>
            <select id="quick-login-select" style="width:100%; margin-bottom:0.5rem;">
              <option value="">-- Account selecteren --</option>
              ${options}
            </select>
            <button class="btn" id="quick-login-btn">Inloggen</button>
          `;
          document.getElementById('quick-login-btn')?.addEventListener('click', (e) => {
            e.preventDefault();
            const select = document.getElementById('quick-login-select');
            const option = select?.selectedOptions[0];
            if (!option || !option.value) {
              showToast('Selecteer eerst een account', 'warning');
              return;
            }
            const emailInput = document.getElementById('login-email');
            const passwordInput = document.getElementById('login-password');
            if (!emailInput || !passwordInput) {
              console.error('[DEBUG] Login inputs not found');
              return;
            }
            emailInput.value = option.value;
            passwordInput.value = option.dataset.password;
            const errorEl = document.getElementById('login-error');
            if (errorEl) {
              errorEl.textContent = '';
              errorEl.classList.remove('show');
            }
            handleLogin({
              preventDefault: () => {},
              target: form
            });
          });
        })
        .catch(() => {
          quickLogin.innerHTML = '<p class="hint">Kon test accounts niet laden</p>';
        });
    }
  }
}

async function renderMainApp() {
  app.className = 'layout';
  navPanel.style.display = 'block';
  document.body.classList.remove('login-active');
  
  toggleHeaderVisibility(true);

  const role = AuthAPI.getRole();
  const views = roleViews[role] || [];

  // Tabs vullen
  const viewTabs = document.getElementById('view-tabs');
  viewTabs.innerHTML = '';
  // ARIA: markeer als tablist
  viewTabs.setAttribute('role', 'tablist');
  views.forEach((view) => {
    const li = document.createElement('li');
    const btn = document.createElement('button');
    btn.className = 'nav-tab';
    btn.dataset.view = view;
    btn.textContent = view.charAt(0).toUpperCase() + view.slice(1);
    // ARIA: maak tab toetsenbord-bedienbaar
    btn.setAttribute('role', 'tab');
    btn.setAttribute('aria-selected', 'false');
    btn.setAttribute('tabindex', '-1');
    btn.id = `tab-${view}`;
    btn.addEventListener('click', () => {
      const url = new URL(window.location.href);
      url.searchParams.set('view', view);
      window.history.replaceState({}, '', url);
      renderView();
    });

    // Pijltjestoetsen navigatie voor tabs
    btn.addEventListener('keydown', (e) => {
      const key = e.key;
      const tabs = Array.from(viewTabs.querySelectorAll('[role="tab"]'));
      const idx = tabs.indexOf(e.currentTarget);
      if (key === 'ArrowRight') {
        e.preventDefault();
        const next = tabs[(idx + 1) % tabs.length];
        next.focus();
        next.click();
      } else if (key === 'ArrowLeft') {
        e.preventDefault();
        const prev = tabs[(idx - 1 + tabs.length) % tabs.length];
        prev.focus();
        prev.click();
      } else if (key === 'Home') {
        e.preventDefault();
        tabs[0].focus();
        tabs[0].click();
      } else if (key === 'End') {
        e.preventDefault();
        tabs[tabs.length - 1].focus();
        tabs[tabs.length - 1].click();
      }
    });
    li.appendChild(btn);
    viewTabs.appendChild(li);
  });

  renderView();
}

async function renderView() {
  const role = AuthAPI.getRole();
  const views = roleViews[role] || [];

  // Bepaal view vanuit URL of standaard
  let urlParams = new URLSearchParams(window.location.search);
  let view = urlParams.get('view');
  if (!view || !views.includes(view)) {
    view = views[0] || '';
  }

  // Actieve tab markeren
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.view === view);
  });

  content.innerHTML = '<div class="loading-overlay"><span class="loading-spinner"></span> Laden...</div>';

  const key = view ? `${role}-${view}` : role;
  const templateId = templates[key] || templates[role];

  try {
    // Geselecteerde stage uit URL
    urlParams = new URLSearchParams(window.location.search);
    const internshipParam = urlParams.get('internship');
    if (internshipParam) selectedInternshipId = parseInt(internshipParam);

    // Laad alle stages zichtbaar voor gebruiker
    allInternships = await InternshipsAPI.list();

    // Vul stage-selector (voor meerdere rollen)
    populateInternshipSelector(role);

    // Stel huidige stage in (back-compat)
    currentInternship = getSelectedInternship();

    // Laad stage-specifieke data
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

    // Template renderen
    content.innerHTML = '';
    const tpl = document.getElementById(templateId);
    if (tpl) {
      content.appendChild(tpl.content.cloneNode(true));
      await wireRoleInteractions(role, view);
    }
  } catch (error) {
    content.innerHTML = `<div class="error-message">Fout bij laden: ${error.message}</div>`;
  }
}

// Stage-selector vullen
function populateInternshipSelector(role) {
  const wrapper = document.getElementById('internship-selector-wrapper');
  const select = document.getElementById('internship-select');
  if (!wrapper || !select) return;

  if (allInternships.length === 0) {
    wrapper.style.display = 'none';
    return;
  }

  // Toon selector voor niet-studenten of als er meerdere stages zijn
  const showSelector = allInternships.length > 1 || role !== 'student';
  if (!showSelector) {
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

  // Voorselectie vanuit URL of eerste item
  const targetId = selectedInternshipId || allInternships[0]?.id;
  if (targetId) select.value = targetId;
}

// Afhandeling selectie wijziging
function handleInternshipChange() {
  const select = document.getElementById('internship-select');
  if (!select) return;
  const newId = parseInt(select.value);
  if (newId === selectedInternshipId) return;

  selectedInternshipId = newId;
  currentInternship = getSelectedInternship();

  // URL bijwerken zonder reload
  const url = new URL(window.location.href);
  url.searchParams.set('internship', newId);
  window.history.replaceState({}, '', url);

  // Huidige view vernieuwen met nieuwe data
  renderView();
}

// Vernieuw stagegegevens vanaf API
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
// Rol interacties
// ============================================

async function wireRoleInteractions(role, view) {
  const handlers = {
    student: {
      dashboard: renderStudentDashboard,
      voorstel: wireProposalForm,
      logboek: wireLogbookForm,
      overeenkomst: wireAgreementUpload,
      evaluaties: renderStudentEvaluations,
    },
    committee: {
      voorstellen: renderCommitteeProposals,
      overeenkomsten: renderCommitteeAgreements,
      overzicht: renderCommitteeOverview,
    },
    teacher: {
      opvolging: renderTeacherLogbooks,
      evaluatie: wireEvaluationForm,
      eindoverzicht: renderTeacherFinalReport,
    },
    mentor: {
      validatie: renderMentorLogbooks,
      evaluatie: renderMentorEvaluation,
    },
    admin: {
      competenties: renderCompetencyManager,
    },
  };

  const handler = handlers[role]?.[view];
  if (handler) await handler();
}

// ============================================

// Gedeelde helper voor rapporttabellen
function formatReportRows(rules) {
  return rules.map(r => `
    <tr>
      <td>${r.competency_name}</td>
      <td>${r.weight}%</td>
      <td>${r.score !== null ? r.score : '-'}</td>
      <td>${r.student_description || '-'}</td>
      <td>${r.evaluator_feedback || '-'}</td>
    </tr>
  `).join('');
}

// ============================================
// Initialisatie
// ============================================

function init() {
  const urlParams = new URLSearchParams(window.location.search);
  const view = urlParams.get('view');
  
  if (view === 'login' || !AuthAPI.isLoggedIn()) {
    renderLogin();
  } else {
    updateUIForUser(AuthAPI.getUser());
    renderMainApp();
  }
  
  // Gebeurtenisluisteraars
  // (tab clicks worden verbonden in renderMainApp)

  
  document.getElementById('internship-select')?.addEventListener('change', handleInternshipChange);
  
  document.getElementById('logout-btn')?.addEventListener('click', handleLogout);
}

// Table-card helper functies zijn verplaatst naar `js/table-cards.js`.

init();