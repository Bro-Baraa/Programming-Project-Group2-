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
    if (view === 'overeenkomsten') {
      renderCommitteeAgreements();
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
    const agreementStatus = currentInternship.agreement_status || 'Niet Ingediend';
    const agreementLabel = agreementStatus === 'Niet Ingediend'
      ? '✗ Nog niet'
      : agreementStatus === 'Onvolledig'
        ? '⚠ Onvolledig'
        : `✓ ${agreementStatus}`;

    hero.innerHTML = `
      <h2>Mijn Stage</h2>
      <p><strong>Bedrijf:</strong> ${companyName}</p>
      <p><strong>Periode:</strong> ${startDate} - ${endDate}</p>
      <p><strong>Status:</strong> <span class="status-pill ${getStatusClass(currentInternship.status)}">${currentInternship.status}</span></p>
      <p><strong>Overeenkomst:</strong> ${agreementLabel}</p>
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
        <td>${lb.mentor_feedback ? lb.mentor_feedback : '<span class="hint">-</span>'}</td>
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
  const isIngediend = currentInternship.status === 'Ingediend';
  const feedback = proposal?.feedback;
  const revisionCount = proposal?.revision_count || 0;
  const resubmittedAt = proposal?.resubmitted_at;

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
      ${revisionCount > 0 ? `<p><strong>Aantal herzieningen:</strong> ${revisionCount}</p>` : ''}
      ${resubmittedAt ? `<p><strong>Laatst herzien:</strong> ${formatDate(resubmittedAt)}</p>` : ''}
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

    ${isIngediend ? `
      <div class="btn-group" style="margin-top: 1rem;">
        <button id="btn-edit-proposal" class="btn">✏️ Wijzigen</button>
        <button id="btn-withdraw-proposal" class="btn danger">🗑️ Intrekken</button>
      </div>
      <div id="edit-section" style="display: none; margin-top: 1.5rem;">
        <h3>Voorstel wijzigen</h3>
        <p class="hint">Pas je voorstel aan voor de commissie het beoordeelt.</p>
        <form id="edit-form">
          <div class="row full">
            <label>Bedrijfsnaam</label>
            <input type="text" id="edit-company-name" value="${escapeHtml(company.name || '')}" />
          </div>
          <div class="row full">
            <label>Adres</label>
            <input type="text" id="edit-company-address" value="${escapeHtml(company.address || '')}" />
          </div>
          <div class="row full">
            <label>Sector</label>
            <input type="text" id="edit-company-sector" value="${escapeHtml(company.sector || '')}" />
          </div>
          <div class="row full">
            <label>Contactpersoon</label>
            <input type="text" id="edit-contact-person" value="${escapeHtml(company.contact_person || '')}" />
          </div>
          <div class="row full">
            <label>E-mail contactpersoon</label>
            <input type="email" id="edit-contact-email" value="${escapeHtml(company.contact_email || '')}" />
          </div>
          <div class="row full">
            <label>Stageperiode</label>
            <div class="date-range">
              <input type="date" id="edit-start-date" value="${currentInternship.start_date || ''}" />
              <span>tot</span>
              <input type="date" id="edit-end-date" value="${currentInternship.end_date || ''}" />
            </div>
          </div>
          <div class="row full">
            <label>Omschrijving opdracht * (min. 20 karakters)</label>
            <textarea id="edit-description" rows="4" required minlength="20">${escapeHtml(proposal?.description || '')}</textarea>
          </div>
          <div class="btn-group">
            <button type="submit" class="btn">Wijzigingen opslaan</button>
            <button type="button" id="btn-cancel-edit" class="btn secondary">Annuleren</button>
          </div>
        </form>
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
    ` : ''}

    ${!isIngediend && !isChangesRequired ? `
      <div class="info-message" style="margin-top: 1rem;">
        <p>Je voorstel is ${currentInternship.status === 'In Beoordeling' ? 'in beoordeling' : currentInternship.status === 'Afgekeurd' ? 'afgekeurd' : 'goedgekeurd'}. Je kunt het op dit moment niet meer wijzigen.</p>
      </div>
    ` : ''}
  `;

  // Wire edit form
  const editBtn = document.getElementById('btn-edit-proposal');
  const editSection = document.getElementById('edit-section');
  const editForm = document.getElementById('edit-form');
  const cancelEditBtn = document.getElementById('btn-cancel-edit');

  editBtn?.addEventListener('click', () => {
    if (editSection) editSection.style.display = 'block';
    editBtn.style.display = 'none';
    const withdrawBtn = document.getElementById('btn-withdraw-proposal');
    if (withdrawBtn) withdrawBtn.style.display = 'none';
  });

  cancelEditBtn?.addEventListener('click', () => {
    if (editSection) editSection.style.display = 'none';
    editBtn.style.display = 'inline-block';
    const withdrawBtn = document.getElementById('btn-withdraw-proposal');
    if (withdrawBtn) withdrawBtn.style.display = 'inline-block';
  });

  editForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = editForm.querySelector('button[type="submit"]');
    const description = document.getElementById('edit-description').value;

    if (!description || description.length < 20) {
      showToast('Omschrijving moet minstens 20 karakters bevatten', 'error');
      return;
    }

    showLoading(submitBtn, 'Opslaan...');

    try {
      await ProposalsAPI.edit(currentInternship.id, {
        description,
        company_name: document.getElementById('edit-company-name').value || undefined,
        company_address: document.getElementById('edit-company-address').value || undefined,
        company_sector: document.getElementById('edit-company-sector').value || undefined,
        contact_person: document.getElementById('edit-contact-person').value || undefined,
        contact_email: document.getElementById('edit-contact-email').value || undefined,
        start_date: document.getElementById('edit-start-date').value || undefined,
        end_date: document.getElementById('edit-end-date').value || undefined,
      });
      hideLoading(submitBtn);
      showToast('Wijzigingen opgeslagen!', 'success');
      await refreshInternshipData();
      renderView();
    } catch (error) {
      hideLoading(submitBtn);
      showToast(error.message, 'error');
    }
  });

  // Wire withdraw button
  document.getElementById('btn-withdraw-proposal')?.addEventListener('click', async () => {
    if (!confirm('Weet je zeker dat je je stagevoorstel wilt intrekken? Dit kan niet ongedaan gemaakt worden.')) return;

    try {
      await ProposalsAPI.withdraw(currentInternship.id);
      showToast('Voorstel succesvol ingetrokken', 'success');
      await refreshInternshipData();
      renderView();
    } catch (error) {
      showToast(error.message, 'error');
    }
  });

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
  const cancelBtn = document.getElementById('cancel-logbook');
  const gridEl = document.getElementById('logbook-week-grid');
  const formPanel = document.getElementById('logbook-form-panel');
  const formWeekLabel = document.getElementById('form-week-label');

  if (!currentInternship) {
    content.innerHTML = `
      <div class="panel card reveal">
        <h2>Geen stage gevonden</h2>
        <p>Je moet eerst een stage indienen voordat je logboeken kunt invullen.</p>
      </div>
    `;
    return;
  }

  const canLog = currentInternship.status === 'Lopend' || currentInternship.status === 'Afgerond';
  if (!canLog) {
    content.innerHTML = `
      <div class="panel card reveal">
        <h2>Logboeken</h2>
        <p>Je kunt pas logboeken invullen als je stage actief is.</p>
        <p>Huidige status: <strong>${currentInternship.status}</strong></p>
        <a href="?view=dashboard" class="btn">Naar dashboard</a>
      </div>
    `;
    return;
  }

  let selectedWeek = null;
  let selectedLogbook = null;

  // ── Build week grid ──
  function renderWeekGrid() {
    if (!gridEl) return;
    const start = currentInternship.start_date ? new Date(currentInternship.start_date) : null;
    const end = currentInternship.end_date ? new Date(currentInternship.end_date) : null;
    let totalWeeks = 0;
    if (start && end && end > start) {
      const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
      totalWeeks = Math.max(1, Math.floor(days / 7) + 1);
    }
    if (!totalWeeks) {
      gridEl.innerHTML = '<p class="hint">Stageperiode niet ingesteld.</p>';
      return;
    }

    const logbookMap = new Map(currentLogbooks.map(lb => [lb.week_number, lb]));

    gridEl.innerHTML = '';
    for (let w = 1; w <= totalWeeks; w++) {
      const lb = logbookMap.get(w);
      let statusClass = 'status-missing';
      let statusLabel = 'Ontbrekend';
      if (lb) {
        if (lb.status === 'submitted') {
          statusClass = 'status-submitted';
          statusLabel = lb.mentor_validated ? 'Aftekend' : 'Ingediend';
        } else {
          statusClass = 'status-draft';
          statusLabel = 'Concept';
        }
      }

      const cell = document.createElement('div');
      cell.className = `week-cell ${statusClass}`;
      cell.dataset.week = w;
      cell.innerHTML = `
        <span class="week-number">${w}</span>
        <span class="week-status">${statusLabel}</span>
      `;
      cell.addEventListener('click', () => openWeek(w));
      gridEl.appendChild(cell);
    }
  }

  // ── Open a week in the form ──
  function openWeek(week) {
    selectedWeek = week;
    selectedLogbook = currentLogbooks.find(lb => lb.week_number === week) || null;

    // Highlight selected cell
    gridEl?.querySelectorAll('.week-cell').forEach(c => c.classList.remove('selected'));
    gridEl?.querySelector(`[data-week="${week}"]`)?.classList.add('selected');

    // Show form panel
    if (formPanel) formPanel.style.display = 'block';
    if (formWeekLabel) formWeekLabel.textContent = week;

    document.getElementById('log-week').value = week;
    document.getElementById('log-tasks').value = selectedLogbook?.tasks || '';
    document.getElementById('log-reflection').value = selectedLogbook?.reflection || '';
    document.getElementById('log-issues').value = selectedLogbook?.issues || '';

    // Disable submit if already submitted
    if (submitBtn) {
      submitBtn.disabled = selectedLogbook?.status === 'submitted';
      submitBtn.textContent = selectedLogbook?.status === 'submitted' ? 'Reeds ingediend' : 'Definitief Indienen';
    }
  }

  function closeForm() {
    if (formPanel) formPanel.style.display = 'none';
    gridEl?.querySelectorAll('.week-cell').forEach(c => c.classList.remove('selected'));
    selectedWeek = null;
    selectedLogbook = null;
  }

  // ── Save as draft ──
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const saveBtn = form.querySelector('button[type="submit"]');
    const week = parseInt(document.getElementById('log-week').value);
    const tasks = document.getElementById('log-tasks').value;

    if (!week) {
      showToast('Selecteer een week', 'error');
      return;
    }

    showLoading(saveBtn, 'Opslaan...');

    try {
      const payload = {
        week_number: week,
        tasks: tasks,
        reflection: document.getElementById('log-reflection').value,
        issues: document.getElementById('log-issues').value,
        status: 'draft'
      };

      if (selectedLogbook) {
        await InternshipsAPI.updateLogbook(selectedLogbook.id, payload);
      } else {
        await InternshipsAPI.createLogbook(currentInternship.id, payload);
      }

      hideLoading(saveBtn);
      showToast('Logboek opgeslagen als concept', 'info');

      // Refresh data and re-render grid
      currentLogbooks = await InternshipsAPI.getLogbooks(currentInternship.id);
      renderWeekGrid();
      // Re-open same week to update selectedLogbook reference
      if (selectedWeek) openWeek(selectedWeek);
    } catch (error) {
      hideLoading(saveBtn);
      showToast(error.message, 'error');
    }
  });

  // ── Submit ──
  submitBtn?.addEventListener('click', async () => {
    const week = parseInt(document.getElementById('log-week').value);
    const tasks = document.getElementById('log-tasks').value;

    if (!week) {
      showToast('Selecteer een week', 'error');
      return;
    }
    if (!tasks) {
      showToast('Taken zijn verplicht', 'error');
      return;
    }
    if (selectedLogbook?.status === 'submitted') {
      showToast('Logboek is al ingediend', 'error');
      return;
    }

    showLoading(submitBtn, 'Indienen...');

    try {
      // Ensure logbook exists first
      let logbook = selectedLogbook;
      if (!logbook) {
        logbook = await InternshipsAPI.createLogbook(currentInternship.id, {
          week_number: week,
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

      // Refresh data and re-render grid
      currentLogbooks = await InternshipsAPI.getLogbooks(currentInternship.id);
      renderWeekGrid();
      if (selectedWeek) openWeek(selectedWeek);
    } catch (error) {
      hideLoading(submitBtn);
      showToast(error.message, 'error');
    }
  });

  // ── Cancel ──
  cancelBtn?.addEventListener('click', closeForm);

  // ── Initial render ──
  renderWeekGrid();
}

function wireAgreementUpload() {
  const form = document.getElementById('agreement-form');
  const statusText = document.getElementById('agreement-status-text');

  if (!currentInternship) {
    content.innerHTML = `
      <div class="panel card reveal">
        <h2>Geen stage gevonden</h2>
        <p>Je moet eerst een stage indienen.</p>
      </div>
    `;
    return;
  }

  const agreementStatus = currentInternship.agreement_status;

  // If agreement is already validated, show success regardless of internship status
  if (agreementStatus === 'Gevalideerd') {
    if (statusText) {
      statusText.innerHTML = `<span class="status-pill status-good">Gevalideerd</span>`;
    }
    form.innerHTML = `
      <div class="info-message success">
        <p>✓ Je overeenkomst is gevalideerd. De stage is actief.</p>
      </div>
    `;
    return;
  }

  const canUpload = currentInternship.status === 'Goedgekeurd' || currentInternship.status === 'Overeenkomst Ingediend';

  if (!canUpload) {
    form.innerHTML = `
      <div class="info-message warning">
        <p>⚠️ Je kan geen overeenkomst uploaden in deze fase.</p>
        <p>Huidige status: <strong>${currentInternship.status}</strong></p>
        <a href="?view=dashboard" class="btn">Naar dashboard</a>
      </div>
    `;
    return;
  }
  const hint = document.getElementById('agreement-hint');

  function setStatusLabel(label, className) {
    if (statusText) {
      statusText.innerHTML = `<span class="status-pill ${className}">${label}</span>`;
    }
  }

  function setHint(text) {
    if (hint) hint.textContent = text;
  }

  if (agreementStatus === 'Onvolledig') {
    setStatusLabel('Onvolledig', 'status-warn');
    setHint('De commissie heeft je overeenkomst als onvolledig gemarkeerd. Upload een nieuwe versie.');
    form.insertAdjacentHTML('afterbegin', `
      <div class="info-message warning" style="margin-bottom: 1rem;">
        <p>⚠️ De commissie heeft je overeenkomst als onvolledig gemarkeerd. Upload een nieuwe versie.</p>
      </div>
    `);
  } else if (agreementStatus === 'Ingediend') {
    setStatusLabel('Ingediend', 'status-info');
    setHint('Je overeenkomst is ingediend en wacht op validatie door de commissie.');
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
        <td>${getEvalTypeLabel(ev.eval_type)}</td>
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
      tbody.innerHTML = allInternships.map(p => {
        const agreementCell = p.status === 'Afgekeurd'
          ? '<span class="hint">-</span>'
          : p.agreement_uploaded
            ? '<span class="status-pill status-good">Ontvangen</span>'
            : '<span class="status-pill status-warn">Nog niet</span>';
        return `
        <tr data-id="${p.id}" class="proposal-row">
          <td>${p.student?.first_name || 'Onbekend'} ${p.student?.last_name || ''}</td>
          <td>${p.company?.name || 'Onbekend'}</td>
          <td>${new Date(p.created_at).toLocaleDateString('nl-BE')}</td>
          <td><span class="status-pill ${getStatusClass(p.status)}">${p.status}</span></td>
          <td>${agreementCell}</td>
        </tr>
      `}).join('');

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
    // Vul feedback box met bestaande feedback (issue #5)
    const feedbackBox = document.getElementById('feedback-box');
    if (feedbackBox && full.proposal?.feedback) {
      feedbackBox.value = full.proposal.feedback;
    }
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

async function renderCommitteeAgreements() {
  try {
    const tbody = document.querySelector('#agreements-table tbody');

    if (tbody) {
      // Filter stages that have an agreement uploaded or are approved (waiting for agreement)
      const stagesWithAgreements = allInternships.filter(
        i => i.status === 'Goedgekeurd' || i.status === 'Overeenkomst Ingediend' || i.status === 'Lopend' || i.status === 'Afgerond' || i.agreement_uploaded
      );

      if (stagesWithAgreements.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">Geen stages met overeenkomsten gevonden.</td></tr>';
      } else {
        tbody.innerHTML = stagesWithAgreements.map(i => {
          const agreementStatus = i.agreement_status || 'Niet Ingediend';
          const statusClass = getStatusClass(agreementStatus);
          return `
            <tr data-id="${i.id}" class="agreement-row">
              <td>${i.student?.first_name || 'Onbekend'} ${i.student?.last_name || ''}</td>
              <td>${i.company?.name || 'Onbekend'}</td>
              <td><span class="status-pill ${getStatusClass(i.status)}">${i.status}</span></td>
              <td><span class="status-pill ${statusClass}">${agreementStatus}</span></td>
              <td>${i.agreement_uploaded ? '<span class="status-pill status-good">✓ Ja</span>' : '<span class="status-pill status-warn">✗ Nee</span>'}</td>
              <td>
                <button class="btn small view-agreement-btn" data-id="${i.id}">Bekijken</button>
              </td>
            </tr>
          `;
        }).join('');

        // Click handlers for view buttons
        tbody.querySelectorAll('.view-agreement-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = parseInt(btn.dataset.id);
            showAgreementDetailPanel(id);
          });
        });
      }
    }

    // Hide detail panel initially
    const panel = document.getElementById('agreement-detail-panel');
    if (panel) panel.style.display = 'none';

  } catch (error) {
    showToast(error.message, 'error');
  }
}

function showAgreementDetailPanel(internshipId) {
  const internship = allInternships.find(i => i.id === internshipId);
  if (!internship) return;

  // Update URL
  selectedInternshipId = internshipId;
  currentInternship = internship;
  const url = new URL(window.location.href);
  url.searchParams.set('internship', internshipId);
  window.history.replaceState({}, '', url);

  // Show panel
  const panel = document.getElementById('agreement-detail-panel');
  if (panel) panel.style.display = 'block';

  // Fill in student info
  document.getElementById('agreement-student-name').textContent =
    `${internship.student?.first_name || ''} ${internship.student?.last_name || ''}`;
  document.getElementById('agreement-company').textContent = internship.company?.name || 'Onbekend';
  document.getElementById('agreement-internship-status').textContent = internship.status;

  // Load agreement details
  const detailContainer = document.getElementById('agreement-detail-content');
  detailContainer.innerHTML = '<p>Laden...</p>';

  InternshipsAPI.get(internship.id).then(full => {
    const agreement = full.agreement;
    if (!agreement) {
      detailContainer.innerHTML = `
        <div class="info-message warning">
          <p>⚠️ Er is nog geen overeenkomst geüpload voor deze stage.</p>
        </div>
      `;
      document.getElementById('agreement-actions').innerHTML = '';
      return;
    }

    const insurance = agreement.insurance_verified
      ? { text: '✓ Verzekering gecontroleerd', class: 'status-good' }
      : { text: '✗ Verzekering nog niet gecontroleerd', class: 'status-warn' };

    detailContainer.innerHTML = `
      <div class="agreement-info">
        <p><strong>Status overeenkomst:</strong> <span class="status-pill ${getStatusClass(agreement.status)}">${agreement.status}</span></p>
        <p><strong>Verzekering:</strong> <span class="status-pill ${insurance.class}">${insurance.text}</span></p>
        <p><strong>Geüpload op:</strong> ${formatDate(agreement.uploaded_at) || 'Onbekend'}</p>
        <p><strong>Gevalideerd op:</strong> ${formatDate(agreement.validated_at) || 'Nog niet gevalideerd'}</p>
        ${agreement.file_path ? `
        <div style="margin-top: 1rem;">
          <button class="btn" id="download-agreement-btn" data-internship-id="${internship.id}">📄 PDF Downloaden</button>
        </div>
        ` : ''}
      </div>
    `;

    // Validation actions
    const actionsDiv = document.getElementById('agreement-actions');
    if (actionsDiv) {
      const isValidated = agreement.status === 'Gevalideerd';

      if (isValidated) {
        actionsDiv.innerHTML = `
          <div class="info-message success">
            <p>✓ Deze overeenkomst is gevalideerd. De stage is actief.</p>
          </div>
        `;
      } else {
        actionsDiv.innerHTML = `
          <div class="validation-form">
            <div class="row full" style="margin-bottom: 0.75rem;">
              <label>
                <input type="checkbox" id="insurance-check" ${agreement.insurance_verified ? 'checked' : ''} />
                Verzekering is in orde
              </label>
            </div>
            <div class="btn-group">
              <button id="btn-validate" class="btn success">✓ Valideren</button>
              <button id="btn-incomplete" class="btn danger">✗ Onvolledig</button>
            </div>
          </div>
        `;

        document.getElementById('btn-validate')?.addEventListener('click', () => {
          const insuranceVerified = document.getElementById('insurance-check')?.checked || false;
          validateAgreement(internship.id, 'Gevalideerd', insuranceVerified);
        });

        document.getElementById('btn-incomplete')?.addEventListener('click', () => {
          const insuranceVerified = document.getElementById('insurance-check')?.checked || false;
          validateAgreement(internship.id, 'Onvolledig', insuranceVerified);
        });
      }
    }

    // Attach download handler
    document.getElementById('download-agreement-btn')?.addEventListener('click', async () => {
      const btn = document.getElementById('download-agreement-btn');
      showLoading(btn, 'Downloaden...');
      try {
        await AgreementsAPI.download(internship.id);
        hideLoading(btn);
      } catch (error) {
        hideLoading(btn);
        showToast(error.message, 'error');
      }
    });
  }).catch(() => {
    detailContainer.innerHTML = '<p class="error">Kon overeenkomstgegevens niet laden.</p>';
  });
}

async function validateAgreement(internshipId, status, insuranceVerified) {
  try {
    await AgreementsAPI.validate(internshipId, status, insuranceVerified);
    showToast(`Overeenkomst gemarkeerd als ${status.toLowerCase()}!`, 'success');
    // Refresh data
    allInternships = await InternshipsAPI.list();
    renderCommitteeAgreements();
    // Refresh detail panel
    showAgreementDetailPanel(internshipId);
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
    tbody.innerHTML = '<tr><td colspan="6">Selecteer een stage via het navigatiemenu.</td></tr>';
    return;
  }

  if (currentLogbooks.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6">Geen logboeken gevonden voor deze stage.</td></tr>';
    return;
  }

  tbody.innerHTML = currentLogbooks.map(lb => {
    let actionCell;
    if (lb.mentor_validated) {
      actionCell = '<span class="status-pill status-good">✓ Gevalideerd</span>';
    } else if (lb.status === 'submitted') {
      actionCell = `<button class="btn small validate-logbook-btn" data-id="${lb.id}">Valideren</button>`;
    } else {
      actionCell = '<span class="status-pill">Concept</span>';
    }

    return `
      <tr data-logbook-id="${lb.id}">
        <td>${lb.week_number}</td>
        <td>${lb.tasks || '-'}</td>
        <td>${lb.reflection || '-'}</td>
        <td><span class="status-pill ${getStatusClass(lb.status)}">${lb.status === 'submitted' ? 'Ingediend' : 'Concept'}</span></td>
        <td>
          <textarea class="mentor-feedback-input" data-id="${lb.id}" rows="2" placeholder="Feedback voor deze week..." style="width:100%; min-width:160px; font-size:0.85rem;">${lb.mentor_feedback || ''}</textarea>
          <button class="btn small save-feedback-btn" data-id="${lb.id}" style="margin-top:0.25rem;">Opslaan</button>
        </td>
        <td>${actionCell}</td>
      </tr>
    `;
  }).join('');

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

  // Feedback opslaan knoppen verbinden
  tbody.querySelectorAll('.save-feedback-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const logbookId = parseInt(btn.dataset.id);
      const textarea = tbody.querySelector(`.mentor-feedback-input[data-id="${logbookId}"]`);
      const feedback = textarea?.value || '';
      showLoading(btn, 'Bezig...');
      try {
        await apiRequest(`/internships/logbooks/${logbookId}`, {
          method: 'PATCH',
          body: JSON.stringify({ mentor_feedback: feedback })
        });
        hideLoading(btn);
        showToast('Feedback opgeslagen!', 'success');
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

  // Zoek actieve evaluatie, anders de meest recente gefinaliseerde
  let actieveEval = currentEvaluations.find(e => !e.finalized);
  let isReadOnly = false;

  if (!actieveEval) {
    // Geen actieve evaluatie: toon laatste gefinaliseerde (final prefereert boven tussentijds)
    const finalized = currentEvaluations.filter(e => e.finalized);
    if (finalized.length > 0) {
      actieveEval = finalized.find(e => e.eval_type === 'final') || finalized[finalized.length - 1];
      isReadOnly = true;
    }
  }

  if (!actieveEval) {
    container.innerHTML = '<p>Geen evaluatie gevonden voor deze stage.</p>';
    return;
  }

  const readOnlyAttr = isReadOnly ? 'readonly' : '';
  const saveBtnHtml = isReadOnly
    ? '<p class="hint">Deze evaluatie is definitief afgesloten. Feedback kan niet meer worden gewijzigd.</p>'
    : '<button id="save-mentor-feedback" class="btn">Feedback Opslaan</button>';

  container.innerHTML = `
  <div style="margin-bottom: 1rem;">
    <span class="status-pill ${isReadOnly ? 'status-good' : 'status-info'}">${isReadOnly ? '✓ Afgeronde evaluatie' : 'Actieve evaluatie'}</span>
    <span class="hint" style="margin-left: 0.5rem;">${actieveEval.eval_type === 'final' ? 'Finale evaluatie' : 'Tussentijdse evaluatie'}</span>
  </div>
  ${currentCompetencies.map(comp => {
    const rule = actieveEval.rules?.find(r => r.competency_id === comp.id);
    const scoreLabel = rule?.score ? `${rule.score}/5` : '-';
    return `
      <div class="mentor-eval-row" style="margin-bottom: 1rem;">
        <label><strong>${comp.name}</strong> (${comp.weight}%)</label>
        <p style="margin: 0.25rem 0; font-size: 0.9rem; color: var(--ink-soft);">Score: <span class="score-highlight">${scoreLabel}</span></p>
        <textarea data-rule-id="${rule?.id ?? ''}" placeholder="Geef hier je feedback..." ${readOnlyAttr}>${rule?.evaluator_feedback || ''}</textarea>
      </div>
    `;
  }).join('')}
  ${saveBtnHtml}`;

  if (!isReadOnly) {
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