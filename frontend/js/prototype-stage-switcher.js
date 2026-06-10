// PROTOTYPE — Stage Switcher UI Variations
// Question: "What is the best UI for switching between multiple stages?"
// Variants: A=Popover Dropdown, B=Sidebar Context, C=Stage Cards Overview
// 
// MOCK DATA — represents a realistic dataset for the app
const MOCK_STAGES = [
  {
    id: 1,
    student: { first_name: 'Jan', last_name: 'Janssens', email: 'jan.janssens@school.be' },
    company: { name: 'Acme BV', address: 'Kerkstraat 1, 1000 Brussel', sector: 'IT' },
    status: 'active',
    start_date: '2026-02-01',
    end_date: '2026-06-30',
    agreement_status: 'validated',
    progress: 68,
    description: 'Web development stage bij een digital agency'
  },
  {
    id: 2,
    student: { first_name: 'Piet', last_name: 'Pieters', email: 'piet.pieters@school.be' },
    company: { name: 'TechCorp', address: 'Industrielaan 42, 9000 Gent', sector: 'Data & Analytics' },
    status: 'pending',
    start_date: '2026-09-01',
    end_date: '2026-12-31',
    agreement_status: 'uploaded',
    progress: 0,
    description: 'Data analyse stage bij een startup'
  },
  {
    id: 3,
    student: { first_name: 'Marie', last_name: 'Desmet', email: 'marie.desmet@school.be' },
    company: { name: 'Design Studio', address: 'Artiestenstraat 7, 2000 Antwerpen', sector: 'Design' },
    status: 'completed',
    start_date: '2025-09-01',
    end_date: '2026-01-31',
    agreement_status: 'validated',
    progress: 100,
    description: 'UI/UX design stage'
  },
  {
    id: 4,
    student: { first_name: 'Lucas', last_name: 'Vermeiren', email: 'lucas.vermeiren@school.be' },
    company: { name: 'Cloud Solutions', address: 'Technologielaan 100, 3000 Leuven', sector: 'Cloud' },
    status: 'rejected',
    start_date: '2026-02-01',
    end_date: '2026-06-30',
    agreement_status: 'missing',
    progress: 0,
    description: 'Cloud infrastructure stage'
  },
  {
    id: 5,
    student: { first_name: 'Emma', last_name: 'De Vries', email: 'emma.devries@school.be' },
    company: { name: 'CyberSecure', address: 'Beveiligingsplein 5, 3500 Hasselt', sector: 'Security' },
    status: 'active',
    start_date: '2026-02-15',
    end_date: '2026-07-15',
    agreement_status: 'validated',
    progress: 45,
    description: 'Cybersecurity stage'
  },
  {
    id: 6,
    student: { first_name: 'Thomas', last_name: 'Maes', email: 'thomas.maes@school.be' },
    company: { name: 'AI Innovations', address: 'Innovatiedreef 20, 2800 Mechelen', sector: 'AI' },
    status: 'pending',
    start_date: '2026-09-01',
    end_date: '2026-12-31',
    agreement_status: 'missing',
    progress: 0,
    description: 'Machine learning stage'
  }
];

const STATUS_META = {
  active: { label: 'Actief', color: 'var(--good)', bg: 'var(--good-bg)' },
  pending: { label: 'In afwachting', color: 'var(--warn)', bg: 'var(--warn-bg)' },
  completed: { label: 'Afgerond', color: 'var(--accent-2)', bg: 'var(--info-bg)' },
  rejected: { label: 'Afgekeurd', color: 'var(--bad)', bg: 'var(--bad-bg)' },
  missing: { label: 'Ontbreekt', color: 'var(--ink-soft)', bg: 'var(--border)' }
};

let selectedStageId = 1;
let currentRole = 'teacher'; // Simulating a teacher / admin view

// ─── Utilities ───
function fmtDate(d) { return d ? new Date(d).toLocaleDateString('nl-BE', { day: 'numeric', month: 'short', year: 'numeric' }) : '-'; }
function getStatusMeta(status) { return STATUS_META[status] || STATUS_META.missing; }
function getSelectedStage() { return MOCK_STAGES.find(s => s.id === selectedStageId) || MOCK_STAGES[0]; }
function stageLabel(s) { return `${s.student.first_name} ${s.student.last_name} — ${s.company.name}`; }

// ─── Variant A: Popover Dropdown ───
// Improved topbar dropdown with search, status badges, and richer info
function renderVariantA() {
  const container = document.getElementById('stage-switcher-root');
  container.innerHTML = `
    <div class="proto-a-wrapper">
      <div class="proto-a-trigger" id="proto-a-trigger" tabindex="0" role="button" aria-expanded="false" aria-haspopup="listbox">
        <span class="proto-a-trigger-icon">📋</span>
        <span class="proto-a-trigger-label">${stageLabel(getSelectedStage())}</span>
        <span class="proto-a-trigger-status status-${getSelectedStage().status}">${getStatusMeta(getSelectedStage().status).label}</span>
        <span class="proto-a-trigger-chevron">▼</span>
      </div>
      <div class="proto-a-popover" id="proto-a-popover" style="display:none;">
        <div class="proto-a-search">
          <input type="text" id="proto-a-search-input" placeholder="🔍 Zoek op student of bedrijf..." />
        </div>
        <ul class="proto-a-list" id="proto-a-list" role="listbox"></ul>
        <div class="proto-a-footer">
          <span class="proto-a-count">${MOCK_STAGES.length} stages</span>
        </div>
      </div>
    </div>
  `;

  const trigger = document.getElementById('proto-a-trigger');
  const popover = document.getElementById('proto-a-popover');
  const searchInput = document.getElementById('proto-a-search-input');
  const list = document.getElementById('proto-a-list');

  function renderList(filter = '') {
    const filtered = MOCK_STAGES.filter(s => {
      const q = filter.toLowerCase();
      return stageLabel(s).toLowerCase().includes(q) || s.company.sector.toLowerCase().includes(q);
    });
    list.innerHTML = filtered.map(s => {
      const meta = getStatusMeta(s.status);
      const isActive = s.id === selectedStageId;
      return `
        <li class="proto-a-item ${isActive ? 'active' : ''}" data-id="${s.id}" role="option" aria-selected="${isActive}">
          <div class="proto-a-item-header">
            <span class="proto-a-item-name">${s.student.first_name} ${s.student.last_name}</span>
            <span class="proto-a-item-badge" style="background:${meta.bg};color:${meta.color}">${meta.label}</span>
          </div>
          <div class="proto-a-item-company">${s.company.name}</div>
          <div class="proto-a-item-meta">
            <span class="proto-a-item-sector">${s.company.sector}</span>
            <span class="proto-a-item-date">${fmtDate(s.start_date)} — ${fmtDate(s.end_date)}</span>
          </div>
        </li>
      `;
    }).join('');
    document.querySelector('.proto-a-count').textContent = `${filtered.length} stage${filtered.length !== 1 ? 's' : ''}`;

    list.querySelectorAll('.proto-a-item').forEach(item => {
      item.addEventListener('click', () => {
        selectedStageId = parseInt(item.dataset.id);
        closePopover();
        renderVariantA();
        refreshContent();
      });
    });
  }

  function openPopover() {
    popover.style.display = 'block';
    trigger.setAttribute('aria-expanded', 'true');
    searchInput.focus();
    renderList();
  }
  function closePopover() {
    popover.style.display = 'none';
    trigger.setAttribute('aria-expanded', 'false');
  }
  function togglePopover() {
    popover.style.display === 'none' ? openPopover() : closePopover();
  }

  trigger.addEventListener('click', togglePopover);
  trigger.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); togglePopover(); } });
  searchInput.addEventListener('input', e => renderList(e.target.value));
  document.addEventListener('click', e => {
    if (!container.contains(e.target)) closePopover();
  });

  renderList();
}

// ─── Variant B: Sidebar Context ───
// Fixed sidebar panel showing stage cards, main content shrinks
function renderVariantB() {
  const container = document.getElementById('stage-switcher-root');
  container.innerHTML = `
    <div class="proto-b-sidebar">
      <div class="proto-b-header">
        <h3 class="proto-b-title">Stages</h3>
        <span class="proto-b-count">${MOCK_STAGES.length}</span>
      </div>
      <div class="proto-b-search">
        <input type="text" id="proto-b-search" placeholder="🔍 Zoek..." />
      </div>
      <ul class="proto-b-list" id="proto-b-list"></ul>
      <div class="proto-b-footer">
        <button class="proto-b-btn" id="proto-b-new">+ Nieuw voorstel</button>
      </div>
    </div>
  `;

  const list = document.getElementById('proto-b-list');
  const searchInput = document.getElementById('proto-b-search');

  function renderList(filter = '') {
    const filtered = MOCK_STAGES.filter(s => {
      const q = filter.toLowerCase();
      return stageLabel(s).toLowerCase().includes(q) || s.status.includes(q);
    });
    list.innerHTML = filtered.map(s => {
      const meta = getStatusMeta(s.status);
      const isActive = s.id === selectedStageId;
      return `
        <li class="proto-b-card ${isActive ? 'active' : ''}" data-id="${s.id}">
          <div class="proto-b-card-top">
            <div class="proto-b-avatar">${s.student.first_name[0]}${s.student.last_name[0]}</div>
            <div class="proto-b-card-info">
              <div class="proto-b-card-name">${s.student.first_name} ${s.student.last_name}</div>
              <div class="proto-b-card-company">${s.company.name}</div>
            </div>
          </div>
          <div class="proto-b-card-bottom">
            <span class="proto-b-card-status" style="background:${meta.bg};color:${meta.color}">${meta.label}</span>
            <span class="proto-b-card-date">${fmtDate(s.start_date)}</span>
          </div>
          ${isActive ? '<div class="proto-b-card-indicator"></div>' : ''}
        </li>
      `;
    }).join('');

    list.querySelectorAll('.proto-b-card').forEach(card => {
      card.addEventListener('click', () => {
        selectedStageId = parseInt(card.dataset.id);
        renderList(searchInput.value);
        refreshContent();
      });
    });
  }

  searchInput.addEventListener('input', e => renderList(e.target.value));
  renderList();
}

// ─── Variant C: Stage Cards Overview ───
// "My Stages" as a primary view — cards grid, no dropdown/sidebar
function renderVariantC() {
  const container = document.getElementById('stage-switcher-root');
  container.innerHTML = `
    <div class="proto-c-overview">
      <div class="proto-c-header">
        <h2 class="proto-c-title">Mijn Stages</h2>
        <p class="proto-c-subtitle">Kies een stage om details te bekijken</p>
      </div>
      <div class="proto-c-grid" id="proto-c-grid"></div>
      <div class="proto-c-new">
        <button class="proto-c-new-btn">+ Nieuw Stagevoorstel Indienen</button>
      </div>
    </div>
  `;

  const grid = document.getElementById('proto-c-grid');
  grid.innerHTML = MOCK_STAGES.map(s => {
    const meta = getStatusMeta(s.status);
    const isActive = s.id === selectedStageId;
    return `
      <div class="proto-c-card ${isActive ? 'active' : ''}" data-id="${s.id}">
        <div class="proto-c-card-header">
          <div class="proto-c-card-avatar">${s.student.first_name[0]}${s.student.last_name[0]}</div>
          <div class="proto-c-card-title-block">
            <div class="proto-c-card-name">${s.student.first_name} ${s.student.last_name}</div>
            <div class="proto-c-card-company">${s.company.name}</div>
          </div>
        </div>
        <div class="proto-c-card-body">
          <div class="proto-c-card-meta">
            <span class="proto-c-card-status" style="background:${meta.bg};color:${meta.color}">${meta.label}</span>
            <span class="proto-c-card-sector">${s.company.sector}</span>
          </div>
          <div class="proto-c-card-dates">
            <span class="proto-c-card-date-icon">📅</span>
            ${fmtDate(s.start_date)} — ${fmtDate(s.end_date)}
          </div>
          <div class="proto-c-card-progress">
            <div class="proto-c-progress-bar">
              <div class="proto-c-progress-fill" style="width:${s.progress}%;background:${meta.color}"></div>
            </div>
            <span class="proto-c-progress-label">${s.progress}%</span>
          </div>
          <p class="proto-c-card-desc">${s.description}</p>
        </div>
        <div class="proto-c-card-footer">
          <button class="proto-c-card-btn ${isActive ? 'active' : ''}">
            ${isActive ? '✓ Huidige selectie' : 'Bekijk details'}
          </button>
        </div>
      </div>
    `;
  }).join('');

  grid.querySelectorAll('.proto-c-card').forEach(card => {
    card.addEventListener('click', () => {
      selectedStageId = parseInt(card.dataset.id);
      renderVariantC();
      refreshContent();
    });
  });
}

// ─── Content placeholder that reacts to stage selection ───
function refreshContent() {
  const stage = getSelectedStage();
  const meta = getStatusMeta(stage.status);
  const content = document.getElementById('proto-content');
  content.innerHTML = `
    <div class="proto-content-header">
      <div class="proto-content-badge" style="background:${meta.bg};color:${meta.color}">${meta.label}</div>
      <h2 class="proto-content-title">${stage.student.first_name} ${stage.student.last_name}</h2>
      <p class="proto-content-subtitle">${stage.company.name} — ${stage.company.sector}</p>
    </div>
    <div class="proto-content-body">
      <div class="proto-content-grid">
        <div class="proto-content-card">
          <h4>📅 Periode</h4>
          <p>${fmtDate(stage.start_date)} — ${fmtDate(stage.end_date)}</p>
        </div>
        <div class="proto-content-card">
          <h4>📄 Overeenkomst</h4>
          <p>${stage.agreement_status === 'validated' ? '✓ Gevalideerd' : stage.agreement_status === 'uploaded' ? '⏳ In afwachting' : '✗ Ontbreekt'}</p>
        </div>
        <div class="proto-content-card">
          <h4>📊 Voortgang</h4>
          <div class="proto-content-progress">
            <div class="proto-content-bar"><div style="width:${stage.progress}%;"></div></div>
            <span>${stage.progress}%</span>
          </div>
        </div>
      </div>
      <div class="proto-content-card full">
        <h4>📝 Opdracht</h4>
        <p>${stage.description}</p>
      </div>
      <div class="proto-content-tabs">
        <button class="proto-content-tab active">Logboeken</button>
        <button class="proto-content-tab">Evaluatie</button>
        <button class="proto-content-tab">Feedback</button>
        <button class="proto-content-tab">Overeenkomst</button>
      </div>
      <div class="proto-content-placeholder">
        <p>🛠️ Tab-inhoud zou hier geladen worden voor stage #${stage.id}</p>
        <p class="hint">Deze tabs tonen hoe de stage-context doorwerkt in de rest van de UI.</p>
      </div>
    </div>
  `;
}

// ─── Main render ───
function initPrototype() {
  const url = new URL(window.location.href);
  const variant = url.searchParams.get('variant') || 'A';

  // Role selector (for demo purposes)
  const roleSelector = document.getElementById('proto-role-selector');
  if (roleSelector) {
    roleSelector.value = currentRole;
    roleSelector.addEventListener('change', e => {
      currentRole = e.target.value;
      // Reload with same variant
      initPrototype();
    });
  }

  // Render variant
  const switcherRoot = document.getElementById('stage-switcher-root');
  const mainContent = document.getElementById('main-content');

  if (variant === 'A') {
    document.body.className = 'proto-variant-a';
    renderVariantA();
    mainContent.style.marginLeft = '0';
  } else if (variant === 'B') {
    document.body.className = 'proto-variant-b';
    renderVariantB();
    mainContent.style.marginLeft = '260px';
  } else if (variant === 'C') {
    document.body.className = 'proto-variant-c';
    renderVariantC();
    mainContent.style.marginLeft = '0';
  }

  refreshContent();

  // Load the floating switcher bar
  const script = document.createElement('script');
  script.src = 'js/prototype-switcher.js';
  document.body.appendChild(script);
}

// Start when DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPrototype);
} else {
  initPrototype();
}
