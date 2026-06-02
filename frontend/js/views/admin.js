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

// ============================================
// Admin - Gebruikersbeheer
// ============================================

let currentUsers = [];
let userSearchQuery = '';
let userRoleFilter = '';
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
      const users = await UsersAPI.list(userRoleFilter || null, userSearchQuery || null, true, userSkip, userLimit);
      currentUsers = users;
      renderUserList();
    } catch (error) {
      if (tbody) tbody.innerHTML = `<tr><td colspan="5">Fout: ${error.message}</td></tr>`;
    }
  }

  function renderUserList() {
    if (!tbody) return;

    if (currentUsers.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5">Geen gebruikers gevonden</td></tr>';
      pagination.innerHTML = '';
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
            <button class="btn small" onclick="handleEditUser(${u.id})">Bewerk</button>
            <button class="btn small secondary" onclick="handleDeleteUser(${u.id})">Verwijder</button>
          </td>
        </tr>
      `;
    }).join('');

    // Pagination controls
    pagination.innerHTML = `
      <button class="btn small" ${userSkip === 0 ? 'disabled' : ''} onclick="changeUserPage(-1)">← Vorige</button>
      <span style="align-self: center;">Pagina ${Math.floor(userSkip / userLimit) + 1}</span>
      <button class="btn small" ${currentUsers.length < userLimit ? 'disabled' : ''} onclick="changeUserPage(1)">Volgende →</button>
    `;
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
    // Re-render the list
    const tbody = document.getElementById('users-table')?.querySelector('tbody');
    if (tbody) {
      if (currentUsers.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">Geen gebruikers gevonden</td></tr>';
      } else {
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
                <button class="btn small" onclick="handleEditUser(${u.id})">Bewerk</button>
                <button class="btn small secondary" onclick="handleDeleteUser(${u.id})">Verwijder</button>
              </td>
            </tr>
          `;
        }).join('');
      }
    }
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function changeUserPage(delta) {
  userSkip = Math.max(0, userSkip + delta * userLimit);
  const tbody = document.getElementById('users-table')?.querySelector('tbody');
  if (tbody) tbody.innerHTML = '<tr><td colspan="5">Laden...</td></tr>';
  UsersAPI.list(userRoleFilter || null, userSearchQuery || null, true, userSkip, userLimit)
    .then(users => {
      currentUsers = users;
      const tbody2 = document.getElementById('users-table')?.querySelector('tbody');
      const pagination = document.getElementById('user-pagination');
      if (currentUsers.length === 0) {
        if (tbody2) tbody2.innerHTML = '<tr><td colspan="5">Geen gebruikers gevonden</td></tr>';
        pagination.innerHTML = '';
        return;
      }
      if (tbody2) {
        tbody2.innerHTML = currentUsers.map(u => {
          const statusClass = u.is_active ? 'status-good' : 'status-warn';
          const statusText = u.is_active ? 'Actief' : 'Inactief';
          return `
            <tr>
              <td>${u.first_name} ${u.last_name}</td>
              <td>${u.email}</td>
              <td>${roleDisplayNames[u.role] || u.role}</td>
              <td><span class="status-pill ${statusClass}">${statusText}</span></td>
              <td>
                <button class="btn small" onclick="handleEditUser(${u.id})">Bewerk</button>
                <button class="btn small secondary" onclick="handleDeleteUser(${u.id})">Verwijder</button>
              </td>
            </tr>
          `;
        }).join('');
      }
      pagination.innerHTML = `
        <button class="btn small" ${userSkip === 0 ? 'disabled' : ''} onclick="changeUserPage(-1)">← Vorige</button>
        <span style="align-self: center;">Pagina ${Math.floor(userSkip / userLimit) + 1}</span>
        <button class="btn small" ${currentUsers.length < userLimit ? 'disabled' : ''} onclick="changeUserPage(1)">Volgende →</button>
      `;
    })
    .catch(error => {
      const tbody2 = document.getElementById('users-table')?.querySelector('tbody');
      if (tbody2) tbody2.innerHTML = `<tr><td colspan="5">Fout: ${error.message}</td></tr>`;
    });
}

window.handleEditUser = handleEditUser;
window.handleDeleteUser = handleDeleteUser;
window.changeUserPage = changeUserPage;

// Blootstellen aan window voor template onclick-handlers
window.handleDeleteCompetency = handleDeleteCompetency;
