function debounce(fn, wait = 150) {
  let t = null;
  return (...args) => {
    if (t) clearTimeout(t);
    t = setTimeout(() => fn(...args), wait);
  };
}

function buildTableCards() {
  const tables = Array.from(document.querySelectorAll('table'));
  tables.forEach((table, idx) => {
    if (table.dataset.cardsId || !table.querySelector('thead') || !table.querySelector('tbody')) return;

    const headers = Array.from(table.querySelectorAll('thead th')).map(h => h.textContent.trim());
    const tbody = table.querySelector('tbody');
    if (!tbody) return;

    const container = document.createElement('div');
    container.className = 'table-cards';
    container.dataset.source = `table-${idx}`;

    Array.from(tbody.querySelectorAll('tr')).forEach(row => {
      const card = document.createElement('div');
      card.className = 'table-card';
      card.setAttribute('role', 'group');

      const cells = Array.from(row.querySelectorAll('td'));
      cells.forEach((cell, i) => {
        const rowEl = document.createElement('div');
        rowEl.className = 'row';

        const label = document.createElement('div');
        label.className = 'label';
        const fieldId = `card-${idx}-${Math.random().toString(36).slice(2,8)}`;
        label.id = `${fieldId}-label`;
        label.textContent = headers[i] || '';

        const value = document.createElement('div');
        value.className = 'value';
        value.innerHTML = cell.innerHTML;
        value.setAttribute('aria-labelledby', label.id);

        const pill = value.querySelector('.status-pill');
        if (pill) {
          pill.setAttribute('role', 'status');
          pill.classList.add('table-card-status');
        }

        rowEl.appendChild(label);
        rowEl.appendChild(value);
        card.appendChild(rowEl);
      });

      container.appendChild(card);
    });

    table.insertAdjacentElement('afterend', container);
    table.dataset.cardsId = 'true';
    table.setAttribute('data-table-cards', 'true');
  });
}

function removeTableCards() {
  document.querySelectorAll('.table-cards').forEach(c => c.remove());
  document.querySelectorAll('table').forEach(t => {
    delete t.dataset.cardsId;
    t.removeAttribute('data-table-cards');
  });
}

function removeTableCards() {
  document.querySelectorAll('.table-cards').forEach(c => c.remove());
  document.querySelectorAll('table').forEach(t => delete t.dataset.cardsId);
}

function ensureTableCards() {
  if (window.innerWidth <= 720) {
    buildTableCards();
  } else {
    removeTableCards();
  }
}

window.addEventListener('resize', debounce(() => ensureTableCards(), 120));

// Initialize on load
window.addEventListener('load', () => ensureTableCards());
