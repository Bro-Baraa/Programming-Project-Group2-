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

function iconHtml(name, size = 16, opts = {}) {
  const alt = opts.alt || '';
  const cls = opts.class || 'icon-img';
  return `<img src="icons/${name}.svg" alt="${alt}" width="${size}" height="${size}" class="${cls}" />`;
}

function showToast(message, type = "success", duration = 3000) {
  const existing = document.querySelector(".toast-notification");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.className = `toast-notification toast-${type}`;
  const icons = {
    success: iconHtml('check-circle', 16),
    error: iconHtml('x-circle', 16),
    warning: iconHtml('alert-circle', 16),
    info: iconHtml('alert-circle', 16)
  };

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

// ============================================
// Shared agreement rendering helpers
// ============================================

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
