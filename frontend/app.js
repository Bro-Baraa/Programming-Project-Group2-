// Stage Monitoring Tool

// Configuratie
// Role waarden moeten overeenkomen met backend User.role
const roleViews = {
  student: ["dashboard", "voorstel", "logboek", "overeenkomst", "evaluaties"],
  committee: ["voorstellen", "overzicht"],
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
  if (selectedInternshipId) {
    const found = allInternships.find(i => i.id == selectedInternshipId);
    if (found) return found;
  }
  return allInternships[0] || null;
}

// Back-compat alias
let currentInternship = null;

// Hulpfuncties (formatDate, getStatusClass, showToast, showLoading, hideLoading)
// zijn verplaatst naar `ui-helpers.js` om dit bestand overzichtelijk te houden.

const app = document.getElementById("app");
const navPanel = document.getElementById("nav-panel");
const content = document.getElementById("content");

// Authenticatie

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
  
  // Header en ambient grid verbergen op login
  const topbar = document.querySelector('.topbar');
  const ambient = document.querySelector('.ambient');
  if (topbar) topbar.style.display = 'none';
  if (ambient) ambient.style.display = 'none';
  
  const tpl = document.getElementById('login-template');
  if (tpl) {
    app.appendChild(tpl.content.cloneNode(true));
    
    const form = document.getElementById('login-form');
    form?.addEventListener('submit', handleLogin);
    
    // Quick-login knoppen vullen
    const quickLogin = document.getElementById('quick-login');
    if (quickLogin) {
      const accounts = [
        { email: 'admin@school.be', password: 'admin123', label: 'Admin' },
        { email: 'student1@school.be', password: 'student123', label: 'Student' },
        { email: 'commissie1@school.be', password: 'commissie123', label: 'Commissie' },
        { email: 'docent1@school.be', password: 'docent123', label: 'Docent' },
        { email: 'mentor1@school.be', password: 'mentor123', label: 'Mentor' },
      ];
      quickLogin.innerHTML = accounts.map(a =>
        `<button class="quick-login-btn" data-email="${a.email}" data-password="${a.password}">${a.label}</button>`
      ).join('');
      quickLogin.querySelectorAll('.quick-login-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          const emailInput = document.getElementById('login-email');
          const passwordInput = document.getElementById('login-password');
          if (!emailInput || !passwordInput) {
            console.error('[DEBUG] Login inputs not found');
            return;
          }
          emailInput.value = btn.dataset.email;
          passwordInput.value = btn.dataset.password;
          console.log('[DEBUG] Quick-login clicked for:', btn.dataset.email);
          // Vorige fout wissen
          const errorEl = document.getElementById('login-error');
          if (errorEl) {
            errorEl.textContent = '';
            errorEl.classList.remove('show');
          }
          // Direct handleLogin aanroepen ipv requestSubmit (browser compatibiliteit)
          handleLogin({
            preventDefault: () => {},
            target: form
          });
        });
      });
    }
  }
}

async function renderMainApp() {
  app.className = 'layout';
  navPanel.style.display = 'block';
  document.body.classList.remove('login-active');
  
  // Header en ambient grid tonen na login
  const topbar = document.querySelector('.topbar');
  const ambient = document.querySelector('.ambient');
  if (topbar) topbar.style.display = 'flex';
  if (ambient) ambient.style.display = 'block';

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
  const urlParams = new URLSearchParams(window.location.search);
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
    const urlParams = new URLSearchParams(window.location.search);
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

  // Toon selector waar nodig
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
    if (view === 'eindoverzicht') {
      renderTeacherFinalReport();
    }
  }

  // MENTOR
  if (role === 'mentor') {
    if (view === 'validatie') {
      renderMentorLogbooks();
    }
    if (view === 'evaluatie') {
      renderMentorEvaluation();
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
// Studentweergaven
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
    const hasAgreement = currentInternship.agreement_uploaded === true;

    hero.innerHTML = `
      <h2>Mijn Stage</h2>
      <p><strong>Bedrijf:</strong> ${companyName}</p>
      <p><strong>Periode:</strong> ${startDate} - ${endDate}</p>
      <p><strong>Status:</strong> <span class="status-pill ${getStatusClass(currentInternship.status)}">${currentInternship.status}</span></p>
      <p><strong>Overeenkomst:</strong> ${hasAgreement ? '✓ Ontvangen' : '✗ Nog niet'}</p>
    `;
  }

  // Logboeken tabel bijwerken
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

  // Feedback sectie bijwerken
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
  const container = content.querySelector('.panel.card');
  if (!container) return;

  // ── No internship yet: show the original creation form ──
  if (!currentInternship) {
    const form = document.getElementById('proposal-form');
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
    return;
  }

  // ── Student already has an internship: show proposal details ──
  const proposal = currentInternship.proposal;
  const company = currentInternship.company || {};
  const isChangesRequired = currentInternship.status === 'Aanpassingen Vereist';
  const feedback = proposal?.feedback;

  container.innerHTML = `
    <h2>Mijn Stagevoorstel</h2>

    <div class="proposal-summary">
      <p><strong>Status:</strong> <span class="status-pill ${getStatusClass(currentInternship.status)}">${currentInternship.status}</span></p>
      <p><strong>Bedrijf:</strong> ${escapeHtml(company.name || 'Onbekend')}</p>
      ${company.address ? `<p><strong>Adres:</strong> ${escapeHtml(company.address)}</p>` : ''}
      ${company.sector ? `<p><strong>Sector:</strong> ${escapeHtml(company.sector)}</p>` : ''}
      <p><strong>Contactpersoon:</strong> ${escapeHtml(company.contact_person || 'Onbekend')}</p>
      <p><strong>E-mail:</strong> ${escapeHtml(company.contact_email || 'Onbekend')}</p>
      <p><strong>Periode:</strong> ${formatDate(currentInternship.start_date)} – ${formatDate(currentInternship.end_date)}</p>
      <div class="proposal-description">
        <p><strong>Omschrijving opdracht:</strong></p>
        <div style="background: rgba(0,0,0,0.03); padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem;">
          ${escapeHtml(proposal?.description || 'Geen omschrijving beschikbaar.')}
        </div>
      </div>
    </div>

    ${feedback ? `
      <div class="info-message warning">
        <p><strong>Feedback van de commissie:</strong></p>
        <p>${escapeHtml(feedback)}</p>
      </div>
    ` : ''}

    ${isChangesRequired ? `
      <div class="resubmit-section" style="margin-top: 1.5rem;">
        <h3>Opnieuw indienen</h3>
        <p class="hint">Pas je voorstel aan op basis van de feedback en dien opnieuw in.</p>
        <form id="resubmit-form">
          <div class="row full">
            <label>Bedrijfsnaam</label>
            <input type="text" id="resubmit-company-name" value="${escapeHtml(company.name || '')}" />
          </div>
          <div class="row full">
            <label>Adres</label>
            <input type="text" id="resubmit-company-address" value="${escapeHtml(company.address || '')}" />
          </div>
          <div class="row full">
            <label>Sector</label>
            <input type="text" id="resubmit-company-sector" value="${escapeHtml(company.sector || '')}" />
          </div>
          <div class="row full">
            <label>Contactpersoon</label>
            <input type="text" id="resubmit-contact-person" value="${escapeHtml(company.contact_person || '')}" />
          </div>
          <div class="row full">
            <label>E-mail contactpersoon</label>
            <input type="email" id="resubmit-contact-email" value="${escapeHtml(company.contact_email || '')}" />
          </div>
          <div class="row full">
            <label>Stageperiode</label>
            <div class="date-range">
              <input type="date" id="resubmit-start-date" value="${currentInternship.start_date || ''}" />
              <span>tot</span>
              <input type="date" id="resubmit-end-date" value="${currentInternship.end_date || ''}" />
            </div>
          </div>
          <div class="row full">
            <label>Omschrijving opdracht * (min. 20 karakters)</label>
            <textarea id="resubmit-description" rows="4" required minlength="20">${escapeHtml(proposal?.description || '')}</textarea>
          </div>
          <button type="submit" class="btn">Voorstel Opnieuw Indienen</button>
        </form>
      </div>
    ` : `
      <div class="info-message" style="margin-top: 1rem;">
        <p>Je voorstel is ${currentInternship.status === 'In Beoordeling' ? 'in beoordeling' : currentInternship.status === 'Goedgekeurd' ? 'goedgekeurd' : 'afgekeurd'}. Je kunt het op dit moment niet meer wijzigen.</p>
      </div>
    `}
  `;

  // Wire resubmit form
  const resubmitForm = document.getElementById('resubmit-form');
  resubmitForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = resubmitForm.querySelector('button[type="submit"]');
    const newDescription = document.getElementById('resubmit-description').value;

    if (!newDescription || newDescription.length < 20) {
      showToast('Omschrijving moet minstens 20 karakters bevatten', 'error');
      return;
    }

    showLoading(submitBtn, 'Indienen...');

    try {
      await ProposalsAPI.resubmit(currentInternship.id, newDescription, {
        company_name: document.getElementById('resubmit-company-name').value || undefined,
        company_address: document.getElementById('resubmit-company-address').value || undefined,
        company_sector: document.getElementById('resubmit-company-sector').value || undefined,
        contact_person: document.getElementById('resubmit-contact-person').value || undefined,
        contact_email: document.getElementById('resubmit-contact-email').value || undefined,
        start_date: document.getElementById('resubmit-start-date').value || undefined,
        end_date: document.getElementById('resubmit-end-date').value || undefined,
      });
      hideLoading(submitBtn);
      showToast('Voorstel succesvol opnieuw ingediend!', 'success');
      await refreshInternshipData();
      renderView();
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

  // Vul weeknummer met volgende beschikbare week
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

      // Gegevens verversen
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
      // Zoek of maak logboek
      let logbook = currentLogbooks.find(lb => lb.week_number === parseInt(week));
      
      if (!logbook) {
        // Maak eerst concept aan
        logbook = await InternshipsAPI.createLogbook(currentInternship.id, {
          week_number: parseInt(week),
          tasks: tasks,
          reflection: document.getElementById('log-reflection').value,
          issues: document.getElementById('log-issues').value,
          status: 'draft'
        });
      }

      // Submit via dedicated endpoint
      await InternshipsAPI.submitLogbook(logbook.id);

      hideLoading(submitBtn);
      showToast(`Logboek week ${week} ingediend!`, 'success');

      // Gegevens verversen
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

  // Controleer status - alleen toegestaan bij goedkeuring
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

  // Controleer of overeenkomst al bestaat (backend list retourneert agreement_uploaded)
  const hasAgreement = currentInternship.agreement_uploaded === true;

  // Statusweergave bijwerken
  const statusText = document.getElementById('agreement-status-text');
  if (hasAgreement && statusText) {
    statusText.innerHTML = '<span class="status-pill status-good">Ontvangen</span>';
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

      // Vernieuw stagegegevens na upload overeenkomst
      await refreshInternshipData();

      if (statusText) {
        statusText.innerHTML = '<span class="status-pill status-good">Ontvangen</span>';
      }
    } catch (error) {
      hideLoading(submitBtn);
      showToast(error.message, 'error');
    }
  });
}

async function renderStudentEvaluations() {
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

  // US-09: Eindoverzicht ophalen
  const finalSummary = document.getElementById('final-summary');
  if (!finalSummary || !currentInternship) return;

  try {
    const report = await InternshipsAPI.getFinalReport(currentInternship.id);
    if (!report || !report.rules || report.rules.length === 0) {
      finalSummary.innerHTML = `
        <p><strong>Status:</strong> Afwachten</p>
        <p>De finale evaluatie is nog niet ingediend.</p>
      `;
      return;
    }

    const rows = report.rules.map(r => `
      <tr>
        <td>${r.competency_name}</td>
        <td>${r.weight}%</td>
        <td>${r.score !== null ? r.score : '-'}</td>
        <td>${r.student_description || '-'}</td>
        <td>${r.evaluator_feedback || '-'}</td>
      </tr>
    `).join('');

    finalSummary.innerHTML = `
      <p><strong>Gewogen eindscore:</strong> <span class="score-highlight">${report.weighted_average_score !== null ? report.weighted_average_score.toFixed(2) : '-'} / 5</span></p>
      <table style="margin-top: 0.5rem;">
        <thead>
          <tr><th>Competentie</th><th>Gewicht</th><th>Score</th><th>Mijn beschrijving</th><th>Feedback</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    `;
  } catch (error) {
    console.error('Failed to load final report:', error);
    finalSummary.innerHTML = '<p class="error">Kon eindoverzicht niet laden.</p>';
  }
}

// ============================================
// Commissieweergaven
// ============================================

async function renderCommitteeProposals() {
  try {
    const tbody = document.querySelector('#proposals-table tbody');

    if (tbody) {
      tbody.innerHTML = allInternships.map(p => `
        <tr data-id="${p.id}" class="proposal-row">
          <td>${p.student?.first_name || 'Onbekend'} ${p.student?.last_name || ''}</td>
          <td>${p.company?.name || 'Onbekend'}</td>
          <td>${new Date(p.created_at).toLocaleDateString('nl-BE')}</td>
          <td><span class="status-pill ${getStatusClass(p.status)}">${p.status}</span></td>
          <td>${p.agreement_uploaded ? '<span class="status-pill status-good">Ontvangen</span>' : '<span class="status-pill status-warn">Nog niet</span>'}</td>
        </tr>
      `).join('');

      // Klikhandler: selecteer stage en toon detailpaneel
      tbody.querySelectorAll('.proposal-row').forEach(row => {
        row.addEventListener('click', () => {
          const id = parseInt(row.dataset.id);
          selectProposalForReview(id);
        });
      });
    }

    // Als een voorstel via URL is geselecteerd, toon detail
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

  // URL bijwerken
  selectedInternshipId = internshipId;
  currentInternship = internship;
  const url = new URL(window.location.href);
  url.searchParams.set('internship', internshipId);
  window.history.replaceState({}, '', url);

  // Geselecteerde rij markeren
  document.querySelectorAll('.proposal-row').forEach(r => {
    r.style.background = r.dataset.id == internshipId ? 'rgba(0, 121, 140, 0.1)' : '';
  });

  // Detailpaneel tonen
  const panel = document.getElementById('proposal-detail-panel');
  if (panel) panel.style.display = 'block';

  // Detailinformatie vullen
  document.getElementById('selected-student-name').textContent =
    `${internship.student?.first_name || ''} ${internship.student?.last_name || ''}`;
  document.getElementById('selected-company').textContent = internship.company?.name || 'Onbekend';
  document.getElementById('selected-status').textContent = internship.status;

  // Haal voorstelbeschrijving op en toon
  document.getElementById('selected-description').textContent = 'Laden...';
  InternshipsAPI.get(internship.id).then(full => {
    document.getElementById('selected-description').textContent =
      full.proposal?.description || 'Geen omschrijving beschikbaar.';
  }).catch(() => {
    document.getElementById('selected-description').textContent = 'Kon omschrijving niet laden.';
  });

  // Actieknoppen verbinden
  const actionsDiv = document.getElementById('review-actions');
  if (actionsDiv) {
    const status = internship.status;
    if (status === 'Ingediend' || status === 'Aanpassingen Vereist') {
      // Eerst "In Beoordeling" zetten
      actionsDiv.innerHTML = `
        <button id="btn-review" class="btn">🔍 In Beoordeling Zetten</button>
      `;
      document.getElementById('btn-review')?.addEventListener('click', () => doReview(internship.id, 'In Beoordeling'));
    } else if (status === 'In Beoordeling') {
      // Dan pas beslissen
      actionsDiv.innerHTML = `
        <button id="btn-approve" class="btn success">✓ Goedkeuren</button>
        <button id="btn-reject" class="btn danger">✗ Afkeuren</button>
        <button id="btn-changes" class="btn secondary">⚠ Aanpassingen Vereist</button>
      `;
      document.getElementById('btn-approve')?.addEventListener('click', () => doReview(internship.id, 'Goedgekeurd'));
      document.getElementById('btn-reject')?.addEventListener('click', () => doReview(internship.id, 'Afgekeurd'));
      document.getElementById('btn-changes')?.addEventListener('click', () => doReview(internship.id, 'Aanpassingen Vereist'));
    } else {
      actionsDiv.innerHTML = '<p class="hint">Voorstel is al beoordeeld.</p>';
    }
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
    // Gegevens verversen
    allInternships = await InternshipsAPI.list();
    renderCommitteeProposals();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function renderCommitteeOverview() {
  try {
    const stats = await InternshipsAPI.getDashboardStats();

    // Statistieken bijwerken
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

    // Tabel bijwerken
    const tbody = document.querySelector('table tbody');
    if (tbody) {
      tbody.innerHTML = allInternships.map(p => `
        <tr>
          <td>${p.student?.first_name || 'Onbekend'}</td>
          <td>${p.company?.name || 'Onbekend'}</td>
          <td>${formatDate(p.start_date)} - ${formatDate(p.end_date)}</td>
          <td><span class="status-pill ${getStatusClass(p.status)}">${p.status}</span></td>
          <td>${p.agreement_uploaded ? '<span class="status-pill status-good">Ontvangen</span>' : '<span class="status-pill status-warn">Nog niet</span>'}</td>
        </tr>
      `).join('');
    }
  } catch (error) {
    showToast(error.message, 'error');
  }
}

// ============================================
// Docent/Admin weergaven
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

  // Haal bestaande evaluaties voor deze stage op
  InternshipsAPI.getEvaluations(currentInternship.id).then(evaluations => {
    currentEvaluations = evaluations;

    // Gebruik bestaande concept-evaluatie indien aanwezig, anders aanmaken bij opslaan
    const existingEval = evaluations.find(e => !e.finalized);

    if (container && currentCompetencies.length > 0) {
      container.innerHTML = currentCompetencies.map(comp => {
        // Zoek regel voor deze competentie als evaluatie bestaat
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

  // Scores opslaan (maakt evaluatie aan indien nodig)
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
      // Stap 1: Evaluatie aanmaken (indien geen concept)
      let evaluation = currentEvaluations.find(e => !e.finalized && e.eval_type === evalType);
      if (!evaluation) {
        evaluation = await InternshipsAPI.createEvaluation(currentInternship.id, {
          eval_type: evalType
        });
        currentEvaluations.push(evaluation);
      }

      // Stap 2: Werk elke regel bij met score, feedback en omschrijving
      const rows = container.querySelectorAll('.eval-row');
      for (const row of rows) {
        const compId = parseInt(row.dataset.compId);
        const score = parseInt(row.querySelector('.score-select')?.value);
        const feedback = row.querySelector('.feedback-input')?.value || null;
        const studentDesc = row.querySelector('.student-desc-input')?.value || null;

        // Vind regel-ID voor deze competentie
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

  // Evaluatie finaliseren
  finalizeBtn?.addEventListener('click', async () => {
    if (!confirm('Evaluatie definitief afsluiten? Dit kan niet ongedaan gemaakt worden.')) return;

    if (!currentInternship) {
      showToast('Geen stage geselecteerd', 'error');
      return;
    }

    // Eerst huidige scores opslaan
    const submitBtn = evalForm.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.click();

    // Daarna evaluatie zoeken en finaliseren
    const evalType = document.getElementById('eval-type')?.value || 'tussentijds';
    const evaluation = currentEvaluations.find(e => !e.finalized && e.eval_type === evalType);

    if (!evaluation) {
      showToast('Geen evaluatie gevonden om af te sluiten', 'error');
      return;
    }

    showLoading(finalizeBtn, 'Bezig...');

    try {
      // Backend finalize endpoint: POST /evaluations/{id}/finalize
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
        <button class="btn small secondary" onclick="handleDeleteCompetency(${comp.id})" style="margin-left: 0.6rem;">Verwijder</button>
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
  
  // Formulier verbinden
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
  
  // Bereken knop
  const calcBtn = document.getElementById('calc-score');
  calcBtn?.addEventListener('click', () => {
    const total = currentCompetencies.reduce((sum, c) => sum + c.weight, 0);
    if (total !== 100) {
      showToast('Gewichten moeten 100% zijn', 'error');
      return;
    }
    
    // Bereken gewogen score
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
// Docent eindoverzicht
// ============================================

async function renderTeacherFinalReport() {
  const container = document.getElementById('final-report-content');
  if (!container) return;

  if (!currentInternship) {
    container.innerHTML = '<p>Selecteer een stage via het navigatiemenu.</p>';
    return;
  }

  container.innerHTML = '<p>Laden...</p>';

  try {
    const report = await InternshipsAPI.getFinalReport(currentInternship.id);
    if (!report || !report.rules || report.rules.length === 0) {
      container.innerHTML = '<p>Geen eindoverzicht beschikbaar. Finaliseer eerst een evaluatie.</p>';
      return;
    }

    const rows = report.rules.map(r => `
      <tr>
        <td>${r.competency_name}</td>
        <td>${r.weight}%</td>
        <td>${r.score !== null ? r.score : '-'}</td>
        <td>${r.student_description || '-'}</td>
        <td>${r.evaluator_feedback || '-'}</td>
      </tr>
    `).join('');

    container.innerHTML = `
      <div class="panel card" style="margin-top: 1rem;">
        <p><strong>Student:</strong> ${currentInternship.student_name || 'Onbekend'}</p>
        <p><strong>Bedrijf:</strong> ${currentInternship.company_name || 'Onbekend'}</p>
        <p><strong>Periode:</strong> ${formatDate(currentInternship.start_date)} – ${formatDate(currentInternship.end_date)}</p>
        <p><strong>Gewogen eindscore:</strong> <span class="score-highlight">${report.weighted_average_score !== null ? report.weighted_average_score.toFixed(2) : '-'} / 5</span></p>
      </div>
      <table style="margin-top: 1rem;">
        <thead>
          <tr><th>Competentie</th><th>Gewicht</th><th>Score</th><th>Student beschrijving</th><th>Feedback</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
      <button class="btn" style="margin-top: 1rem;" onclick="window.print()">Afdrukken</button>
    `;
  } catch (error) {
    console.error('Failed to load final report:', error);
    container.innerHTML = '<p class="error">Kon eindoverzicht niet laden.</p>';
  }
}

// ============================================
// Docent & Mentor logboekweergaven
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
      <td><span class="status-pill ${getStatusClass(lb.status)}">${lb.status === 'submitted' ? 'Ingediend' : 'Concept'}</span></td>
      <td>${lb.mentor_validated ? '✓ Gevalideerd' : 'In afwachting'}</td>
    </tr>
  `).join('');

  // Feedbackknop verbinden
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
      <td><span class="status-pill ${getStatusClass(lb.status)}">${lb.status === 'submitted' ? 'Ingediend' : 'Concept'}</span></td>
      <td>
        ${lb.mentor_validated
          ? '<span class="status-pill status-good">✓ Gevalideerd</span>'
          : `<button class="btn small validate-logbook-btn" data-id="${lb.id}">Valideren</button>`
        }
      </td>
    </tr>
  `).join('');

  // Validatieknoppen verbinden
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
        // Vernieuw logboeken
        currentLogbooks = await InternshipsAPI.getLogbooks(currentInternship.id);
        renderMentorLogbooks();
      } catch (error) {
        hideLoading(btn);
        showToast(error.message, 'error');
      }
    });
  });
}

// Renderen van mentor-feedbackformulier per competentie
async function renderMentorEvaluation() {
  const container = document.getElementById('mentor-eval-content');
  if (!container) return;

  if (!currentInternship) {
    container.innerHTML = '<p>Selecteer een stage via het navigatiemenu.</p>'; 
    return;
  }
  const actieveEval = currentEvaluations.find(e => !e.finalized);
  if (!actieveEval) {
    container.innerHTML = '<p>Geen actieve evaluatie gevonden voor deze stage.</p>';
    return;
  }

  container.innerHTML = `
  ${currentCompetencies.map(comp => {
    const rule = actieveEval.rules?.find(r => r.competency_id === comp.id);
    return `<label>${comp.name}</label><textarea data-rule-id="${rule?.id ?? ''}" placeholder="Geef hier je feedback..."></textarea>`;
  }).join('')}<button id="save-mentor-feedback" class="btn">Feedback Opslaan</button>`;

  document.getElementById('save-mentor-feedback')?.addEventListener('click', async () => {
    const textareas = container.querySelectorAll('textarea');

    for (const textarea of textareas) {
      const ruleId = textarea.dataset.ruleId;
      const feedback = textarea.value;

      if (ruleId) {
      await EvaluationRulesAPI.update(actieveEval.id, ruleId, { evaluator_feedback: feedback });
      }
    }
    showToast('Feedback opgeslagen!', 'success');
  });
} 

// Handler voor verwijderen van competentie - beschikbaar in window voor templates
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

// Blootstellen aan window voor template onclick-handlers
window.handleDeleteCompetency = handleDeleteCompetency;
window.selectProposalForReview = selectProposalForReview;
window.doReview = doReview;

// ============================================
// Initialisatie
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
  
  // Gebeurtenisluisteraars
  // (tab clicks worden verbonden in renderMainApp)

  
  document.getElementById('internship-select')?.addEventListener('change', handleInternshipChange);
  
  document.getElementById('logout-btn')?.addEventListener('click', handleLogout);
}

// Table-card helper functies zijn verplaatst naar `table-cards.js`.

init();