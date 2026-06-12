const NotificationsAPI = {
  getAll() {
    return apiRequest('/notifications');
  },
  markRead(id) {
    return apiRequest(`/notifications/${id}/read`, { method: 'PATCH' });
  },
  markAllRead() {
    return apiRequest('/notifications/read-all', { method: 'PATCH' });
  },
};

let _pollInterval = null;
let _dropdownOpen = false;

function initNotifications() {
  const wrapper = document.getElementById('notif-wrapper');
  if (!wrapper) return;

  if (_pollInterval) {
    clearInterval(_pollInterval);
    _pollInterval = null;
  }

  wrapper.style.display = 'block';

  if (!wrapper.dataset.listenersAttached) {
    wrapper.dataset.listenersAttached = 'true';

    document.getElementById('notif-bell')?.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleDropdown();
    });

    document.getElementById('notif-read-all')?.addEventListener('click', async (e) => {
      e.stopPropagation();
      try {
        const updated = await NotificationsAPI.markAllRead();
        renderNotifications(updated);
      } catch (err) {
        console.error('[Notifications] Failed to mark all as read:', err);
      }
    });

    document.addEventListener('click', (e) => {
      if (_dropdownOpen && !e.target.closest('#notif-wrapper')) {
        closeDropdown();
      }
    });

    document.getElementById('notif-dropdown')?.addEventListener('keydown', (e) => {
      if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
      e.preventDefault();
      const items = Array.from(document.querySelectorAll('.notif-item, .notif-read-all'));
      const focused = document.activeElement;
      const idx = items.indexOf(focused);
      if (e.key === 'ArrowDown') {
        const next = idx < items.length - 1 ? idx + 1 : 0;
        items[next]?.focus();
      } else if (e.key === 'ArrowUp') {
        const prev = idx > 0 ? idx - 1 : items.length - 1;
        items[prev]?.focus();
      }
    });
  }

  fetchAndRender();
  _pollInterval = setInterval(fetchAndRender, 30_000);
}

function destroyNotifications() {
  if (_pollInterval) {
    clearInterval(_pollInterval);
    _pollInterval = null;
  }
  const wrapper = document.getElementById('notif-wrapper');
  if (wrapper) wrapper.style.display = 'none';
  closeDropdown();
}

async function fetchAndRender() {
  try {
    const notifications = await NotificationsAPI.getAll();
    renderNotifications(notifications);
  } catch (err) {
    console.error('[Notifications] Poll failed:', err);
  }
}

function renderNotifications(notifications) {
  const dot = document.getElementById('notif-dot');
  const list = document.getElementById('notif-list');
  if (!dot || !list) return;

  const unreadCount = notifications.filter(n => !n.is_read).length;
  const hadNew = dot.style.display === 'block';
  dot.style.display = unreadCount > 0 ? 'block' : 'none';

  if (unreadCount > 0 && !hadNew) {
    const bell = document.getElementById('notif-bell');
    if (bell) {
      bell.classList.remove('has-new');
      void bell.offsetWidth;
      bell.classList.add('has-new');
    }
  }

  if (notifications.length === 0) {
    list.textContent = '';
    const emptyLi = document.createElement('li');
    emptyLi.className = 'notif-empty';
    emptyLi.textContent = 'Geen notificaties';
    list.appendChild(emptyLi);
    return;
  }

  const fragment = document.createDocumentFragment();
  notifications.forEach(n => {
    const li = document.createElement('li');
    li.className = 'notif-item' + (n.is_read ? '' : ' unread');
    li.dataset.id = n.id;
    li.dataset.internship = n.internship_id || '';
    li.dataset.view = n.link_view || '';
    li.tabIndex = 0;

    const body = document.createElement('div');
    body.className = 'notif-item-body';
    const msg = document.createElement('span');
    msg.className = 'notif-message';
    msg.textContent = n.message;
    const time = document.createElement('span');
    time.className = 'notif-time';
    time.textContent = formatRelativeTime(n.created_at);
    body.appendChild(msg);
    body.appendChild(time);
    li.appendChild(body);

    if (n.internship_id && n.link_view) {
      const btn = document.createElement('button');
      btn.className = 'notif-view-btn';
      btn.title = 'Bekijken';
      btn.dataset.id = n.id;
      btn.dataset.internship = n.internship_id;
      btn.dataset.view = n.link_view;
      btn.innerHTML = '<img src="icons/eye.svg" alt="" width="16" height="16" class="icon-img" />';
      li.appendChild(btn);
    }

    fragment.appendChild(li);
  });
  list.textContent = '';
  list.appendChild(fragment);

  list.querySelectorAll('.notif-item').forEach(item => {
    item.addEventListener('click', (e) => {
      if (e.target.closest('.notif-view-btn')) return;
      markReadOnly(item);
    });
  });

  list.querySelectorAll('.notif-view-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      navigateToNotification(btn);
    });
  });
}

function toggleDropdown() {
  _dropdownOpen ? closeDropdown() : openDropdown();
}

function openDropdown() {
  const dropdown = document.getElementById('notif-dropdown');
  const bell = document.getElementById('notif-bell');
  if (dropdown) dropdown.style.display = 'block';
  _dropdownOpen = true;
  if (bell) {
    bell.setAttribute('aria-expanded', 'true');
    const firstItem = dropdown?.querySelector('.notif-item, .notif-read-all');
    if (firstItem) firstItem.focus();
  }
}

function closeDropdown() {
  const dropdown = document.getElementById('notif-dropdown');
  const bell = document.getElementById('notif-bell');
  if (dropdown) dropdown.style.display = 'none';
  _dropdownOpen = false;
  if (bell) {
    bell.setAttribute('aria-expanded', 'false');
    bell.focus();
  }
}

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && _dropdownOpen) {
    closeDropdown();
  }
});

async function markReadOnly(item) {
  const id = parseInt(item.dataset.id);
  item.classList.remove('unread');
  try {
    await NotificationsAPI.markRead(id);
    fetchAndRender();
  } catch (err) {
    console.error('[Notifications] Failed to mark as read:', err);
  }
}

async function navigateToNotification(btn) {
  const id = parseInt(btn.dataset.id);
  const internshipId = btn.dataset.internship;
  const view = btn.dataset.view;

  try {
    await NotificationsAPI.markRead(id);
  } catch (err) {
    console.error('[Notifications] Failed to mark as read:', err);
  }

  closeDropdown();

  if (view && internshipId) {
    window.location.href = `?view=${view}&internship=${internshipId}`;
  } else if (view) {
    window.location.href = `?view=${view}`;
  }
}

function formatRelativeTime(isoString) {
  const date = new Date(isoString);
  const diffMs = Date.now() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);

  if (diffMin < 1)  return 'Zojuist';
  if (diffMin < 60) return `${diffMin} minuut${diffMin === 1 ? '' : 'en'} geleden`;

  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24)  return `${diffHr} uur geleden`;

  const diffDay = Math.floor(diffHr / 24);
  return `${diffDay} dag${diffDay === 1 ? '' : 'en'} geleden`;
}

function _safeEscapeHtml(str) {
  if (typeof escapeHtml === 'function') return escapeHtml(str);
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

const _escapeHtml = _safeEscapeHtml;
