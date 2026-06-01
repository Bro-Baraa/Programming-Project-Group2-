function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('nl-BE', { day: '2-digit', month: '2-digit', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

function getStatusClass(status) {
  if (!status) return '';
  const map = {
    'ingediend': 'status-info',
    'overeenkomst-ingediend': 'status-info',
    'submitted': 'status-info',
    'draft': '',
    'in-beoordeling': 'status-warn',
    'aanpassingen-vereist': 'status-warn',
    'pending': 'status-warn',
    'goedgekeurd': 'status-good',
    'lopend': 'status-good',
    'approved': 'status-good',
    'afgekeurd': 'status-bad',
    'rejected': 'status-bad',
  };
  return map[status.toLowerCase().replace(/\s+/g, '-')] || '';
}

function showToast(message, type = "success", duration = 3000) {
  const existing = document.querySelector(".toast-notification");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.className = `toast-notification toast-${type}`;
  const icons = { success: "✓", error: "✗", warning: "⚠", info: "ℹ" };

  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || "•"}</span>
    <span class="toast-message">${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">×</button>
  `;

  document.body.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add("show"));

  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function showLoading(element, message = "Laden...") {
  if (!element) return;
  element.dataset.originalContent = element.innerHTML;
  element.innerHTML = `<span class="loading-spinner"></span> ${message}`;
  element.disabled = true;
}

function hideLoading(element) {
  if (!element) return;
  const original = element.dataset.originalContent;
  if (original !== undefined) {
    element.innerHTML = original;
  }
  element.disabled = false;
}
