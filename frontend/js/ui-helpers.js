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
    'afgerond': 'status-good',
    'gevalideerd': 'status-good',
    'approved': 'status-good',
    'afgekeurd': 'status-bad',
    'rejected': 'status-bad',
    'onvolledig': 'status-warn',
    'niet-ingediend': 'status-warn',
  };
  return map[status.toLowerCase().replace(/\s+/g, '-')] || '';
}

function getEvalTypeLabel(type) {
  if (type === 'tussentijds') return 'Tussentijds';
  if (type === 'final') return 'Final';
  return type;
}

// Inline SVG icons — eliminates dozens of individual HTTP requests per page
const _ICON_SVGS = {
  'alert-circle': '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
  'bell': '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
  'book-open': '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>',
  'calendar': '<rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
  'check-circle': '<circle cx="12" cy="12" r="10"/><polyline points="9 12 12 15 16 10"/>',
  'chevron-down': '<polyline points="6 9 12 15 18 9"/>',
  'chevron-left': '<polyline points="15 18 9 12 15 6"/>',
  'chevron-right': '<polyline points="9 18 15 12 9 6"/>',
  'clock': '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
  'download': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>',
  'edit': '<path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"/>',
  'eye': '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>',
  'file-text': '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/>',
  'filter': '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>',
  'home': '<path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>',
  'lock': '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
  'log-out': '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>',
  'plus': '<line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>',
  'search': '<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>',
  'settings': '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.47a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
  'trash': '<polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
  'upload': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>',
  'user': '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
  'users': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
  'x-circle': '<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>'
};

function iconHtml(name, size = 16, opts = {}) {
  const alt = opts.alt || '';
  const cls = opts.class || 'icon-img';
  const inner = _ICON_SVGS[name] || '';
  if (!inner) {
    // Fallback to img tag for unknown icons (e.g. favicon, logo)
    return `<img src="icons/${name}.svg" alt="${alt}" width="${size}" height="${size}" class="${cls}" />`;
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="${cls}" aria-hidden="true">${inner}</svg>`;
}

/** Replaces any existing <img class="icon-img"> tags in a container with inline SVGs.
 *  Call this after cloning templates or rendering dynamic content. */
function inlineIconsInContainer(container) {
  if (!container) return;
  container.querySelectorAll('img.icon-img').forEach(img => {
    const match = img.src.match(/icons\/(.+)\.svg$/);
    const name = match ? match[1] : null;
    if (!name || !_ICON_SVGS[name]) return;
    const size = parseInt(img.getAttribute('width')) || 16;
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', size);
    svg.setAttribute('height', size);
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('fill', 'none');
    svg.setAttribute('stroke', 'currentColor');
    svg.setAttribute('stroke-width', '2');
    svg.setAttribute('stroke-linecap', 'round');
    svg.setAttribute('stroke-linejoin', 'round');
    svg.setAttribute('class', img.className);
    svg.setAttribute('aria-hidden', 'true');
    svg.innerHTML = _ICON_SVGS[name];
    img.replaceWith(svg);
  });
}

function showToast(message, type = "success", duration = 3000) {
  // Ensure aria-live region exists
  let toastRegion = document.getElementById('toast-region');
  if (!toastRegion) {
    toastRegion = document.createElement('div');
    toastRegion.id = 'toast-region';
    toastRegion.setAttribute('aria-live', 'polite');
    toastRegion.setAttribute('aria-atomic', 'true');
    toastRegion.style.position = 'fixed';
    toastRegion.style.top = '20px';
    toastRegion.style.right = '20px';
    toastRegion.style.zIndex = '1000';
    document.body.appendChild(toastRegion);
  }

  const existing = toastRegion.querySelector(".toast-notification");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.className = `toast-notification toast-${type}`;
  toast.setAttribute('role', 'status');

  const iconSpan = document.createElement('span');
  iconSpan.className = 'toast-icon';
  const iconNames = { success: 'check-circle', error: 'x-circle', warning: 'alert-circle', info: 'alert-circle' };
  iconSpan.innerHTML = iconHtml(iconNames[type] || 'alert-circle', 16);

  const messageSpan = document.createElement('span');
  messageSpan.className = 'toast-message';
  messageSpan.textContent = message;

  const closeBtn = document.createElement('button');
  closeBtn.className = 'toast-close';
  closeBtn.innerHTML = iconHtml('x-circle', 14);
  closeBtn.addEventListener('click', () => toast.remove());

  toast.appendChild(iconSpan);
  toast.appendChild(messageSpan);
  toast.appendChild(closeBtn);

  toastRegion.appendChild(toast);
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

/** Wrap an async function with loading state and toast-on-error. */
async function withLoading(element, message, asyncFn) {
  showLoading(element, message);
  try {
    return await asyncFn();
  } catch (err) {
    showToast(err.message || err, 'error');
    throw err;
  } finally {
    hideLoading(element);
  }
}

function renderAgreementStatusCell(agreementStatus) {
  const statusClass = getStatusClass(agreementStatus);
  return `<span class="status-pill ${statusClass}">${agreementStatus}</span>`;
}

function renderAgreementUploadedCell(uploaded) {
  return uploaded
    ? `<span class="status-pill status-good">${iconHtml('check-circle', 14)} Ja</span>`
    : `<span class="status-pill status-warn">${iconHtml('x-circle', 14)} Nee</span>`;
}

function renderAgreementDetailHTML(agreement, opts = {}) {
  const {
    showDownload = true,
    showInsurance = false,
    showValidation = false,
    insuranceVerified = false,
    onValidate = null,
    onIncomplete = null,
  } = opts;

  const insurance = agreement?.insurance_verified || insuranceVerified
    ? { text: `${iconHtml('check-circle', 14)} Verzekering gecontroleerd`, class: 'status-good' }
    : { text: `${iconHtml('x-circle', 14)} Verzekering nog niet gecontroleerd`, class: 'status-warn' };

  let html = `
    <div class="agreement-info">
      <p><strong>Status overeenkomst:</strong> <span class="status-pill ${getStatusClass(agreement.status)}">${agreement.status}</span></p>
      ${showInsurance ? `<p><strong>Verzekering:</strong> <span class="status-pill ${insurance.class}">${insurance.text}</span></p>` : ''}
      <p><strong>Geüpload op:</strong> ${formatDate(agreement.uploaded_at) || 'Onbekend'}</p>
      <p><strong>Gevalideerd op:</strong> ${formatDate(agreement.validated_at) || 'Nog niet gevalideerd'}</p>
    </div>
  `;

  if (showDownload && agreement.file_path) {
    html += `
      <div style="margin-top: 1rem;">
        <button class="btn" id="download-agreement-btn" data-internship-id="${agreement.internship_id || ''}">${iconHtml('file-text', 16)} PDF Downloaden</button>
      </div>
    `;
  }

  if (showValidation && agreement.status !== 'Gevalideerd') {
    html += `
      <div class="validation-form" style="margin-top: 1rem;">
        <div class="row full" style="margin-bottom: 0.75rem;">
          <label>
            <input type="checkbox" id="insurance-check" ${agreement.insurance_verified ? 'checked' : ''} />
            Verzekering is in orde
          </label>
        </div>
        <div class="btn-group">
          <button id="btn-validate" class="btn success">${iconHtml('check-circle', 14)} Valideren</button>
          <button id="btn-incomplete" class="btn danger">${iconHtml('x-circle', 14)} Onvolledig</button>
        </div>
      </div>
    `;
  }

  return html;
}

function attachAgreementDownload(internshipId, buttonId = 'download-agreement-btn') {
  const btn = document.getElementById(buttonId);
  if (!btn) return;
  btn.addEventListener('click', async () => {
    showLoading(btn, 'Downloaden...');
    try {
      await AgreementsAPI.download(internshipId);
      hideLoading(btn);
    } catch (error) {
      hideLoading(btn);
      showToast(error.message, 'error');
    }
  });
}

// Generic confirm modal — returns a Promise that resolves when user clicks OK or rejects on cancel
function showConfirmModal({ title = 'Bevestigen', message, okText = 'Bevestigen', okClass = 'danger' }) {
  return new Promise((resolve, reject) => {
    const modal = document.getElementById('confirm-modal');
    const titleEl = document.getElementById('confirm-modal-title');
    const messageEl = document.getElementById('confirm-modal-message');
    const okBtn = document.getElementById('confirm-modal-ok');
    const cancelBtn = document.getElementById('confirm-modal-cancel');
    if (!modal || !okBtn || !cancelBtn) {
      // Fallback to native confirm if modal markup is missing
      if (confirm(message)) resolve();
      else reject();
      return;
    }

    titleEl.textContent = title;
    messageEl.textContent = message;
    okBtn.textContent = okText;
    okBtn.className = `btn ${okClass}`;
    modal.style.display = 'flex';

    // Focus trap: focus on OK button
    okBtn.focus();

    // Focus trap: collect focusable elements within the modal card
    const focusable = Array.from(
      modal.querySelectorAll('.modal-card button, .modal-card [href], .modal-card input, .modal-card select, .modal-card textarea, .modal-card [tabindex]:not([tabindex="-1"])')
    ).filter(el => !el.disabled && el.offsetParent !== null);
    const firstFocusable = focusable[0] || okBtn;
    const lastFocusable = focusable[focusable.length - 1] || okBtn;

    function cleanup() {
      modal.style.display = 'none';
      okBtn.removeEventListener('click', onOk);
      cancelBtn.removeEventListener('click', onCancel);
      document.removeEventListener('keydown', onKey);
    }

    function onOk() {
      cleanup();
      resolve();
    }

    function onCancel() {
      cleanup();
      reject();
    }

    function onKey(e) {
      if (e.key === 'Escape') {
        e.preventDefault();
        onCancel();
        return;
      }
      if (e.key === 'Tab') {
        const active = document.activeElement;
        if (e.shiftKey) {
          if (active === firstFocusable || !focusable.includes(active)) {
            e.preventDefault();
            lastFocusable.focus();
          }
        } else {
          if (active === lastFocusable || !focusable.includes(active)) {
            e.preventDefault();
            firstFocusable.focus();
          }
        }
      }
    }

    okBtn.addEventListener('click', onOk);
    cancelBtn.addEventListener('click', onCancel);
    document.addEventListener('keydown', onKey);
  });
}
