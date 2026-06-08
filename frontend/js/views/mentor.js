async function renderMentorLogbooks() {
  const tbody = document.querySelector('#mentor-logbooks-table tbody');
  if (!tbody) return;

  if (!currentInternship) {
    tbody.innerHTML = '<tr><td colspan="6">Selecteer een stage via het navigatiemenu.</td></tr>';
    return;
  }

  // Berekend weekoverzicht lokaal vanuit currentInternship + currentLogbooks
  const start = currentInternship.start_date ? new Date(currentInternship.start_date) : null;
  const end = currentInternship.end_date ? new Date(currentInternship.end_date) : null;
  let totalWeeks = 0;
  if (start && end && end > start) {
    const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
    totalWeeks = Math.max(1, Math.floor(days / 7) + 1);
  }

  const logbookMap = new Map(currentLogbooks.map(lb => [lb.week_number, lb]));
  const rows = [];
  for (let w = 1; w <= totalWeeks; w++) {
    const lb = logbookMap.get(w);
    if (!lb) {
      rows.push(`
        <tr class="missing-row">
          <td>${w}</td>
          <td colspan="3"><span class="status-pill status-warn">Ontbrekend</span></td>
          <td>-</td>
          <td>-</td>
        </tr>
      `);
    } else {
      let actionCell;
      if (lb.mentor_validated) {
        actionCell = `<span class="status-pill status-good">${iconHtml('check-circle', 14)} Gevalideerd</span>`;
      } else if (lb.status === 'submitted') {
        actionCell = `<button class="btn small validate-logbook-btn" data-id="${lb.id}">${iconHtml('check-circle', 14)} Valideren</button>`;
      } else {
        actionCell = '<span class="status-pill">Concept</span>';
      }

      rows.push(`
        <tr data-logbook-id="${lb.id}">
          <td>${w}</td>
          <td>${escapeHtml(lb.tasks || '-')}</td>
          <td>${escapeHtml(lb.reflection || '-')}</td>
          <td><span class="status-pill ${getStatusClass(lb.status)}">${lb.status === 'submitted' ? 'Ingediend' : 'Concept'}</span></td>
          <td>
            <textarea class="mentor-feedback-input" data-id="${lb.id}" rows="2" placeholder="Feedback voor deze week..." style="width:100%; min-width:160px; font-size:0.85rem;">${escapeHtml(lb.mentor_feedback || '')}</textarea>
            <button class="btn small save-feedback-btn" data-id="${lb.id}" style="margin-top:0.25rem;">${iconHtml('check-circle', 14)} Opslaan</button>
          </td>
          <td>${actionCell}</td>
        </tr>
      `);
    }
  }
  tbody.innerHTML = rows.join('') || '<tr><td colspan="6">Geen logboeken gevonden voor deze stage.</td></tr>';

  // Validatieknoppen verbinden
  tbody.querySelectorAll('.validate-logbook-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const logbookId = parseInt(btn.dataset.id);
      showLoading(btn, 'Bezig...');
      try {
        await apiRequest(`/internships/logbooks/${logbookId}`, {
          method: 'PATCH',
          body: JSON.stringify({ mentor_validated: true })
        });
        hideLoading(btn);
        showToast('Logboek gevalideerd!', 'success');
        // Vernieuw logboeken
        currentLogbooks = await InternshipsAPI.getLogbooks(currentInternship.id);
        renderMentorLogbooks();
      } catch (error) {
        hideLoading(btn);
        showToast(error.message, 'error');
      }
    });
  });

  // Feedback opslaan knoppen verbinden
  tbody.querySelectorAll('.save-feedback-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const logbookId = parseInt(btn.dataset.id);
      const textarea = tbody.querySelector(`.mentor-feedback-input[data-id="${logbookId}"]`);
      const feedback = textarea?.value || '';
      showLoading(btn, 'Bezig...');
      try {
        await apiRequest(`/internships/logbooks/${logbookId}`, {
          method: 'PATCH',
          body: JSON.stringify({ mentor_feedback: feedback })
        });
        hideLoading(btn);
        showToast('Feedback opgeslagen!', 'success');
      } catch (error) {
        hideLoading(btn);
        showToast(error.message, 'error');
      }
    });
  });
}

// Renderen van mentor-feedbackformulier per competentie
async function renderMentorEvaluation() {
  const container = document.getElementById('mentor-eval-content');
  if (!container) return;

  if (!currentInternship) {
    container.innerHTML = '<p>Selecteer een stage via het navigatiemenu.</p>';
    return;
  }

  // Zoek actieve evaluatie, anders de meest recente gefinaliseerde
  const draft = currentEvaluations.find(e => !e.finalized);
  const finalized = currentEvaluations.filter(e => e.finalized);
  const actieveEval = draft || finalized.find(e => e.eval_type === 'final') || finalized[finalized.length - 1] || null;
  const isReadOnly = !draft && !!actieveEval;

  if (!actieveEval) {
    container.innerHTML = '<p>Geen evaluatie gevonden voor deze stage.</p>';
    return;
  }

  const readOnlyAttr = isReadOnly ? 'readonly' : '';
  const saveBtnHtml = isReadOnly
    ? '<p class="hint">Deze evaluatie is definitief afgesloten. Feedback kan niet meer worden gewijzigd.</p>'
    : `<button id="save-mentor-feedback" class="btn">${iconHtml('check-circle', 14)} Feedback Opslaan</button>`;

  container.innerHTML = `
  <div style="margin-bottom: 1rem;">
    <span class="status-pill ${isReadOnly ? 'status-good' : 'status-info'}">${isReadOnly ? `${iconHtml('check-circle', 14)} Afgeronde evaluatie` : 'Actieve evaluatie'}</span>
    <span class="hint" style="margin-left: 0.5rem;">${actieveEval.eval_type === 'final' ? 'Finale evaluatie' : 'Tussentijdse evaluatie'}</span>
  </div>
  ${currentCompetencies.map(comp => {
    const rule = actieveEval.rules?.find(r => r.competency_id === comp.id);
    const scoreLabel = rule?.score ? `${rule.score}/5` : '-';
    return `
      <div class="mentor-eval-row" style="margin-bottom: 1rem;">
        <label><strong>${comp.name}</strong> (${comp.weight}%)</label>
        <p style="margin: 0.25rem 0; font-size: 0.9rem; color: var(--ink-soft);">Score: <span class="score-highlight">${scoreLabel}</span></p>
        <textarea data-rule-id="${rule?.id ?? ''}" placeholder="Geef hier je feedback..." ${readOnlyAttr}>${rule?.evaluator_feedback || ''}</textarea>
      </div>
    `;
  }).join('')}
  ${saveBtnHtml}`;

  if (!isReadOnly) {
    document.getElementById('save-mentor-feedback')?.addEventListener('click', async () => {
      const textareas = container.querySelectorAll('textarea');

      for (const textarea of textareas) {
        const ruleId = textarea.dataset.ruleId;
        const feedback = textarea.value;

        if (ruleId) {
          await EvaluationRulesAPI.update(actieveEval.id, ruleId, { evaluator_feedback: feedback });
        }
      }
      showToast('Feedback opgeslagen!', 'success');
    });
  }

  // PDF-exportknop toevoegen voor mentors (altijd zichtbaar in evaluatieweergave)
  const exportWrap = document.createElement('div');
  exportWrap.style.marginTop = '1rem';
  exportWrap.innerHTML = `<button class="btn" id="mentor-export-pdf-btn">${iconHtml('download', 16)} Exporteer Stage als PDF</button>`;
  container.appendChild(exportWrap);

  document.getElementById('mentor-export-pdf-btn')?.addEventListener('click', async () => {
    if (!currentInternship) return;
    const btn = document.getElementById('mentor-export-pdf-btn');
    const studentName = `${currentInternship.student?.first_name || ''} ${currentInternship.student?.last_name || ''}`.trim();
    showLoading(btn, 'Bezig...');
    try {
      await InternshipsAPI.exportPdf(currentInternship.id, studentName);
      hideLoading(btn);
    } catch (error) {
      hideLoading(btn);
      showToast(`PDF exporteren mislukt: ${error.message}`, 'error');
    }
  });
}