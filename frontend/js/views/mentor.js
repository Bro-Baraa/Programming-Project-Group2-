async function renderMentorLogbooks() {
  const tbody = document.querySelector('#mentor-logbooks-table tbody');
  if (!tbody) return;

  if (!currentInternship) {
    tbody.innerHTML = '<tr><td colspan="6">Selecteer een stage via het navigatiemenu.</td></tr>';
    const existingCtx = document.getElementById('mentor-stage-context');
    if (existingCtx) existingCtx.remove();
    return;
  }

  const table = document.getElementById('mentor-logbooks-table');
  let stageCtx = document.getElementById('mentor-stage-context');
  if (!stageCtx) {
    stageCtx = document.createElement('div');
    stageCtx.id = 'mentor-stage-context';
    table.parentNode.insertBefore(stageCtx, table);
  }
  const companyName = currentInternship.company_name || currentInternship.company?.name || 'Onbekend';
  const assignment = currentInternship.assignment_description || '-';
  const startDate = currentInternship.start_date || '-';
  const endDate = currentInternship.end_date || '-';
  stageCtx.className = 'stage-context card';
  stageCtx.innerHTML = `
    <h3>Stage-informatie</h3>
    <p><strong>Bedrijf:</strong> ${escapeHtml(companyName)}</p>
    <p><strong>Opdracht:</strong> ${escapeHtml(assignment)}</p>
    <p><strong>Periode:</strong> ${escapeHtml(startDate)} t/m ${escapeHtml(endDate)}</p>
  `;

  const start = currentInternship.start_date ? new Date(currentInternship.start_date) : null;
  const end = currentInternship.end_date ? new Date(currentInternship.end_date) : null;
  let totalDays = 0;
  if (start && end && end >= start) {
    totalDays = Math.floor((end - start) / (1000 * 60 * 60 * 24)) + 1;
  }

  const logbookMap = new Map();
  for (const lb of currentLogbooks) {
    if (lb.entry_date) {
      logbookMap.set(lb.entry_date, lb);
    } else if (lb.week_number && start) {
      const computed = new Date(start);
      computed.setDate(computed.getDate() + (lb.week_number - 1) * 7);
      logbookMap.set(computed.toISOString().split('T')[0], lb);
    }
  }

  const rows = [];
  for (let d = 0; d < totalDays; d++) {
    const dayDate = new Date(start);
    dayDate.setDate(dayDate.getDate() + d);
    const dateStr = dayDate.toISOString().split('T')[0];
    const lb = logbookMap.get(dateStr);
    const dayLabel = `${dayDate.getDate()}/${dayDate.getMonth() + 1}`;
    if (!lb) {
      rows.push(`
        <tr class="missing-row">
          <td>${dayLabel}</td>
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
          <td>${dayLabel}</td>
          <td>${escapeHtml(lb.tasks || '-')}</td>
          <td>${escapeHtml(lb.reflection || '-')}</td>
          <td><span class="status-pill ${getStatusClass(lb.status)}">${lb.status === 'submitted' ? 'Ingediend' : 'Concept'}</span></td>
          <td>
            <textarea class="mentor-feedback-input" data-id="${lb.id}" rows="2" placeholder="Feedback voor deze dag..." style="width:100%; min-width:160px; font-size:0.85rem;">${escapeHtml(lb.mentor_feedback || '')}</textarea>
            <button class="btn small save-feedback-btn" data-id="${lb.id}" style="margin-top:0.25rem;">${iconHtml('check-circle', 14)} Opslaan</button>
          </td>
          <td>${actionCell}</td>
        </tr>
      `);
    }
  }
  tbody.innerHTML = rows.join('') || '<tr><td colspan="6">Geen logboeken gevonden voor deze stage.</td></tr>';

  tbody.querySelectorAll('.validate-logbook-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const logbookId = parseInt(btn.dataset.id);
      await withLoading(btn, 'Bezig...', async () => {
        await apiRequest(`/internships/logbooks/${logbookId}`, {
          method: 'PATCH',
          body: JSON.stringify({ mentor_validated: true })
        });
        showToast('Logboek gevalideerd!', 'success');
        currentLogbooks = await InternshipsAPI.getLogbooks(currentInternship.id);
        renderMentorLogbooks();
      });
    });
  });

  tbody.querySelectorAll('.save-feedback-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
      const logbookId = parseInt(btn.dataset.id);
      const textarea = tbody.querySelector(`.mentor-feedback-input[data-id="${logbookId}"]`);
      const feedback = textarea?.value || '';
      await withLoading(btn, 'Bezig...', async () => {
        await apiRequest(`/internships/logbooks/${logbookId}`, {
          method: 'PATCH',
          body: JSON.stringify({ mentor_feedback: feedback })
        });
        showToast('Feedback opgeslagen!', 'success');
      });
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
}
