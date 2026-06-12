// ============================================
// Admin - Competentiebeheer
// ============================================

let competencyProfiles = [];
let selectedProfileId = null;
let compSearchQuery = '';
let compShowInactive = false;
let compEditId = null;

async function renderCompetencyManager() {
  const list = document.getElementById('competency-list');
  const scoreInputs = document.getElementById('score-inputs');
  const weightCheck = document.getElementById('weight-check');
  const profileSelect = document.getElementById('profile-select');
  const weightChart = document.getElementById('weight-chart');
  const compSearch = document.getElementById('comp-search');
  const showInactive = document.getElementById('show-inactive');

  // Load profiles first
  try {
    competencyProfiles = await CompetencyProfileAPI.list();
  } catch (error) {
    showToast('Kon profielen niet laden', 'error');
    competencyProfiles = [];
  }

  // Populate profile selector
  if (profileSelect) {
    profileSelect.innerHTML = competencyProfiles.length
      ? competencyProfiles.map(p =>
        `<option value="${p.id}" ${p.active ? 'selected' : ''}>${p.name} (${p.academic_year})${p.active ? ' (actief)' : ''}</option>`
      ).join('')
      : '<option value="">Geen profielen</option>';

    // Auto-select active profile if none selected
    const activeProfile = competencyProfiles.find(p => p.active);
    if (activeProfile && !selectedProfileId) {
      selectedProfileId = activeProfile.id;
      profileSelect.value = activeProfile.id;
    } else if (selectedProfileId) {
      profileSelect.value = selectedProfileId;
    }

    profileSelect.addEventListener('change', async () => {
      selectedProfileId = parseInt(profileSelect.value) || null;
      await loadCompetencies();
      renderCompetencies();
      renderScoreSimulator();
      renderWeightChart();
    });
  }

  // Load competencies for selected profile
  await loadCompetencies();

  function renderCompetencies() {
    if (!list) return;

    let filtered = currentCompetencies;
    if (!compShowInactive) {
      filtered = filtered.filter(c => c.active);
    }
    if (compSearchQuery) {
      const q = compSearchQuery.toLowerCase();
      filtered = filtered.filter(c => c.name.toLowerCase().includes(q));
    }

    if (filtered.length === 0) {
      list.innerHTML = '<li class="comp-empty">Geen competenties gevonden</li>';
    } else {
      list.innerHTML = filtered.map(comp => {
        const isEditing = compEditId === comp.id;
        const isInactive = !comp.active;
        return `
          <li class="comp-item ${isInactive ? 'comp-inactive' : ''}">
            ${isEditing ? `
              <div class="comp-edit-row">
                <input type="text" id="edit-name-${comp.id}" value="${escapeHtml(comp.name)}" />
                <input type="text" id="edit-desc-${comp.id}" value="${escapeHtml(comp.description || '')}" placeholder="Beschrijving" />
                <input type="number" id="edit-weight-${comp.id}" value="${comp.weight}" min="0" max="100" />
                <button class="btn small" onclick="saveCompetencyEdit(${comp.id})">${iconHtml('check-circle', 14)} Opslaan</button>
                <button class="btn small secondary" onclick="cancelCompetencyEdit()">${iconHtml('x-circle', 14)} Annuleren</button>
              </div>
            ` : `
              <div class="comp-row">
                <div class="comp-info">
                  <span class="comp-name">${escapeHtml(comp.name)}</span>
                  <span class="comp-weight">${comp.weight}%</span>
                  ${isInactive ? '<span class="comp-status-badge inactive">Inactief</span>' : ''}
                </div>
                ${comp.description ? `<div class="comp-desc">${escapeHtml(comp.description)}</div>` : ''}
                <div class="comp-actions">
                  <button class="btn small" onclick="startCompetencyEdit(${comp.id})">${iconHtml('edit', 14)} Bewerk</button>
                  ${isInactive
            ? `<button class="btn small success" onclick="activateCompetency(${comp.id})">${iconHtml('check-circle', 14)} Heractiveer</button>`
            : `<button class="btn small secondary" onclick="deactivateCompetency(${comp.id})">${iconHtml('x-circle', 14)} Deactiveer</button>`
          }
                  <button class="btn small danger" onclick="deleteCompetency(${comp.id})">${iconHtml('trash', 14)} Verwijder</button>
                </div>
              </div>
            `}
          </li>
        `;
      }).join('');
    }

    const total = currentCompetencies.filter(c => c.active).reduce((sum, c) => sum + c.weight, 0);
    const valid = Math.abs(total - 100) < 0.01;
    if (weightCheck) {
      weightCheck.textContent = `Totaal gewicht (actief): ${total}% ${valid ? 'OK' : 'Moet 100% zijn'}`;
      weightCheck.className = `weight-check ${valid ? 'valid' : 'invalid'}`;
    }
  }

  function renderScoreSimulator() {
    if (!scoreInputs) return;
    const activeComps = currentCompetencies.filter(c => c.active);
    scoreInputs.innerHTML = activeComps.map(comp => `
      <div class="row score-row">
        <label>${escapeHtml(comp.name)} (${comp.weight}%)</label>
        <input type="number" min="1" max="5" value="3" data-comp="${comp.id}" />
      </div>
    `).join('');
  }

  function renderWeightChart() {
    if (!weightChart) return;
    const activeComps = currentCompetencies.filter(c => c.active);
    if (activeComps.length === 0) {
      weightChart.innerHTML = '<p class="hint">Geen actieve competenties</p>';
      return;
    }
    const total = activeComps.reduce((sum, c) => sum + c.weight, 0);
    const colors = ['var(--accent)', 'var(--accent-2)', 'var(--good)', 'var(--warn)', 'var(--bad)', '#8b5cf6', '#ec4899', '#14b8a6'];
    let colorIdx = 0;
    const segments = activeComps.map(comp => {
      const pct = total > 0 ? (comp.weight / total) * 100 : 0;
      const color = colors[colorIdx % colors.length];
      colorIdx++;
      return { name: comp.name, pct, color, weight: comp.weight };
    });

    const barHtml = segments.map(s =>
      `<div class="chart-segment" style="width: ${s.pct}%; background: ${s.color};" title="${escapeHtml(s.name)}: ${s.weight}% (${s.pct.toFixed(1)}%)"></div>`
    ).join('');

    const legendHtml = segments.map(s =>
      `<div class="chart-legend-item">
        <span class="chart-dot" style="background: ${s.color}"></span>
        <span class="chart-label">${escapeHtml(s.name)} (${s.weight}%)</span>
      </div>`
    ).join('');

    weightChart.innerHTML = `
      <div class="chart-bar">${barHtml}</div>
      <div class="chart-legend">${legendHtml}</div>
    `;
  }

  // Search
  compSearch?.addEventListener('input', (e) => {
    compSearchQuery = e.target.value.trim();
    renderCompetencies();
  });

  // Show inactive toggle
  showInactive?.addEventListener('change', async (e) => {
    compShowInactive = e.target.checked;
    await loadCompetencies();
    renderCompetencies();
    renderScoreSimulator();
    renderWeightChart();
  });

  // Add form
  const form = document.getElementById('competency-form');
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('comp-name').value;
    const description = document.getElementById('comp-desc').value;
    const weight = parseFloat(document.getElementById('comp-weight').value);
    const submitBtn = form.querySelector('button[type="submit"]');

    if (!selectedProfileId) {
      showToast('Selecteer eerst een profiel', 'error');
      return;
    }

    showLoading(submitBtn, 'Toevoegen...');

    try {
      const newComp = await CompetenciesAPI.create({
        name,
        description: description || null,
        weight,
        profile_id: selectedProfileId
      });
      currentCompetencies.push(newComp);
      renderCompetencies();
      renderScoreSimulator();
      renderWeightChart();
      hideLoading(submitBtn);
      showToast(`Competentie "${name}" toegevoegd`, 'success');
      form.reset();
    } catch (error) {
      hideLoading(submitBtn);
      showToast(error.message, 'error');
    }
  });

  // Bulk add toggle
  const bulkToggle = document.getElementById('bulk-add-toggle');
  const bulkPanel = document.getElementById('bulk-add-panel');
  bulkToggle?.addEventListener('click', () => {
    const isHidden = bulkPanel.style.display === 'none';
    bulkPanel.style.display = isHidden ? 'block' : 'none';
    bulkToggle.innerHTML = isHidden ? '<img src="icons/plus.svg" alt="" width="14" height="14" class="icon-img" /> − Bulk toevoegen' : '<img src="icons/plus.svg" alt="" width="14" height="14" class="icon-img" /> + Bulk toevoegen';
  });

  // Bulk add
  const bulkBtn = document.getElementById('bulk-add-btn');
  bulkBtn?.addEventListener('click', async () => {
    const textarea = document.getElementById('bulk-add-text');
    const text = textarea.value.trim();
    if (!text) return;

    const lines = text.split('\n').filter(l => l.trim());
    const competencies = [];
    for (const line of lines) {
      const parts = line.split('|').map(p => p.trim());
      if (parts.length >= 2) {
        const weight = parseFloat(parts[1]);
        if (!isNaN(weight)) {
          competencies.push({
            name: parts[0],
            weight,
            description: parts[2] || null
          });
        }
      }
    }

    if (competencies.length === 0) {
      showToast('Geen geldige competenties gevonden', 'error');
      return;
    }

    if (!selectedProfileId) {
      showToast('Selecteer eerst een profiel', 'error');
      return;
    }

    showLoading(bulkBtn, 'Toevoegen...');
    try {
      const created = await CompetenciesAPI.createBulk({
        profile_id: selectedProfileId,
        competencies
      });
      currentCompetencies.push(...created);
      renderCompetencies();
      renderScoreSimulator();
      renderWeightChart();
      hideLoading(bulkBtn);
      showToast(`${created.length} competenties toegevoegd`, 'success');
      textarea.value = '';
      bulkPanel.style.display = 'none';
      bulkToggle.innerHTML = '<img src="icons/plus.svg" alt="" width="14" height="14" class="icon-img" /> + Bulk toevoegen';
    } catch (error) {
      hideLoading(bulkBtn);
      showToast(error.message, 'error');
    }
  });

  // Score calculator
  const calcBtn = document.getElementById('calc-score');
  calcBtn?.addEventListener('click', () => {
    const activeComps = currentCompetencies.filter(c => c.active);
    const total = activeComps.reduce((sum, c) => sum + c.weight, 0);
    if (Math.abs(total - 100) > 0.01) {
      showToast('Gewichten moeten 100% zijn', 'error');
      return;
    }

    let score = 0;
    document.querySelectorAll('#score-inputs input').forEach(input => {
      const compId = parseInt(input.dataset.comp);
      const comp = activeComps.find(c => c.id === compId);
      if (comp) {
        score += comp.weight * parseInt(input.value || 3);
      }
    });
    score = score / 100;

    const resultEl = document.getElementById('score-result');
    resultEl.textContent = `Gewogen eindscore: ${score.toFixed(2)} / 5`;
    resultEl.className = 'result success';
    showToast(`Eindscore: ${score.toFixed(2)} / 5`, 'success');
  });

  // Profile modal
  const manageProfilesBtn = document.getElementById('manage-profiles-btn');
  const profileModal = document.getElementById('profile-modal');
  const closeProfileModal = document.getElementById('close-profile-modal');
  const profileForm = document.getElementById('profile-form');
  const profileList = document.getElementById('profile-list');

  function renderProfileList() {
    if (!profileList) return;
    if (competencyProfiles.length === 0) {
      profileList.innerHTML = '<p class="hint">Geen profielen</p>';
      return;
    }
    profileList.innerHTML = competencyProfiles.map(p => `
      <div class="profile-item ${p.active ? 'profile-active' : ''}">
        <div class="profile-info">
          <strong>${escapeHtml(p.name)}</strong>
          <span class="profile-meta">${p.version ? 'v' + p.version + ' · ' : ''}${p.academic_year}${p.active ? ' · Actief' : ''}</span>
        </div>
        <div class="profile-actions">
          ${!p.active ? `<button class="btn small" onclick="activateProfile(${p.id})">${iconHtml('check-circle', 14)} Activeren</button>` : ''}
          <button class="btn small danger" onclick="deleteProfile(${p.id})">${iconHtml('trash', 14)} Verwijder</button>
        </div>
      </div>
    `).join('');
  }

  manageProfilesBtn?.addEventListener('click', () => {
    profileModal.style.display = 'block';
    renderProfileList();
  });

  closeProfileModal?.addEventListener('click', () => {
    profileModal.style.display = 'none';
  });

  profileModal?.querySelector('.modal-overlay')?.addEventListener('click', () => {
    profileModal.style.display = 'none';
  });

  profileForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('profile-name').value;
    const version = document.getElementById('profile-version').value;
    const academicYear = document.getElementById('profile-year').value;
    const active = document.getElementById('profile-active').checked;
    const submitBtn = profileForm.querySelector('button[type="submit"]');

    showLoading(submitBtn, 'Aanmaken...');
    try {
      const profile = await CompetencyProfileAPI.create({
        name,
        version: version || '1.0',
        academic_year: academicYear,
        active
      });
      competencyProfiles.push(profile);
      if (active) {
        selectedProfileId = profile.id;
      }
      renderProfileList();
      // Refresh profile selector
      if (profileSelect) {
        profileSelect.innerHTML = competencyProfiles.map(p =>
          `<option value="${p.id}" ${p.id === selectedProfileId ? 'selected' : ''}>${p.name} (${p.academic_year})${p.active ? ' (actief)' : ''}</option>`
        ).join('');
      }
      await loadCompetencies();
      renderCompetencies();
      renderScoreSimulator();
      renderWeightChart();
      hideLoading(submitBtn);
      showToast(`Profiel "${name}" aangemaakt`, 'success');
      profileForm.reset();
    } catch (error) {
      hideLoading(submitBtn);
      showToast(error.message, 'error');
    }
  });

  // Initial render
  renderCompetencies();
  renderScoreSimulator();
  renderWeightChart();
}

async function loadCompetencies() {
  try {
    currentCompetencies = await CompetenciesAPI.list(selectedProfileId, false, null, 0, 100);
  } catch (error) {
    showToast('Kon competenties niet laden', 'error');
    currentCompetencies = [];
  }
}

function startCompetencyEdit(id) {
  compEditId = id;
  renderCompetencyManager();
}

function cancelCompetencyEdit() {
  compEditId = null;
  renderCompetencyManager();
}

async function saveCompetencyEdit(id) {
  const name = document.getElementById(`edit-name-${id}`).value;
  const description = document.getElementById(`edit-desc-${id}`).value;
  const weight = parseFloat(document.getElementById(`edit-weight-${id}`).value);

  try {
    const updated = await CompetenciesAPI.update(id, {
      name: name || undefined,
      description: description || undefined,
      weight: !isNaN(weight) ? weight : undefined
    });
    const idx = currentCompetencies.findIndex(c => c.id === id);
    if (idx !== -1) currentCompetencies[idx] = updated;
    compEditId = null;
    renderCompetencyManager();
    showToast('Competentie bijgewerkt', 'success');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function deactivateCompetency(id) {
  try {
    await CompetenciesAPI.deactivate(id);
    const comp = currentCompetencies.find(c => c.id === id);
    if (comp) comp.active = false;
    renderCompetencyManager();
    showToast('Competentie gedeactiveerd', 'info');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function activateCompetency(id) {
  try {
    await CompetenciesAPI.update(id, { active: true });
    const comp = currentCompetencies.find(c => c.id === id);
    if (comp) comp.active = true;
    renderCompetencyManager();
    showToast('Competentie heractiveerd', 'success');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function deleteCompetency(id) {
  const comp = currentCompetencies.find(c => c.id === id);
  const name = comp ? comp.name : 'deze competentie';
  try {
    await showConfirmModal({
      title: 'Competentie verwijderen',
      message: `Competentie "${name}" definitief verwijderen? Dit kan niet ongedaan worden gemaakt.`,
      okText: 'Verwijderen',
      okClass: 'danger'
    });
    await CompetenciesAPI.delete(id);
    currentCompetencies = currentCompetencies.filter(c => c.id !== id);
    renderCompetencyManager();
    showToast('Competentie verwijderd', 'info');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function activateProfile(id) {
  try {
    await CompetencyProfileAPI.update(id, { active: true });
    competencyProfiles.forEach(p => { p.active = p.id === id; });
    selectedProfileId = id;
    renderCompetencyManager();
    showToast('Profiel geactiveerd', 'success');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function deleteProfile(id) {
  const profile = competencyProfiles.find(p => p.id === id);
  const name = profile ? profile.name : 'dit profiel';
  if (!confirm(`Profiel "${name}" verwijderen? Alle bijbehorende competenties worden ook verwijderd.`)) return;

  try {
    await CompetencyProfileAPI.delete(id);
    competencyProfiles = competencyProfiles.filter(p => p.id !== id);
    if (selectedProfileId === id) {
      const active = competencyProfiles.find(p => p.active);
      selectedProfileId = active ? active.id : (competencyProfiles[0]?.id || null);
    }
    renderCompetencyManager();
    showToast('Profiel verwijderd', 'info');
  } catch (error) {
    showToast(error.message, 'error');
  }
}

// Blootstellen aan window voor template onclick-handlers
window.startCompetencyEdit = startCompetencyEdit;
window.cancelCompetencyEdit = cancelCompetencyEdit;
window.saveCompetencyEdit = saveCompetencyEdit;
window.deactivateCompetency = deactivateCompetency;
window.activateCompetency = activateCompetency;
window.deleteCompetency = deleteCompetency;
window.activateProfile = activateProfile;
window.deleteProfile = deleteProfile;

// ============================================
// Admin - Gebruikersbeheer
// ============================================

let currentUsers = [];
let userSearchQuery = '';
let userRoleFilter = '';
let userShowInactive = false;
let userSkip = 0;
const userLimit = 20;

async function renderUserManager() {
  const table = document.getElementById('users-table');
  const tbody = table?.querySelector('tbody');
  const pagination = document.getElementById('user-pagination');
  const formPanel = document.getElementById('user-form-panel');

  async function loadUsers() {
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="5">Laden...</td></tr>';
    }
    try {
      const users = await UsersAPI.list(userRoleFilter || null, userSearchQuery || null, !userShowInactive, userSkip, userLimit);
      currentUsers = users;
      renderUserList();
    } catch (error) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="5">Fout: ${escapeHtml(error.message)}</td></tr>`;
    }
  }

  function renderUserList() {
    _renderUserTable();
  }

  // Search and filter handlers
  const searchBtn = document.getElementById('user-search-btn');
  const searchInput = document.getElementById('user-search');
  const roleFilter = document.getElementById('user-role-filter');

  searchBtn?.addEventListener('click', () => {
    userSearchQuery = searchInput.value.trim();
    userRoleFilter = roleFilter.value;
    userSkip = 0;
    loadUsers();
  });

  searchInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      userSearchQuery = searchInput.value.trim();
      userRoleFilter = roleFilter.value;
      userSkip = 0;
      loadUsers();
    }
  });

  roleFilter?.addEventListener('change', () => {
    userRoleFilter = roleFilter.value;
    userSkip = 0;
    loadUsers();
  });

  const showInactiveCheckbox = document.getElementById('user-show-inactive');
  showInactiveCheckbox?.addEventListener('change', () => {
    userShowInactive = showInactiveCheckbox.checked;
    userSkip = 0;
    loadUsers();
  });

  // Create button
  document.getElementById('user-create-btn')?.addEventListener('click', () => {
    showUserForm();
  });

  // Cancel button
  document.getElementById('user-cancel-btn')?.addEventListener('click', () => {
    formPanel.style.display = 'none';
  });

  // Form submit
  const form = document.getElementById('user-form');
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = document.getElementById('user-submit-btn');
    const userId = document.getElementById('user-form-id').value;

    const data = {
      email: document.getElementById('user-email').value,
      first_name: document.getElementById('user-first-name').value,
      last_name: document.getElementById('user-last-name').value,
      role: document.getElementById('user-role').value,
      is_active: document.getElementById('user-is-active').checked,
    };

    if (!userId) {
      data.password = document.getElementById('user-password').value;
    }

    showLoading(submitBtn, userId ? 'Wijzigen...' : 'Aanmaken...');

    try {
      if (userId) {
        await UsersAPI.update(parseInt(userId), data);
        showToast('Gebruiker gewijzigd', 'success');
      } else {
        await UsersAPI.create(data);
        showToast('Gebruiker aangemaakt', 'success');
      }
      formPanel.style.display = 'none';
      form.reset();
      await loadUsers();
    } catch (error) {
      showToast(error.message, 'error');
    } finally {
      hideLoading(submitBtn);
    }
  });

  // Initial load
  loadUsers();
}

function showUserForm(user = null) {
  const formPanel = document.getElementById('user-form-panel');
  const formTitle = document.getElementById('user-form-title');
  const formId = document.getElementById('user-form-id');
  const passwordRow = document.getElementById('user-password-row');
  const submitBtn = document.getElementById('user-submit-btn');

  formTitle.textContent = user ? 'Gebruiker bewerken' : 'Gebruiker aanmaken';
  formId.value = user ? user.id : '';
  document.getElementById('user-first-name').value = user ? user.first_name : '';
  document.getElementById('user-last-name').value = user ? user.last_name : '';
  document.getElementById('user-email').value = user ? user.email : '';
  document.getElementById('user-role').value = user ? user.role : 'student';
  document.getElementById('user-is-active').checked = user ? user.is_active : true;
  document.getElementById('user-password').value = '';

  // Password only required for new users
  passwordRow.style.display = user ? 'none' : 'block';
  document.getElementById('user-password').required = !user;
  submitBtn.textContent = user ? 'Wijzigingen opslaan' : 'Aanmaken';

  formPanel.style.display = 'block';
  formPanel.scrollIntoView({ behavior: 'smooth' });
}

async function handleEditUser(id) {
  const user = currentUsers.find(u => u.id === id);
  if (!user) {
    try {
      const fetched = await UsersAPI.get(id);
      showUserForm(fetched);
    } catch (error) {
      showToast(error.message, 'error');
    }
    return;
  }
  showUserForm(user);
}

async function handleDeleteUser(id) {
  const user = currentUsers.find(u => u.id === id);
  const name = user ? `${user.first_name} ${user.last_name}` : 'deze gebruiker';
  if (!confirm(`Gebruiker "${name}" verwijderen?`)) return;

  try {
    await UsersAPI.delete(id);
    currentUsers = currentUsers.filter(u => u.id !== id);
    showToast('Gebruiker verwijderd', 'info');
    _renderUserTable();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function changeUserPage(delta) {
  userSkip = Math.max(0, userSkip + delta * userLimit);
  const tbody = document.getElementById('users-table')?.querySelector('tbody');
  if (tbody) tbody.innerHTML = '<tr><td colspan="5">Laden...</td></tr>';
  UsersAPI.list(userRoleFilter || null, userSearchQuery || null, !userShowInactive, userSkip, userLimit)
    .then(users => {
      currentUsers = users;
      _renderUserTable();
    })
    .catch(error => {
      const tbody = document.getElementById('users-table')?.querySelector('tbody');
      if (tbody) tbody.innerHTML = `<tr><td colspan="5">Fout: ${escapeHtml(error.message)}</td></tr>`;
    });
}

function _renderUserTable() {
  const tbody = document.getElementById('users-table')?.querySelector('tbody');
  const pagination = document.getElementById('user-pagination');
  if (!tbody) return;

  if (currentUsers.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5">Geen gebruikers gevonden</td></tr>';
    if (pagination) pagination.innerHTML = '';
    return;
  }

  tbody.innerHTML = currentUsers.map(u => {
    const statusClass = u.is_active ? 'status-good' : 'status-warn';
    const statusText = u.is_active ? 'Actief' : 'Inactief';
    return `
      <tr>
        <td>${u.first_name} ${u.last_name}</td>
        <td>${u.email}</td>
        <td>${roleDisplayNames[u.role] || u.role}</td>
        <td><span class="status-pill ${statusClass}">${statusText}</span></td>
        <td>
          <button class="btn small" onclick="handleEditUser(${u.id})">${iconHtml('edit', 14)} Bewerk</button>
          <button class="btn small secondary" onclick="handleDeleteUser(${u.id})">${iconHtml('trash', 14)} Verwijder</button>
        </td>
      </tr>
    `;
  }).join('');

  if (pagination) {
    pagination.innerHTML = `
      <button class="btn small" ${userSkip === 0 ? 'disabled' : ''} onclick="changeUserPage(-1)">${iconHtml('chevron-left', 14)} Vorige</button>
      <span style="align-self: center;">Pagina ${Math.floor(userSkip / userLimit) + 1}</span>
      <button class="btn small" ${currentUsers.length < userLimit ? 'disabled' : ''} onclick="changeUserPage(1)">Volgende ${iconHtml('chevron-right', 14)}</button>
    `;
  }
}

window.handleEditUser = handleEditUser;
window.changeUserPage = changeUserPage;

// ============================================
// Admin - Overeenkomsten Overzicht (US-26)
// ============================================

let currentAgreements = [];

async function renderAdminAgreements() {
  const tbody = document.querySelector('#admin-agreements-table tbody');
  const detailPanel = document.getElementById('admin-agreement-detail-panel');
  const exportBtn = document.getElementById('btn-export-csv');
  const exportExcelBtn = document.getElementById('btn-export-excel');

  if (exportBtn) {
    exportBtn.addEventListener('click', async () => {
      try {
        await ReportsAPI.exportCsv();
        showToast('CSV export gedownload', 'success');
      } catch (error) {
        showToast(error.message || 'Export mislukt', 'error');
      }
    });
  }

  if (exportExcelBtn) {
    exportExcelBtn.addEventListener('click', async () => {
      try {
        await ReportsAPI.exportExcel();
        showToast('Excel export gedownload', 'success');
      } catch (error) {
        showToast(error.message || 'Export mislukt', 'error');
      }
    });
  }

  if (tbody) tbody.innerHTML = '<tr><td colspan="5">Laden...</td></tr>';

  try {
    currentAgreements = await ReportsAPI.listAgreements();

    if (tbody) {
      if (currentAgreements.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">Geen stages met overeenkomsten gevonden.</td></tr>';
      } else {
        tbody.innerHTML = currentAgreements.map(item => `
          <tr data-id="${item.internship_id}" class="admin-agreement-row">
            <td>${item.student?.first_name || 'Onbekend'} ${item.student?.last_name || ''}</td>
            <td><span class="status-pill ${getStatusClass(item.status)}">${item.status}</span></td>
            <td>${renderAgreementStatusCell(item.agreement_status)}</td>
            <td>${item.uploaded_at ? formatDate(item.uploaded_at) : '-'}</td>
            <td>
              <button class="btn small view-admin-agreement-btn" data-id="${item.internship_id}">${iconHtml('eye', 14)} Bekijken</button>
            </td>
          </tr>
        `).join('');

        tbody.querySelectorAll('.admin-agreement-row').forEach(row => {
          row.addEventListener('click', (e) => {
            if (e.target.classList.contains('view-admin-agreement-btn')) return;
            showAdminAgreementDetail(parseInt(row.dataset.id));
          });
        });

        tbody.querySelectorAll('.view-admin-agreement-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            showAdminAgreementDetail(parseInt(btn.dataset.id));
          });
        });
      }
    }

    if (detailPanel) detailPanel.style.display = 'none';
  } catch (error) {
    if (tbody) tbody.innerHTML = `<tr><td colspan="5">Fout: ${error.message}</td></tr>`;
    showToast(error.message, 'error');
  }
}

function showAdminAgreementDetail(internshipId) {
  const item = currentAgreements.find(a => a.internship_id === internshipId);
  if (!item) return;

  const detailPanel = document.getElementById('admin-agreement-detail-panel');
  const content = document.getElementById('admin-agreement-detail-content');
  const actions = document.getElementById('admin-agreement-actions');

  document.getElementById('admin-agreement-student-name').textContent =
    `${item.student?.first_name || ''} ${item.student?.last_name || ''}`;
  document.getElementById('admin-agreement-internship-id').textContent = item.internship_id;
  document.getElementById('admin-agreement-internship-status').textContent = item.status;

  if (content) {
    if (item.agreement_status === 'Niet Ingediend') {
      content.innerHTML = `
        <div class="info-message warning">
          <p>${iconHtml('alert-circle', 16)} Er is nog geen overeenkomst ingediend voor deze stage.</p>
        </div>
      `;
    } else {
      const agreement = {
        status: item.agreement_status,
        uploaded_at: item.uploaded_at,
        validated_at: null,
        file_path: true,
        internship_id: item.internship_id,
      };
      content.innerHTML = renderAgreementDetailHTML(agreement, { showDownload: true });
      attachAgreementDownload(internshipId, 'download-agreement-btn');
    }
  }

  if (actions) {
    actions.innerHTML = item.agreement_status === 'Niet Ingediend'
      ? '<p class="hint">Wacht tot de student een overeenkomst uploadt.</p>'
      : '';
  }

  if (detailPanel) detailPanel.style.display = 'block';
}

// Blootstellen aan window voor template onclick-handlers
window.renderAdminAgreements = renderAdminAgreements;
window.showAdminAgreementDetail = showAdminAgreementDetail;
window.handleEditUser = handleEditUser;
window.handleDeleteUser = handleDeleteUser;
window.changeUserPage = changeUserPage;

// ============================================
// Admin - Audit Log (US-30)
// ============================================

let auditSkip = 0;
const auditLimit = 50;
let auditFilters = { action: '', user_email: '', entity_type: '' };

async function renderAuditLog() {
  const tbody = document.querySelector('#audit-table tbody');
  const pagination = document.getElementById('audit-pagination');

  async function loadLogs() {
    if (tbody) tbody.innerHTML = '<tr><td colspan="6">Laden...</td></tr>';
    try {
      const logs = await AuditAPI.list(
        auditFilters.action || null,
        auditFilters.user_email || null,
        auditFilters.entity_type || null,
        auditSkip,
        auditLimit
      );
      renderLogs(logs);
    } catch (error) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="7">Fout: ${escapeHtml(error.message)}</td></tr>`;
    }
  }

  function renderLogs(logs) {
    if (!tbody) return;
    if (logs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6">Geen events gevonden.</td></tr>';
      if (pagination) pagination.innerHTML = '';
      return;
    }

    function _actionClass(action) {
      if (action.startsWith('login')) return 'status-good';
      if (action.includes('delete')) return 'status-bad';
      if (action.includes('review') || action.includes('validate')) return 'status-warn';
      return '';
    }

    tbody.innerHTML = logs.map(log => {
      const ts = new Date(log.timestamp).toLocaleString('nl-BE', {
        day: '2-digit', month: '2-digit', year: 'numeric',
        hour: '2-digit', minute: '2-digit', second: '2-digit'
      });
      return `
      <tr>
      <td style="white-space:nowrap;font-size:0.8rem;">${ts}</td>
      <td>${escapeHtml(log.user_email || '-')}</td>
      <td>${log.user_role ? `<span class="status-pill">${escapeHtml(log.user_role)}</span>` : '-'}</td>
      <td><span class="status-pill ${_actionClass(log.action)}">${escapeHtml(log.action)}</span></td>
      <td style="font-size:0.85rem;">${escapeHtml(log.detail || '-')}</td>
      <td style="font-size:0.75rem;color:var(--ink-soft);">${escapeHtml(log.ip_address || '-')}</td>
      </tr>
      `;
    }).join('');

    if (pagination) {
      pagination.innerHTML = `
        <button class="btn small" ${auditSkip === 0 ? 'disabled' : ''} onclick="changeAuditPage(-1)">${iconHtml('chevron-left', 14)} Vorige</button>
        <span style="align-self:center;">Pagina ${Math.floor(auditSkip / auditLimit) + 1}</span>
        <button class="btn small" ${logs.length < auditLimit ? 'disabled' : ''} onclick="changeAuditPage(1)">Volgende ${iconHtml('chevron-right', 14)}</button>
      `;
    }
  }

  // Filter handlers
  document.getElementById('audit-search-btn')?.addEventListener('click', () => {
    auditFilters.action = document.getElementById('audit-search-action')?.value.trim() || '';
    auditFilters.user_email = document.getElementById('audit-search-email')?.value.trim() || '';
    auditFilters.entity_type = document.getElementById('audit-entity-filter')?.value || '';
    auditSkip = 0;
    loadLogs();
  });

  document.getElementById('audit-reset-btn')?.addEventListener('click', () => {
    auditFilters = { action: '', user_email: '', entity_type: '' };
    const emailEl = document.getElementById('audit-search-email');
    const actionEl = document.getElementById('audit-search-action');
    const entityEl = document.getElementById('audit-entity-filter');
    if (emailEl) emailEl.value = '';
    if (actionEl) actionEl.value = '';
    if (entityEl) entityEl.value = '';
    auditSkip = 0;
    loadLogs();
  });

  loadLogs();
}

function changeAuditPage(delta) {
  auditSkip = Math.max(0, auditSkip + delta * auditLimit);
  renderAuditLog();
}

window.changeAuditPage = changeAuditPage;
