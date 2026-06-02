// ============================================
// Commissieweergaven
// ============================================

async function renderCommitteeProposals() {
  try {
    const tbody = document.querySelector('#proposals-table tbody');

    if (tbody) {
      tbody.innerHTML = allInternships.map(p => {
        let agreementCell;
        if (p.status === 'Afgekeurd') {
          agreementCell = '<span class="hint">-</span>';
        } else if (p.agreement_uploaded) {
          agreementCell = '<span class="status-pill status-good">Ontvangen</span>';
        } else {
          agreementCell = '<span class="status-pill status-warn">Nog niet</span>';
        }
        return `
        <tr data-id="${p.id}" class="proposal-row">
          <td>${p.student?.first_name || 'Onbekend'} ${p.student?.last_name || ''}</td>
          <td>${p.company?.name || 'Onbekend'}</td>
          <td>${new Date(p.created_at).toLocaleDateString('nl-BE')}</td>
          <td><span class="status-pill ${getStatusClass(p.status)}">${p.status}</span></td>
          <td>${agreementCell}</td>
        </tr>
      `}).join('');

      // Klikhandler: selecteer stage en toon detailpaneel
      tbody.querySelectorAll('.proposal-row').forEach(row => {
        row.addEventListener('click', () => {
          const id = parseInt(row.dataset.id);
          selectProposalForReview(id);
        });
      });
    }

    // Als een voorstel via URL is geselecteerd, toon detail
    if (selectedInternshipId) {
      const preselected = allInternships.find(i => i.id == selectedInternshipId);
      if (preselected) selectProposalForReview(preselected.id);
    }

  } catch (error) {
    showToast(error.message, 'error');
  }
}

function selectProposalForReview(internshipId) {
  const internship = allInternships.find(i => i.id == internshipId);
  if (!internship) return;

  // URL bijwerken
  selectedInternshipId = internshipId;
  currentInternship = internship;
  const url = new URL(window.location.href);
  url.searchParams.set('internship', internshipId);
  window.history.replaceState({}, '', url);

  // Geselecteerde rij markeren
  document.querySelectorAll('.proposal-row').forEach(r => {
    r.style.background = r.dataset.id == internshipId ? 'rgba(0, 121, 140, 0.1)' : '';
  });

  // Detailpaneel tonen
  const panel = document.getElementById('proposal-detail-panel');
  if (panel) panel.style.display = 'block';

  // Detailinformatie vullen
  document.getElementById('selected-student-name').textContent =
    `${internship.student?.first_name || ''} ${internship.student?.last_name || ''}`;
  document.getElementById('selected-company').textContent = internship.company?.name || 'Onbekend';
  document.getElementById('selected-status').textContent = internship.status;

  // Haal voorstelbeschrijving op en toon
  document.getElementById('selected-description').textContent = 'Laden...';
  InternshipsAPI.get(internship.id).then(full => {
    document.getElementById('selected-description').textContent =
      full.proposal?.description || 'Geen omschrijving beschikbaar.';
    // Vul feedback box met bestaande feedback (issue #5)
    const feedbackBox = document.getElementById('feedback-box');
    if (feedbackBox && full.proposal?.feedback) {
      feedbackBox.value = full.proposal.feedback;
    }
  }).catch(() => {
    document.getElementById('selected-description').textContent = 'Kon omschrijving niet laden.';
  });

  // Actieknoppen verbinden
  const actionsDiv = document.getElementById('review-actions');
  if (actionsDiv) {
    const status = internship.status;
    if (status === 'Ingediend' || status === 'Aanpassingen Vereist') {
      // Eerst "In Beoordeling" zetten
      actionsDiv.innerHTML = `
        <button id="btn-review" class="btn">🔍 In Beoordeling Zetten</button>
      `;
      document.getElementById('btn-review')?.addEventListener('click', () => doReview(internship.id, 'In Beoordeling'));
    } else if (status === 'In Beoordeling') {
      // Dan pas beslissen
      actionsDiv.innerHTML = `
        <button id="btn-approve" class="btn success">✓ Goedkeuren</button>
        <button id="btn-reject" class="btn danger">✗ Afkeuren</button>
        <button id="btn-changes" class="btn secondary">⚠ Aanpassingen Vereist</button>
      `;
      document.getElementById('btn-approve')?.addEventListener('click', () => doReview(internship.id, 'Goedgekeurd'));
      document.getElementById('btn-reject')?.addEventListener('click', () => doReview(internship.id, 'Afgekeurd'));
      document.getElementById('btn-changes')?.addEventListener('click', () => doReview(internship.id, 'Aanpassingen Vereist'));
    } else {
      actionsDiv.innerHTML = '<p class="hint">Voorstel is al beoordeeld.</p>';
    }
  }
}

async function doReview(internshipId, decision) {
  const feedback = document.getElementById('feedback-box')?.value || null;

  if (decision === 'Aanpassingen Vereist' && !feedback) {
    showToast('Feedback is verplicht bij "Aanpassingen Vereist"', 'warning');
    return;
  }

  try {
    await ProposalsAPI.review(internshipId, decision, feedback);
    showToast(`Voorstel ${decision.toLowerCase()}!`, 'success');
    // Gegevens verversen
    allInternships = await InternshipsAPI.list();
    renderCommitteeProposals();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function renderCommitteeAgreements() {
  try {
    const tbody = document.querySelector('#agreements-table tbody');

    if (tbody) {
      // Filter stages that have an agreement uploaded or are approved (waiting for agreement)
      const agreementStatuses = ['Goedgekeurd', 'Overeenkomst Ingediend', 'Lopend', 'Afgerond'];
      const stagesWithAgreements = allInternships.filter(
        i => agreementStatuses.includes(i.status) || i.agreement_uploaded
      );

      if (stagesWithAgreements.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">Geen stages met overeenkomsten gevonden.</td></tr>';
      } else {
        tbody.innerHTML = stagesWithAgreements.map(i => {
          const agreementStatus = i.agreement_status || 'Niet Ingediend';
          const statusClass = getStatusClass(agreementStatus);
          return `
            <tr data-id="${i.id}" class="agreement-row">
              <td>${i.student?.first_name || 'Onbekend'} ${i.student?.last_name || ''}</td>
              <td>${i.company?.name || 'Onbekend'}</td>
              <td><span class="status-pill ${getStatusClass(i.status)}">${i.status}</span></td>
              <td><span class="status-pill ${statusClass}">${agreementStatus}</span></td>
              <td>${i.agreement_uploaded ? '<span class="status-pill status-good">✓ Ja</span>' : '<span class="status-pill status-warn">✗ Nee</span>'}</td>
              <td>
                <button class="btn small view-agreement-btn" data-id="${i.id}">Bekijken</button>
              </td>
            </tr>
          `;
        }).join('');

        // Click handlers for view buttons
        tbody.querySelectorAll('.view-agreement-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = parseInt(btn.dataset.id);
            showAgreementDetailPanel(id);
          });
        });
      }
    }

    // Hide detail panel initially
    const panel = document.getElementById('agreement-detail-panel');
    if (panel) panel.style.display = 'none';

  } catch (error) {
    showToast(error.message, 'error');
  }
}

function showAgreementDetailPanel(internshipId) {
  const internship = allInternships.find(i => i.id === internshipId);
  if (!internship) return;

  // Update URL
  selectedInternshipId = internshipId;
  currentInternship = internship;
  const url = new URL(window.location.href);
  url.searchParams.set('internship', internshipId);
  window.history.replaceState({}, '', url);

  // Show panel
  const panel = document.getElementById('agreement-detail-panel');
  if (panel) panel.style.display = 'block';

  // Fill in student info
  document.getElementById('agreement-student-name').textContent =
    `${internship.student?.first_name || ''} ${internship.student?.last_name || ''}`;
  document.getElementById('agreement-company').textContent = internship.company?.name || 'Onbekend';
  document.getElementById('agreement-internship-status').textContent = internship.status;

  // Load agreement details
  const detailContainer = document.getElementById('agreement-detail-content');
  detailContainer.innerHTML = '<p>Laden...</p>';

  InternshipsAPI.get(internship.id).then(full => {
    const agreement = full.agreement;
    if (!agreement) {
      detailContainer.innerHTML = `
        <div class="info-message warning">
          <p>⚠️ Er is nog geen overeenkomst geüpload voor deze stage.</p>
        </div>
      `;
      document.getElementById('agreement-actions').innerHTML = '';
      return;
    }

    const insurance = agreement.insurance_verified
      ? { text: '✓ Verzekering gecontroleerd', class: 'status-good' }
      : { text: '✗ Verzekering nog niet gecontroleerd', class: 'status-warn' };

    detailContainer.innerHTML = `
      <div class="agreement-info">
        <p><strong>Status overeenkomst:</strong> <span class="status-pill ${getStatusClass(agreement.status)}">${agreement.status}</span></p>
        <p><strong>Verzekering:</strong> <span class="status-pill ${insurance.class}">${insurance.text}</span></p>
        <p><strong>Geüpload op:</strong> ${formatDate(agreement.uploaded_at) || 'Onbekend'}</p>
        <p><strong>Gevalideerd op:</strong> ${formatDate(agreement.validated_at) || 'Nog niet gevalideerd'}</p>
        ${agreement.file_path ? `
        <div style="margin-top: 1rem;">
          <button class="btn" id="download-agreement-btn" data-internship-id="${internship.id}">📄 PDF Downloaden</button>
        </div>
        ` : ''}
      </div>
    `;

    // Validation actions
    const actionsDiv = document.getElementById('agreement-actions');
    if (actionsDiv) {
      const isValidated = agreement.status === 'Gevalideerd';

      if (isValidated) {
        actionsDiv.innerHTML = `
          <div class="info-message success">
            <p>✓ Deze overeenkomst is gevalideerd. De stage is actief.</p>
          </div>
        `;
      } else {
        actionsDiv.innerHTML = `
          <div class="validation-form">
            <div class="row full" style="margin-bottom: 0.75rem;">
              <label>
                <input type="checkbox" id="insurance-check" ${agreement.insurance_verified ? 'checked' : ''} />
                Verzekering is in orde
              </label>
            </div>
            <div class="btn-group">
              <button id="btn-validate" class="btn success">✓ Valideren</button>
              <button id="btn-incomplete" class="btn danger">✗ Onvolledig</button>
            </div>
          </div>
        `;

        document.getElementById('btn-validate')?.addEventListener('click', () => {
          const insuranceVerified = document.getElementById('insurance-check')?.checked || false;
          validateAgreement(internship.id, 'Gevalideerd', insuranceVerified);
        });

        document.getElementById('btn-incomplete')?.addEventListener('click', () => {
          const insuranceVerified = document.getElementById('insurance-check')?.checked || false;
          validateAgreement(internship.id, 'Onvolledig', insuranceVerified);
        });
      }
    }

    // Attach download handler
    document.getElementById('download-agreement-btn')?.addEventListener('click', async () => {
      const btn = document.getElementById('download-agreement-btn');
      showLoading(btn, 'Downloaden...');
      try {
        await AgreementsAPI.download(internship.id);
        hideLoading(btn);
      } catch (error) {
        hideLoading(btn);
        showToast(error.message, 'error');
      }
    });
  }).catch(() => {
    detailContainer.innerHTML = '<p class="error">Kon overeenkomstgegevens niet laden.</p>';
  });
}

async function validateAgreement(internshipId, status, insuranceVerified) {
  try {
    await AgreementsAPI.validate(internshipId, status, insuranceVerified);
    showToast(`Overeenkomst gemarkeerd als ${status.toLowerCase()}!`, 'success');
    // Refresh data
    allInternships = await InternshipsAPI.list();
    renderCommitteeAgreements();
    // Refresh detail panel
    showAgreementDetailPanel(internshipId);
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function renderCommitteeOverview() {
  try {
    const stats = await InternshipsAPI.getDashboardStats();

    // Statistieken bijwerken
    const statElements = document.querySelectorAll('.grid.two-col ul');
    if (statElements[0]) {
      statElements[0].innerHTML = `
        <li>Totaal voorstellen: ${stats.total_internships}</li>
        <li>Goedgekeurd: ${stats.approved}</li>
        <li>In behandeling: ${stats.pending_approval}</li>
        <li>Afgekeurd: ${stats.rejected}</li>
      `;
    }
    if (statElements[1]) {
      statElements[1].innerHTML = `
        <li>Ontvangen: ${stats.agreements_received}</li>
        <li>Nog uitstaand: ${stats.agreements_pending}</li>
      `;
    }

    // Tabel bijwerken
    const tbody = document.querySelector('table tbody');
    if (tbody) {
      tbody.innerHTML = allInternships.map(p => `
        <tr>
          <td>${p.student?.first_name || 'Onbekend'}</td>
          <td>${p.company?.name || 'Onbekend'}</td>
          <td>${formatDate(p.start_date)} - ${formatDate(p.end_date)}</td>
          <td><span class="status-pill ${getStatusClass(p.status)}">${p.status}</span></td>
          <td>${p.agreement_uploaded ? '<span class="status-pill status-good">Ontvangen</span>' : '<span class="status-pill status-warn">Nog niet</span>'}</td>
        </tr>
      `).join('');
    }
  } catch (error) {
    showToast(error.message, 'error');
  }
}

// ============================================
// Blootstellen aan window voor template onclick-handlers
window.selectProposalForReview = selectProposalForReview;
window.doReview = doReview;
