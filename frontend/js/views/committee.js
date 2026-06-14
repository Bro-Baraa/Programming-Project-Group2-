function _agreementCell(p) {
  if (p.status === 'Afgekeurd') return '<span class="hint">-</span>';
  if (p.agreement_uploaded) return '<span class="status-pill status-good">Ontvangen</span>';
  return '<span class="status-pill status-warn">Nog niet</span>';
}

async function renderCommitteeProposals() {
  try {
    const tbody = document.querySelector('#proposals-table tbody');
    if (!tbody) return;

    tbody.innerHTML = allInternships.map(p => `
      <tr data-id="${p.id}" class="proposal-row">
        <td>${p.student?.first_name || 'Onbekend'} ${p.student?.last_name || ''}</td>
        <td>${p.company?.name || 'Onbekend'}</td>
        <td>${new Date(p.created_at).toLocaleDateString('nl-BE')}</td>
        <td><span class="status-pill ${getStatusClass(p.status)}">${p.status}</span></td>
        <td>${_agreementCell(p)}</td>
      </tr>
    `).join('');

    tbody.querySelectorAll('.proposal-row').forEach(row => {
      row.addEventListener('click', () => selectProposalForReview(parseInt(row.dataset.id)));
    });

    if (selectedInternshipId) {
      const preselected = allInternships.find(i => i.id == selectedInternshipId);
      if (preselected) selectProposalForReview(preselected.id);
    }
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function _setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function _loadSelect(id, role, emptyLabel) {
  UsersAPI.list(role).then(users => {
    const select = document.getElementById(id);
    if (select) select.innerHTML = `<option value="">${emptyLabel}</option>` +
      users.map(u => `<option value="${u.id}">${u.first_name} ${u.last_name}</option>`).join('');
  }).catch(() => {
    const select = document.getElementById(id);
    if (select) select.innerHTML = `<option value="">Kon ${role}s niet laden</option>`;
  });
}

function _renderReviewActions(internship) {
  const actionsDiv = document.getElementById('review-actions');
  if (!actionsDiv) return;

  const status = internship.status;
  if (status === 'Ingediend' || status === 'Aanpassingen Vereist') {
    actionsDiv.innerHTML = `<button id="btn-review" class="btn">${iconHtml('search', 14)} In Beoordeling Zetten</button>`;
    document.getElementById('btn-review')?.addEventListener('click', () => doReview(internship.id, 'In Beoordeling'));
    return;
  }

  if (status === 'In Beoordeling') {
    actionsDiv.innerHTML = `
      <div class="row full" style="margin-bottom: 0.75rem;">
        <label>Docent aanduiden (verplicht bij goedkeuring)</label>
        <select id="approve-teacher-select"><option value="">Laden...</option></select>
      </div>
      <div class="row full" style="margin-bottom: 0.75rem;">
        <label>Mentor aanduiden (optioneel bij goedkeuring)</label>
        <select id="approve-mentor-select"><option value="">-- Geen mentor --</option></select>
      </div>
      <button id="btn-approve" class="btn success">${iconHtml('check-circle', 14)} Goedkeuren</button>
      <button id="btn-reject" class="btn danger">${iconHtml('x-circle', 14)} Afkeuren</button>
      <button id="btn-changes" class="btn secondary">${iconHtml('alert-circle', 14)} Aanpassingen Vereist</button>
    `;

    _loadSelect('approve-teacher-select', 'teacher', '-- Kies een docent --');
    _loadSelect('approve-mentor-select', 'mentor', '-- Geen mentor --');

    document.getElementById('btn-approve')?.addEventListener('click', () => {
      const teacherId = parseInt(document.getElementById('approve-teacher-select')?.value);
      if (!teacherId) {
        showToast('Duid eerst een docent aan voor goedkeuring', 'warning');
        return;
      }
      const mentorId = document.getElementById('approve-mentor-select')?.value || null;
      doReview(internship.id, 'Goedgekeurd', teacherId, mentorId ? parseInt(mentorId) : null);
    });
    // 'Afgekeurd' moet exact overeenkomen met de backend-statusovergang (lifecycle.py).
    document.getElementById('btn-reject')?.addEventListener('click', () => doReview(internship.id, 'Afgekeurd'));
    document.getElementById('btn-changes')?.addEventListener('click', () => doReview(internship.id, 'Aanpassingen Vereist'));
    return;
  }

  actionsDiv.innerHTML = '<p class="hint">Voorstel is al beoordeeld.</p>';
}

function selectProposalForReview(internshipId) {
  const internship = allInternships.find(i => i.id == internshipId);
  if (!internship) return;

  selectedInternshipId = internshipId;
  currentInternship = internship;
  const url = new URL(window.location.href);
  url.searchParams.set('internship', internshipId);
  window.history.replaceState({}, '', url);

  document.querySelectorAll('.proposal-row').forEach(r => {
    r.style.background = r.dataset.id == internshipId ? 'rgba(0, 121, 140, 0.1)' : '';
  });

  const modal = document.getElementById('proposal-review-modal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    wireReviewModalClose(modal);
  }

  _setText('selected-student-name', `${internship.student?.first_name || ''} ${internship.student?.last_name || ''}`);
  _setText('selected-company', internship.company?.name || 'Onbekend');
  _setText('selected-status', internship.status);

  _setText('selected-description', 'Laden...');
  InternshipsAPI.get(internship.id).then(full => {
    _setText('selected-description', full.proposal?.description || 'Geen omschrijving beschikbaar.');
    const feedbackBox = document.getElementById('feedback-box');
    if (feedbackBox && full.proposal?.feedback) feedbackBox.value = full.proposal.feedback;
  }).catch(() => {
    _setText('selected-description', 'Kon omschrijving niet laden.');
  });

  _renderReviewActions(internship);
}

function wireReviewModalClose(modal) {
  if (modal.dataset.closeWired) return;
  modal.dataset.closeWired = '1';
  const close = () => {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  };
  document.getElementById('btn-close-review')?.addEventListener('click', close);
  modal.querySelector('.modal-overlay')?.addEventListener('click', close);
}

async function doReview(internshipId, decision, teacherId = null, mentorId = null) {
  const feedback = document.getElementById('feedback-box')?.value || null;

  if (decision === 'Aanpassingen Vereist' && !feedback) {
    showToast('Feedback is verplicht bij "Aanpassingen Vereist"', 'warning');
    return;
  }

  try {
    await ProposalsAPI.review(internshipId, decision, feedback, teacherId, mentorId);
    showToast(`Voorstel ${decision.toLowerCase()}!`, 'success');
    // Gegevens verversen (paginatie-safe via app.js helper)
    allInternships = await loadAllInternships();
    renderCommitteeProposals();
  } catch (error) {
    showToast(error.message, 'error');
  }
}

async function renderCommitteeAgreements() {
  try {
    const tbody = document.querySelector('#agreements-table tbody');

    if (tbody) {
      const agreementStatuses = ['Goedgekeurd', 'Overeenkomst Ingediend', 'Lopend', 'Afgerond', 'Stopgezet'];
      const stagesWithAgreements = allInternships.filter(
        i => agreementStatuses.includes(i.status) || i.agreement_uploaded
      );

      if (stagesWithAgreements.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6">Geen stages met overeenkomsten gevonden.</td></tr>';
      } else {
        tbody.innerHTML = stagesWithAgreements.map(i => {
          const agreementStatus = i.agreement_status || 'Niet Ingediend';
          return `
            <tr data-id="${i.id}" class="agreement-row">
              <td>${i.student?.first_name || 'Onbekend'} ${i.student?.last_name || ''}</td>
              <td>${i.company?.name || 'Onbekend'}</td>
              <td><span class="status-pill ${getStatusClass(i.status)}">${i.status}</span></td>
              <td>${renderAgreementStatusCell(agreementStatus)}</td>
              <td>${renderAgreementUploadedCell(i.agreement_uploaded)}</td>
              <td>
                <button class="btn small view-agreement-btn" data-id="${i.id}">${iconHtml('eye', 14)} Bekijken</button>
              </td>
            </tr>
          `;
        }).join('');

        tbody.querySelectorAll('.view-agreement-btn').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const id = parseInt(btn.dataset.id);
            showAgreementDetailPanel(id);
          });
        });
      }
    }

    const panel = document.getElementById('agreement-detail-panel');
    if (panel) panel.style.display = 'none';
  } catch (error) {
    showToast(error.message, 'error');
  }
}

// Vult een <select> met gebruikers van een bepaalde rol en selecteert eventueel de huidige persoon.
// Variant op _loadSelect die ook een reeds toegewezen waarde kan voorselecteren.
function _loadSelectWithCurrent(id, role, emptyLabel, selectedId) {
  UsersAPI.list(role).then(users => {
    const select = document.getElementById(id);
    if (!select) return;
    select.innerHTML = `<option value="">${emptyLabel}</option>` +
      users.map(u => {
        const selected = (selectedId && u.id === selectedId) ? ' selected' : '';
        return `<option value="${u.id}"${selected}>${u.first_name} ${u.last_name}</option>`;
      }).join('');
  }).catch(() => {
    const select = document.getElementById(id);
    if (select) select.innerHTML = `<option value="">Kon ${role}s niet laden</option>`;
  });
}

// Toont het paneel om docent/mentor opnieuw toe te wijzen (US: wendbaarheid — opvolging kan wijzigen).
// Alleen zichtbaar voor commissie en admin. Werkt in elke fase, ook bij een lopende stage.
function _renderReassignSection(internship) {
  const role = AuthAPI.getRole();
  if (role !== 'committee' && role !== 'admin') return;

  const container = document.getElementById('agreement-detail-content');
  if (!container) return;

  // Eigen blok toevoegen onderaan het detailpaneel (we raken de bestaande inhoud niet aan).
  const section = document.createElement('div');
  section.className = 'reassign-form';
  section.style.marginTop = '1.5rem';
  section.style.paddingTop = '1rem';
  section.style.borderTop = '1px solid var(--border, #ddd)';
  // Een stage stopzetten kan enkel als ze nog niet in een eindstatus zit.
  const canTerminate = !['Afgerond', 'Stopgezet', 'Afgekeurd'].includes(internship.status);
  const terminateHtml = canTerminate
    ? `<button id="btn-terminate" class="btn danger" style="margin-top: 0.75rem;">${iconHtml('x-circle', 14)} Stage stopzetten</button>`
    : '';

  section.innerHTML = `
    <h4 style="margin-bottom: 0.75rem;">${iconHtml('users', 16)} Begeleiding wijzigen</h4>
    <div class="row full" style="margin-bottom: 0.75rem;">
      <label>Docent</label>
      <select id="reassign-teacher-select"><option value="">Laden...</option></select>
    </div>
    <div class="row full" style="margin-bottom: 0.75rem;">
      <label>Mentor</label>
      <select id="reassign-mentor-select"><option value="">-- Geen mentor --</option></select>
    </div>
    <button id="btn-reassign" class="btn">${iconHtml('check-circle', 14)} Wijzigingen opslaan</button>
    ${terminateHtml}
  `;
  container.appendChild(section);

  // Dropdowns vullen en huidige toewijzing voorselecteren.
  _loadSelectWithCurrent('reassign-teacher-select', 'teacher', '-- Geen docent --', internship.teacher?.id);
  _loadSelectWithCurrent('reassign-mentor-select', 'mentor', '-- Geen mentor --', internship.mentor?.id);

  document.getElementById('btn-reassign')?.addEventListener('click', () => reassignSupervisors(internship.id));
  document.getElementById('btn-terminate')?.addEventListener('click', () => terminateInternship(internship.id));
}

async function reassignSupervisors(internshipId) {
  const teacherVal = document.getElementById('reassign-teacher-select')?.value || '';
  const mentorVal = document.getElementById('reassign-mentor-select')?.value || '';

  // Lege keuze betekent 'niet wijzigen' — we sturen alleen velden mee die een waarde hebben.
  const data = {};
  if (teacherVal) data.teacher_id = parseInt(teacherVal);
  if (mentorVal) data.mentor_id = parseInt(mentorVal);

  if (Object.keys(data).length === 0) {
    showToast('Kies een docent of mentor om te wijzigen', 'warning');
    return;
  }

  try {
    await InternshipsAPI.update(internshipId, data);
    showToast('Begeleiding bijgewerkt!', 'success');
    // Data verversen zodat de nieuwe toewijzing overal klopt.
    allInternships = await loadAllInternships();
    showAgreementDetailPanel(internshipId);
  } catch (error) {
    showToast(error.message, 'error');
  }
}

// Zet een stage vroegtijdig stop. Vraagt eerst een reden (verplicht).
async function terminateInternship(internshipId) {
  // prompt() dient meteen als bevestiging én als invoer van de reden.
  // Annuleren (null) of een lege reden stopt de actie.
  const reason = window.prompt('Reden om deze stage stop te zetten (verplicht):');
  if (reason === null) return; // gebruiker annuleerde
  if (!reason.trim()) {
    showToast('Een reden is verplicht om de stage stop te zetten', 'warning');
    return;
  }

  try {
    await InternshipsAPI.terminate(internshipId, reason.trim());
    showToast('Stage stopgezet', 'info');
    // Data verversen (status wordt Stopgezet) en detail opnieuw tonen.
    allInternships = await loadAllInternships();
    showAgreementDetailPanel(internshipId);
  } catch (error) {
    showToast(error.message, 'error');
  }
}

function showAgreementDetailPanel(internshipId) {
  const internship = allInternships.find(i => i.id === internshipId);
  if (!internship) return;

  selectedInternshipId = internshipId;
  currentInternship = internship;
  const url = new URL(window.location.href);
  url.searchParams.set('internship', internshipId);
  window.history.replaceState({}, '', url);

  const panel = document.getElementById('agreement-detail-panel');
  if (panel) panel.style.display = 'block';

  _setText('agreement-student-name', `${internship.student?.first_name || ''} ${internship.student?.last_name || ''}`);
  _setText('agreement-company', internship.company?.name || 'Onbekend');
  _setText('agreement-internship-status', internship.status);

  const detailContainer = document.getElementById('agreement-detail-content');
  detailContainer.innerHTML = '<p>Laden...</p>';

  InternshipsAPI.get(internship.id).then(full => {
    const agreement = full.agreement;
    if (!agreement) {
      detailContainer.innerHTML = `
        <div class="info-message warning">
          <p>${iconHtml('alert-circle', 16)} Er is nog geen overeenkomst geüpload voor deze stage.</p>
        </div>
      `;
      document.getElementById('agreement-actions').innerHTML = '';
      return;
    }

    detailContainer.innerHTML = renderAgreementDetailHTML(agreement, {
      showDownload: true,
      showInsurance: true,
      showValidation: true,
    });
    attachAgreementDownload(internship.id);

    // Begeleiding-wijzigen paneel toevoegen (alleen commissie/admin, in elke fase).
    _renderReassignSection(internship);

    const actionsDiv = document.getElementById('agreement-actions');
    if (actionsDiv) {
      const isValidated = agreement.status === 'Gevalideerd';
      if (isValidated) {
        actionsDiv.innerHTML = `
          <div class="info-message success">
            <p>${iconHtml('check-circle', 16)} Deze overeenkomst is gevalideerd. De stage is actief.</p>
          </div>
        `;
      } else {
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
  }).catch(() => {
    detailContainer.innerHTML = '<p class="error">Kon overeenkomstgegevens niet laden.</p>';
  });
}

async function validateAgreement(internshipId, status, insuranceVerified) {
  try {
    await AgreementsAPI.validate(internshipId, status, insuranceVerified);
    showToast(`Overeenkomst gemarkeerd als ${status.toLowerCase()}!`, 'success');
    // Refresh data
    allInternships = await loadAllInternships();
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
        <li>Stopgezet: ${stats.stopped || 0}</li>
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
          <td>${p.student?.first_name || 'Onbekend'} ${p.student?.last_name || ''}</td>
          <td>${p.company?.name || 'Onbekend'}</td>
          <td>${formatDate(p.start_date)} - ${formatDate(p.end_date)}</td>
          <td><span class="status-pill ${getStatusClass(p.status)}">${p.status}</span></td>
          <td>${p.agreement_uploaded ? '<span class="status-pill status-good">Ontvangen</span>' : '<span class="status-pill status-warn">Nog niet</span>'}</td>
          <td>${p.teacher ? `${p.teacher.first_name} ${p.teacher.last_name}` : '<span class="hint">Niet toegewezen</span>'}</td>
        </tr>
      `).join('');
    }
  } catch (error) {
    showToast(error.message, 'error');
  }
}

window.selectProposalForReview = selectProposalForReview;
window.doReview = doReview;
