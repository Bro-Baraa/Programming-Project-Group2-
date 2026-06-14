// Stage Monitoring Tool

// Role waarden moeten overeenkomen met backend User.role
const roleViews = {
  student: ["dashboard", "voorstel", "logboek", "overeenkomst", "evaluaties"],
  committee: ["voorstellen", "overeenkomsten", "overzicht"],
  teacher: ["opvolging", "evaluatie", "eindoverzicht"],
  mentor: ["validatie", "evaluatie"],
  admin: ["competenties", "overeenkomsten", "gebruikers", "auditlog"],
};

const roleDisplayNames = {
  student: "Student",
  committee: "Stagecommissie",
  teacher: "Docent",
  mentor: "Stagementor",
  admin: "Administratie"
};

const tabIcons = {
  dashboard: 'home',
  voorstel: 'plus',
  logboek: 'book-open',
  overeenkomst: 'file-text',
  evaluaties: 'check-circle',
  voorstellen: 'search',
  overeenkomsten: 'file-text',
  overzicht: 'users',
  opvolging: 'book-open',
  evaluatie: 'check-circle',
  eindoverzicht: 'eye',
  validatie: 'check-circle',
  competenties: 'settings',
  gebruikers: 'users',
  auditlog: 'clock',
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
  "admin-overeenkomsten": "admin-overeenkomsten-template",
  "admin-gebruikers": "admin-gebruikers-template",
  "admin-auditlog": "admin-auditlog-template",
};

let allInternships = [];
let selectedInternshipId = null;
let currentCompetencies = [];
let currentLogbooks = [];
let currentEvaluations = [];
let currentFeedback = [];
let _renderGeneration = 0;

let _allInternshipsLoaded = false;
let _lastInternshipDataId = null;
let _lastCompetencyLoad = 0;
const _CACHE_TTL_MS = 30_000;

function getSelectedInternship() {
  return allInternships.find(i => i.id == selectedInternshipId) || allInternships[0] || null;
}

function toggleHeaderVisibility(show) {
  const topbar = document.querySelector('.topbar');
  if (topbar) topbar.style.display = show ? 'flex' : 'none';
}

let currentInternship = null;

const app = document.getElementById("app");
const navPanel = document.getElementById("nav-panel");
const content = document.getElementById("content");

function updateUIForUser(user) {
  const userInfo = document.getElementById('user-info');
  const userName = document.getElementById('user-name');
  const userRole = document.getElementById('user-role');

  if (userInfo && userName && userRole) {
    userInfo.style.display = 'flex';
    userName.textContent = `${user.first_name} ${user.last_name}`;
    userRole.textContent = roleDisplayNames[user.role] || user.role;
  }

  initNotifications();
}

async function handleLogin(e) {
  e.preventDefault();
  const emailInput = document.getElementById('login-email');
  const passwordInput = document.getElementById('login-password');
  const email = emailInput.value;
  const password = passwordInput.value;
  const submitBtn = e.target.querySelector('button[type="submit"]');
  const errorEl = document.getElementById('login-error');

  if (errorEl) {
    errorEl.textContent = '';
    errorEl.classList.remove('show');
  }
  emailInput?.removeAttribute('aria-invalid');
  passwordInput?.removeAttribute('aria-invalid');

  showLoading(submitBtn, "Inloggen...");

  try {
    const data = await AuthAPI.login(email, password);
    hideLoading(submitBtn);
    showToast(`Welkom, ${data.user.first_name}!`, 'success');
    // SPA navigation instead of full page reload (U1 fix)
    const url = new URL(window.location.href);
    url.searchParams.delete('view');
    window.history.replaceState({}, '', url);
    renderMainApp();
  } catch (error) {
    console.error('[DEBUG] Login error in handleLogin:', error.message);
    hideLoading(submitBtn);
    if (errorEl) {
      errorEl.textContent = error.message;
      errorEl.classList.add('show');
    } else {
      alert('Login fout: ' + error.message);
    }
    emailInput?.setAttribute('aria-invalid', 'true');
    passwordInput?.setAttribute('aria-invalid', 'true');
  }
}

function handleLogout() {
  destroyNotifications();
  AuthAPI.logout();
  showToast('Uitgelogd', 'info');
  // SPA navigation instead of full page reload (U1 fix)
  const url = new URL(window.location.href);
  url.searchParams.set('view', 'login');
  window.history.replaceState({}, '', url);
  renderLogin();
}

function renderLogin() {
  app.className = 'login-layout';
  // Keep #content attached so its cached reference stays valid. Clearing
  // app.textContent here would detach #content and break the next render.
  if (content.isConnected) {
    content.textContent = '';
  } else {
    app.textContent = '';
    app.appendChild(content);
  }
  navPanel.style.display = 'none';
  document.body.classList.add('login-active');

  toggleHeaderVisibility(false);

  const tpl = document.getElementById('login-template');
  if (tpl) {
    content.appendChild(tpl.content.cloneNode(true));

    const form = document.getElementById('login-form');
    form?.addEventListener('submit', handleLogin);

    const quickLogin = document.getElementById('quick-login');
    if (quickLogin) {
      quickLogin.textContent = '';
      const loadBtn = document.createElement('button');
      loadBtn.className = 'btn secondary';
      loadBtn.style.cssText = 'width:100%; font-size:0.9rem;';
      loadBtn.textContent = 'Test accounts laden';
      quickLogin.appendChild(loadBtn);

      loadBtn.addEventListener('click', () => {
        loadBtn.disabled = true;
        loadBtn.textContent = 'Laden...';
        fetch(`${API_BASE_URL}/users/seed`)
          .then(r => {
            if (!r.ok) {
              if (r.status === 0) {
                throw new Error('Kan geen verbinding maken met de backend. Is de server gestart?');
              }
              throw new Error(`Server fout: ${r.status}`);
            }
            return r.json();
          })
          .then(accounts => {
            if (!accounts.length) {
              quickLogin.textContent = '';
              const pNone = document.createElement('p');
              pNone.className = 'hint';
              pNone.textContent = 'Geen test accounts beschikbaar';
              quickLogin.appendChild(pNone);
              return;
            }
            const options = accounts.map(a =>
              `<option value="${a.email}">${a.first_name} ${a.last_name} (${a.role})</option>`
            ).join('');
            quickLogin.textContent = '';
            const lbl = document.createElement('label');
            lbl.htmlFor = 'quick-login-select';
            lbl.style.cssText = 'display:block; margin-bottom:0.25rem; font-size:0.85rem; color:var(--ink-soft);';
            lbl.textContent = 'Kies een test account:';
            const sel = document.createElement('select');
            sel.id = 'quick-login-select';
            sel.style.cssText = 'width:100%; margin-bottom:0.5rem;';
            sel.innerHTML = '<option value="">-- Account selecteren --</option>' + options;
            const btn = document.createElement('button');
            btn.className = 'btn';
            btn.id = 'quick-login-btn';
            btn.textContent = 'Inloggen';
            quickLogin.appendChild(lbl);
            quickLogin.appendChild(sel);
            quickLogin.appendChild(btn);
            document.getElementById('quick-login-btn')?.addEventListener('click', async (e) => {
              e.preventDefault();
              const select = document.getElementById('quick-login-select');
              const option = select?.selectedOptions[0];
              if (!option || !option.value) {
                showToast('Selecteer eerst een account', 'warning');
                return;
              }
              showLoading(btn, 'Inloggen...');
              try {
                const data = await AuthAPI.demoLogin(option.value);
                showToast(`Welkom, ${data.user.first_name}!`, 'success');
                const url = new URL(window.location.href);
                url.searchParams.delete('view');
                window.history.replaceState({}, '', url);
                renderMainApp();
              } catch (error) {
                showToast(error.message, 'error');
              } finally {
                hideLoading(btn);
              }
            });
          })
          .catch((err) => {
            quickLogin.textContent = '';
            const pErr = document.createElement('p');
            pErr.className = 'hint';
            pErr.textContent = err.message || 'Kon test accounts niet laden';
            quickLogin.appendChild(pErr);
            console.error('[Login] Failed to load seed accounts:', err);
          })
          .finally(() => {
            loadBtn.disabled = false;
            loadBtn.textContent = 'Test accounts laden';
          });
      });
    }
  }
}

async function renderMainApp() {
  app.className = 'layout';
  navPanel.style.display = 'block';
  document.body.classList.remove('login-active');

  toggleHeaderVisibility(true);

  // renderLogin() wipes #app (and with it #content). Recreate #content if it
  // was removed, otherwise the cached `content` reference is detached and every
  // render writes into a node that is not in the DOM (stale login screen stays).
  if (!content.isConnected) {
    app.textContent = '';
    app.appendChild(content);
  }

  // Refresh the header identity. On an in-app login (handleLogin -> renderMainApp)
  // init()/updateUIForUser() does NOT run, so without this the name/role keep the
  // previous account's values until a page refresh.
  const currentUser = AuthAPI.getUser();
  if (currentUser) updateUIForUser(currentUser);

  const role = AuthAPI.getRole();
  const views = roleViews[role] || [];

  const viewTabs = document.getElementById('view-tabs');
  viewTabs.textContent = '';
  viewTabs.setAttribute('role', 'tablist');
  views.forEach((view) => {
    const li = document.createElement('li');
    const btn = document.createElement('button');
    btn.className = 'nav-tab';
    btn.dataset.view = view;
    const iconName = tabIcons[view];
    const icon = iconName ? iconHtml(iconName, 16, { class: 'icon-img tab-icon' }) + ' ' : '';
    btn.innerHTML = icon + view.charAt(0).toUpperCase() + view.slice(1);
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

let _firstRender = true;

const _internshipViews = new Set([
  'dashboard', 'voorstel', 'logboek', 'overeenkomst', 'evaluaties',
  'opvolging', 'validatie', 'eindoverzicht', 'teacher-evaluatie', 'mentor-evaluatie'
]);

const _competencyViews = new Set([
  'evaluatie', 'teacher-evaluatie', 'mentor-evaluatie', 'competenties', 'eindoverzicht'
]);

async function loadAllInternships() {
  const all = [];
  let skip = 0;
  const limit = 200;
  while (true) {
    const batch = await InternshipsAPI.list(null, skip, limit);
    all.push(...batch);
    if (batch.length < limit) break;
    skip += limit;
  }
  return all;
}

async function renderView() {
  const role = AuthAPI.getRole();
  const views = roleViews[role] || [];

  let urlParams = new URLSearchParams(window.location.search);
  let view = urlParams.get('view');
  if (!view || !views.includes(view)) {
    view = views[0] || '';
  }

  document.querySelectorAll('.nav-tab').forEach(tab => {
    const isActive = tab.dataset.view === view;
    tab.classList.toggle('active', isActive);
    tab.setAttribute('aria-selected', String(isActive));
    tab.setAttribute('tabindex', isActive ? '0' : '-1');
  });

  // Announce tab change for screen readers (A5 fix)
  const announcer = document.getElementById('tab-announcer');
  if (announcer) {
    const viewName = view.charAt(0).toUpperCase() + view.slice(1);
    announcer.textContent = `Navigatie: ${viewName} tab geactiveerd`;
  }

  const loadingOverlay = document.createElement('div');
  loadingOverlay.className = 'loading-overlay';
  const spinner = document.createElement('span');
  spinner.className = 'loading-spinner';
  loadingOverlay.appendChild(spinner);
  loadingOverlay.appendChild(document.createTextNode(' Laden...'));
  // Timeout message for loading (U2 fix)
  const timeoutMsg = document.createElement('p');
  timeoutMsg.className = 'loading-timeout';
  timeoutMsg.style.cssText = 'margin-top: 1rem; color: var(--ink-soft); font-size: 0.9rem; display: none;';
  timeoutMsg.textContent = 'Dit duurt langer dan verwacht. Controleer je internetverbinding of probeer het later opnieuw.';
  loadingOverlay.appendChild(timeoutMsg);
  content.replaceChildren(loadingOverlay);

  // Show timeout message after 10 seconds
  const loadingTimeout = setTimeout(() => {
    if (timeoutMsg) timeoutMsg.style.display = 'block';
  }, 10000);

  const key = view ? `${role}-${view}` : role;
  const templateId = templates[key] || templates[role];

  const gen = ++_renderGeneration;

  try {
    urlParams = new URLSearchParams(window.location.search);
    const internshipParam = urlParams.get('internship');
    if (internshipParam) selectedInternshipId = parseInt(internshipParam);

    if (!_allInternshipsLoaded || allInternships.length === 0) {
      allInternships = await loadAllInternships();
      _allInternshipsLoaded = true;
    }

    if (gen !== _renderGeneration) return;

    populateInternshipSelector(role);
    currentInternship = getSelectedInternship();

    const needsInternshipData = _internshipViews.has(view);
    const internshipChanged = currentInternship?.id !== _lastInternshipDataId;
    if (needsInternshipData && currentInternship) {
      if (internshipChanged || currentLogbooks.length === 0) {
        [currentLogbooks, currentEvaluations, currentFeedback] = await Promise.all([
          InternshipsAPI.getLogbooks(currentInternship.id),
          InternshipsAPI.getEvaluations(currentInternship.id),
          InternshipsAPI.getFeedback(currentInternship.id)
        ]);
        _lastInternshipDataId = currentInternship.id;
      }
    } else {
      currentLogbooks = [];
      currentEvaluations = [];
      currentFeedback = [];
    }

    if (gen !== _renderGeneration) return;

    const needsCompetencies = _competencyViews.has(view);
    const now = Date.now();
    if (needsCompetencies && (currentCompetencies.length === 0 || (now - _lastCompetencyLoad) > _CACHE_TTL_MS)) {
      currentCompetencies = await CompetenciesAPI.list();
      _lastCompetencyLoad = now;
    } else if (!needsCompetencies) {
      currentCompetencies = [];
    }

    if (gen !== _renderGeneration) return;

    clearTimeout(loadingTimeout);
    content.textContent = '';
    const tpl = document.getElementById(templateId);
    if (tpl) {
      content.appendChild(tpl.content.cloneNode(true));
      content.classList.add('content-fade-in');
      const panels = content.querySelectorAll('.panel, .grid');
      panels.forEach((el, i) => {
        el.classList.add('reveal-stagger');
        el.style.setProperty('--panel-i', i);
      });
      content.addEventListener('animationend', () => {
        content.classList.remove('content-fade-in');
      }, { once: true });
      if (_firstRender) {
        _firstRender = false;
      }
      await wireRoleInteractions(role, view);
      if (typeof removeTableCards === 'function' && typeof buildTableCards === 'function') {
        removeTableCards();
        if (window.innerWidth <= 720) {
          buildTableCards();
        }
      }
    }

    if (gen !== _renderGeneration) return;

    const firstHeading = content.querySelector('h2');
    if (firstHeading) {
      firstHeading.setAttribute('tabindex', '-1');
      firstHeading.focus({ preventScroll: true });
    }

    if (needsInternshipData && !currentInternship && !content.querySelector('.error-message')) {
      const emptyDiv = document.createElement('div');
      emptyDiv.className = 'panel card info-message';
      emptyDiv.innerHTML = `
        <h2>Geen stage gevonden</h2>
        <p>Je hebt nog geen stage ingediend. Dien een voorstel in via het tabblad <strong>Voorstel</strong> om te beginnen.</p>
        <a href="?view=voorstel" class="btn">Stagevoorstel indienen</a>
      `;
      content.replaceChildren(emptyDiv);
    }

    inlineIconsInContainer(content);
  } catch (error) {
    if (gen !== _renderGeneration) return;
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = `Fout bij laden: ${error.message}`;
    content.replaceChildren(errorDiv);
  }
}

function populateInternshipSelector(role) {
  const wrapper = document.getElementById('internship-selector-wrapper');
  const select = document.getElementById('internship-select');
  if (!wrapper || !select) return;

  if (allInternships.length === 0) {
    wrapper.style.display = 'none';
    return;
  }

  const showSelector = allInternships.length > 1 || role !== 'student';
  if (!showSelector) {
    wrapper.style.display = 'none';
    return;
  }

  wrapper.style.display = 'block';
  select.textContent = '';

  allInternships.forEach(i => {
    const option = document.createElement('option');
    option.value = i.id;
    const label = i.student
      ? `${i.student.first_name} ${i.student.last_name}, ${i.company?.name || 'Onbekend'} (${i.status})`
      : `Stage ${i.id}, ${i.status}`;
    option.textContent = label;
    select.appendChild(option);
  });

  const targetId = selectedInternshipId || allInternships[0]?.id;
  if (targetId) select.value = targetId;
}

function handleInternshipChange() {
  const select = document.getElementById('internship-select');
  if (!select) return;
  const newId = parseInt(select.value);
  if (newId === selectedInternshipId) return;

  selectedInternshipId = newId;
  currentInternship = getSelectedInternship();

  const url = new URL(window.location.href);
  url.searchParams.set('internship', newId);
  window.history.replaceState({}, '', url);

  renderView();
}

async function refreshInternshipData() {
  try {
    _allInternshipsLoaded = false;
    _lastInternshipDataId = null;

    allInternships = await loadAllInternships();
    _allInternshipsLoaded = true;
    currentInternship = getSelectedInternship();

    const role = AuthAPI.getRole();
    populateInternshipSelector(role);

    if (currentInternship) {
      [currentLogbooks, currentEvaluations, currentFeedback] = await Promise.all([
        InternshipsAPI.getLogbooks(currentInternship.id),
        InternshipsAPI.getEvaluations(currentInternship.id),
        InternshipsAPI.getFeedback(currentInternship.id)
      ]);
      _lastInternshipDataId = currentInternship.id;
    } else {
      currentLogbooks = [];
      currentEvaluations = [];
      currentFeedback = [];
    }
  } catch (error) {
    console.error('Failed to refresh internship data:', error);
  }
}

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
      overeenkomsten: renderAdminAgreements,
      gebruikers: renderUserManager,
      auditlog: renderAuditLog,
    },
  };

  const handler = handlers[role]?.[view];
  if (handler) await handler();

  enhanceViewTables(role, view);
}

function enhanceViewTables(role, view) {
  if (role === "committee" && view === "voorstellen") {
    enhanceTable(document.getElementById("proposals-table"), {
      search: true,
      searchPlaceholder: "Zoek op student, bedrijf of status...",
      filterColumn: 3,
      filterLabel: "Alle statussen",
      sort: true,
    });
  }

  if (role === "committee" && view === "overeenkomsten") {
    enhanceTable(document.getElementById("agreements-table"), {
      search: true,
      searchPlaceholder: "Zoek op student of bedrijf...",
      filterColumn: 3,
      filterLabel: "Alle overeenkomst-statussen",
      sort: true,
      skipSortColumns: [5],
    });
  }

  if (role === "committee" && view === "overzicht") {
    enhanceTable(document.getElementById("committee-overview-table"), {
      search: true,
      searchPlaceholder: "Zoek op student of bedrijf...",
      filterColumn: 3,
      filterLabel: "Alle statussen",
      sort: true,
    });
  }

  if (role === "admin" && view === "overeenkomsten") {
    enhanceTable(document.getElementById("admin-agreements-table"), {
      search: true,
      searchPlaceholder: "Zoek op student of status...",
      filterColumn: 2,
      filterLabel: "Alle overeenkomst-statussen",
      sort: true,
      skipSortColumns: [4],
    });
  }

  if (role === "admin" && view === "gebruikers") {
    enhanceTable(document.getElementById("users-table"), {
      sort: true,
      skipSortColumns: [4],
    });

    const userSearch = document.getElementById("user-search");
    const userSearchBtn = document.getElementById("user-search-btn");
    if (userSearch && userSearchBtn && !userSearch.dataset.liveSearch) {
      userSearch.dataset.liveSearch = "true";
      userSearch.addEventListener("input", debounce(function () {
        userSearchBtn.click();
      }, 300));
    }
  }

  if (role === "admin" && view === "auditlog") {
    enhanceTable(document.getElementById("audit-table"), {
      sort: true,
    });
  }
}

function formatReportRows(rules) {
  return rules.map(r => {
    const name = escapeHtml(r.competency?.name || 'Onbekend');
    const weight = r.competency?.weight !== undefined ? r.competency.weight : '-';
    return `
      <tr>
        <td>${name}</td>
        <td>${weight !== '-' ? weight + '%' : '-'}</td>
        <td>${r.score !== null && r.score !== undefined ? r.score : '-'}</td>
        <td>${escapeHtml(r.student_description || '-')}</td>
        <td>${escapeHtml(r.evaluator_feedback || '-')}</td>
      </tr>
    `;
  }).join('');
}

async function init() {
  const urlParams = new URLSearchParams(window.location.search);
  const view = urlParams.get('view');

  if (view === 'login') {
    renderLogin();
  } else {
    // Always verify session via cookie — sessionStorage may be stale (e.g. after switching accounts)
    try {
      const user = await AuthAPI.getMe();
      if (user) {
        AuthAPI.setUser(user);
        updateUIForUser(user);
        renderMainApp();
      } else {
        renderLogin();
      }
    } catch {
      renderLogin();
    }
  }

  document.getElementById('internship-select')?.addEventListener('change', handleInternshipChange);
  document.getElementById('logout-btn')?.addEventListener('click', handleLogout);
  inlineIconsInContainer(document.body);
}

init();
