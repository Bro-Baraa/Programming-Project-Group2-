/**
 * notifications.js
 *
 * Handles the bell icon, dropdown, and polling for in-app notifications.
 * Loaded after api-client.js so it can use apiRequest() directly.
 *
 * How it works:
 *  1. initNotifications() is called from app.js once the user is logged in.
 *  2. It fetches notifications immediately, then polls every 30 seconds.
 *  3. Clicking the bell opens/closes the dropdown and marks all as read.
 *  4. Clicking a single notification marks it as read and navigates to the
 *     relevant internship if one is linked.
 *  5. Clicking outside the dropdown closes it.
 *
 * To add email support in the future: extend the backend notify() helper in
 * app/services/notifications.py — no frontend changes needed.
 */

// ── API calls ─────────────────────────────────────────────────────────────────

const NotificationsAPI = {
  /** Fetch all notifications for the logged-in user (newest first, max 50). */
  getAll() {
    return apiRequest('/notifications');
  },

  /** Mark a single notification as read. */
  markRead(id) {
    return apiRequest(`/notifications/${id}/read`, { method: 'PATCH' });
  },

  /** Mark every unread notification as read in one call. */
  markAllRead() {
    return apiRequest('/notifications/read-all', { method: 'PATCH' });
  },
};

// ── State ─────────────────────────────────────────────────────────────────────

let _pollInterval = null;   // setInterval handle so we can clear it on logout
let _dropdownOpen = false;  // track whether the panel is visible

// ── Initialisation ────────────────────────────────────────────────────────────

/**
 * Call this once after the user has logged in.
 * Shows the bell, does the first fetch, and starts the 30-second poll.
 */
function initNotifications() {
  const wrapper = document.getElementById('notif-wrapper');
  if (!wrapper) return;

  // Clear any existing poll interval before starting a new one.
  // This prevents intervals stacking up if the user logs in/out multiple times.
  if (_pollInterval) {
    clearInterval(_pollInterval);
    _pollInterval = null;
  }

  // Show the bell now that the user is logged in
  wrapper.style.display = 'block';

  // Wire up event listeners only once — use a flag on the element to track this
  if (!wrapper.dataset.listenersAttached) {
    wrapper.dataset.listenersAttached = 'true';

    // Bell button toggle
    document.getElementById('notif-bell')?.addEventListener('click', (e) => {
      e.stopPropagation();
      toggleDropdown();
    });

    // "Mark all as read" button
    document.getElementById('notif-read-all')?.addEventListener('click', async (e) => {
      e.stopPropagation();
      try {
        const updated = await NotificationsAPI.markAllRead();
        renderNotifications(updated);
      } catch (err) {
        console.error('[Notifications] Failed to mark all as read:', err);
      }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
      if (_dropdownOpen && !e.target.closest('#notif-wrapper')) {
        closeDropdown();
      }
    });
  }

  // Initial fetch
  fetchAndRender();

  // Poll every 30 seconds so new notifications appear without a page refresh
  _pollInterval = setInterval(fetchAndRender, 30_000);
}

/**
 * Call this when the user logs out to stop the polling.
 */
function destroyNotifications() {
  if (_pollInterval) {
    clearInterval(_pollInterval);
    _pollInterval = null;
  }
  const wrapper = document.getElementById('notif-wrapper');
  if (wrapper) wrapper.style.display = 'none';
  closeDropdown();
}

// ── Fetch & render ────────────────────────────────────────────────────────────

async function fetchAndRender() {
  try {
    const notifications = await NotificationsAPI.getAll();
    renderNotifications(notifications);
  } catch (err) {
    // Silently ignore fetch errors during polling — the user doesn't need to see
    // an error toast every 30 seconds if e.g. the backend restarts briefly.
    console.error('[Notifications] Poll failed:', err);
  }
}

/**
 * Update the bell dot and re-render the dropdown list.
 * @param {Array} notifications - Array of notification objects from the API.
 */
function renderNotifications(notifications) {
  const dot = document.getElementById('notif-dot');
  const list = document.getElementById('notif-list');
  if (!dot || !list) return;

  // Count unread to decide whether to show the red dot
  const unreadCount = notifications.filter(n => !n.is_read).length;
  dot.style.display = unreadCount > 0 ? 'block' : 'none';

  if (notifications.length === 0) {
    list.textContent = '';
    const emptyLi = document.createElement('li');
    emptyLi.className = 'notif-empty';
    emptyLi.textContent = 'Geen notificaties';
    list.appendChild(emptyLi);
    return;
  }

  // Build the list items using DocumentFragment (no innerHTML thrashing)
  const fragment = document.createDocumentFragment();
  notifications.forEach(n => {
    const li = document.createElement('li');
    li.className = 'notif-item' + (n.is_read ? '' : ' unread');
    li.dataset.id = n.id;
    li.dataset.internship = n.internship_id || '';
    li.dataset.view = n.link_view || '';

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
      btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
      li.appendChild(btn);
    }

    fragment.appendChild(li);
  });
  list.textContent = '';
  list.appendChild(fragment);

  // Wire up click handler for each item (marks as read)
  list.querySelectorAll('.notif-item').forEach(item => {
    item.addEventListener('click', (e) => {
      // Don't trigger on the view button — it has its own handler
      if (e.target.closest('.notif-view-btn')) return;
      markReadOnly(item);
    });
  });

  // Wire up the view button — marks as read AND navigates
  list.querySelectorAll('.notif-view-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      navigateToNotification(btn);
    });
  });
}

// ── Interactions ──────────────────────────────────────────────────────────────

function toggleDropdown() {
  _dropdownOpen ? closeDropdown() : openDropdown();
}

function openDropdown() {
  const dropdown = document.getElementById('notif-dropdown');
  if (dropdown) dropdown.style.display = 'block';
  _dropdownOpen = true;
}

function closeDropdown() {
  const dropdown = document.getElementById('notif-dropdown');
  if (dropdown) dropdown.style.display = 'none';
  _dropdownOpen = false;
}

/**
 * Mark a notification as read without navigating anywhere.
 * Called when the user clicks the notification row itself.
 */
async function markReadOnly(item) {
  const id = parseInt(item.dataset.id);
  item.classList.remove('unread'); // optimistic UI update
  try {
    await NotificationsAPI.markRead(id);
    fetchAndRender(); // refresh dot count
  } catch (err) {
    console.error('[Notifications] Failed to mark as read:', err);
  }
}

/**
 * Mark a notification as read AND navigate to the linked view.
 * Called when the user clicks the 👁 view button.
 */
async function navigateToNotification(btn) {
  const id = parseInt(btn.dataset.id);
  const internshipId = btn.dataset.internship;
  const view = btn.dataset.view;

  // Mark as read first
  try {
    await NotificationsAPI.markRead(id);
  } catch (err) {
    console.error('[Notifications] Failed to mark as read:', err);
  }

  closeDropdown();

  // Navigate to the specific view for this notification
  // Both internship_id and view are needed to land on the right screen
  if (view && internshipId) {
    window.location.href = `?view=${view}&internship=${internshipId}`;
  } else if (view) {
    window.location.href = `?view=${view}`;
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Format an ISO datetime string into a human-readable relative time.
 * e.g. "5 minuten geleden", "2 uur geleden", "3 dagen geleden"
 */
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

/**
 * escapeHtml is defined in ui-helpers.js but notifications.js loads before it.
 * This local fallback keeps us safe if the order ever changes.
 */
function _safeEscapeHtml(str) {
  if (typeof escapeHtml === 'function') return escapeHtml(str);
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
// Override the inline usage above to use the safe version
// (notifications.js is loaded before ui-helpers.js)
// We redefine escapeHtml locally just for this file's usage:
const _escapeHtml = _safeEscapeHtml;
