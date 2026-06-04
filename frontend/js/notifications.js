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
    list.innerHTML = '<li class="notif-empty">Geen notificaties</li>';
    return;
  }

  // Build the list items
  list.innerHTML = notifications.map(n => `
    <li
      class="notif-item ${n.is_read ? '' : 'unread'}"
      data-id="${n.id}"
      data-internship="${n.internship_id || ''}"
    >
      ${_escapeHtml(n.message)}
      <span class="notif-time">${formatRelativeTime(n.created_at)}</span>
    </li>
  `).join('');

  // Wire up click handler for each item
  list.querySelectorAll('.notif-item').forEach(item => {
    item.addEventListener('click', () => handleNotificationClick(item));
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
 * Handle a click on a single notification row.
 * Marks it as read, updates the UI, and navigates to the internship if linked.
 */
async function handleNotificationClick(item) {
  const id = parseInt(item.dataset.id);
  const internshipId = item.dataset.internship;

  // Optimistically mark as read in the UI immediately (feels snappy)
  item.classList.remove('unread');

  try {
    await NotificationsAPI.markRead(id);
    // Re-fetch to get accurate unread count for the dot
    fetchAndRender();
  } catch (err) {
    console.error('[Notifications] Failed to mark as read:', err);
  }

  // Navigate to the linked internship if there is one
  if (internshipId) {
    closeDropdown();
    // Use the app's existing URL-based navigation
    window.location.href = `?view=dashboard&internship=${internshipId}`;
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
