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
        <button id="btn-review" class="btn">${iconHtml('search', 14)} In Beoordeling Zetten</button>
      `;
      document.getElementById('btn-review')?.addEventListener('click', () => doReview(internship.id, 'In Beoordeling'));
    } else if (status === 'In Beoordeling') {
      // Dan pas beslissen — docent is verplicht, mentor is optioneel bij goedkeuring
      actionsDiv.innerHTML = `
        <div class="row full" style="margin-bottom: 0.75rem;">
          <label>Docent aanduiden (verplicht bij goedkeuring)</label>
          <select id="approve-teacher-select">
            <option value="">Laden...</option>
          </select>
        </div>
        <div class="row full" style="margin-bottom: 0.75rem;">
          <label>Mentor aanduiden (optioneel bij goedkeuring)</label>
          <select id="approve-mentor-select">
            <option value="">-- Geen mentor --</option>
          </select>
        </div>
        <button id="btn-approve" class="btn success">${iconHtml('check-circle', 14)} Goedkeuren</button>
        <button id="btn-reject" class="btn danger">${iconHtml('x-circle', 14)} Afkeuren</button>
        <button id="btn-changes" class="btn secondary">${iconHtml('alert-circle', 14)} Aanpassingen Vereist</button>
      `;

      // Laad docenten in de dropdown
      UsersAPI.list('teacher').then(teachers => {
        const select = document.getElementById('approve-teacher-select');
        if (select) {
          select.innerHTML = '<option value="">-- Kies een docent --</option>' +
            teachers.map(t => `<option value="${t.id}">${t.first_name} ${t.last_name}</option>`).join('');
        }
      }).catch(() => {
        const select = document.getElementById('approve-teacher-select');
        if (select) select.innerHTML = '<option value="">Kon docenten niet laden</option>';
      });

      // Laad mentors in de dropdown
      UsersAPI.list('mentor').then(mentors => {
        const select = document.getElementById('approve-mentor-select');
        if (select) {
          select.innerHTML = '<option value="">-- Geen mentor --</option>' +
            mentors.map(m => `<option value="${m.id}">${m.first_name} ${m.last_name}</option>`).join('');
        }
      }).catch(() => {
        const select = document.getElementById('approve-mentor-select');
        if (select) select.innerHTML = '<option value="">Kon mentors niet laden</option>';
      });

      document.getElementById('btn-approve')?.addEventListener('click', () => {
        const teacherId = parseInt(document.getElementById('approve-teacher-select')?.value);
        if (!teacherId) {
          showToast('Duid eerst een docent aan voor goedkeuring', 'warning');
          return;
        }
        // Mentor is optioneel — null als niets gekozen
        const mentorVal = document.getElementById('approve-mentor-select')?.value;
        const mentorId = mentorVal ? parseInt(mentorVal) : null;
        doReview(internship.id, 'Goedgekeurd', teacherId, mentorId);
      });
      document.getElementById('btn-reject')?.addEventListener('click', () => doReview(internship.id, 'Afgekeurd'));
      document.getElementById('btn-changes')?.addEventListener('click', () => doReview(internship.id, 'Aanpassingen Vereist'));
    } else {
      actionsDiv.innerHTML = '<p class="hint">Voorstel is al beoordeeld.</p>';
    }
  }
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
      const agreementStatuses = ['Goedgekeurd', 'Overeenkomst Ingediend', 'Lopend', 'Afgerond'];
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

  document.getElementById('agreement-student-name').textContent =
    `${internship.student?.first_name || ''} ${internship.student?.last_name || ''}`;
  document.getElementById('agreement-company').textContent = internship.company?.name || 'Onbekend';
  document.getElementById('agreement-internship-status').textContent = internship.status;

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

// ============================================
// Blootstellen aan window voor template onclick-handlers
window.selectProposalForReview = selectProposalForReview;
window.doReview = doReview;
