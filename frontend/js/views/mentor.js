async function renderMentorLogbooks() {
  const tbody = document.querySelector('#mentor-logbooks-table tbody');
  if (!tbody) return;

  if (!currentInternship) {
    tbody.innerHTML = '<tr><td colspan="6">Selecteer een stage via het navigatiemenu.</td></tr>';
    return;
  }

  try {
    const weeks = await InternshipsAPI.getLogbookWeeks(currentInternship.id);
    const logbookMap = new Map(currentLogbooks.map(lb => [lb.week_number, lb]));
    tbody.innerHTML = weeks.map(w => {
      if (w.status === 'missing') {
        return `
          <tr class="missing-row">
            <td>${w.week_number}</td>
            <td colspan="3"><span class="status-pill status-warn">Ontbrekend</span></td>
            <td>-</td>
            <td>-</td>
          </tr>
        `;
      }
      const lb = logbookMap.get(w.week_number);
      let actionCell;
      if (w.mentor_validated) {
        actionCell = '<span class="status-pill status-good">✓ Gevalideerd</span>';
      } else if (w.status === 'submitted') {
        actionCell = `<button class="btn small validate-logbook-btn" data-id="${lb?.id}">Valideren</button>`;
      } else {
        actionCell = '<span class="status-pill">Concept</span>';
      }

      return `
        <tr data-logbook-id="${lb?.id ?? ''}">
          <td>${w.week_number}</td>
          <td>${lb?.tasks || '-'}</td>
          <td>${lb?.reflection || '-'}</td>
          <td><span class="status-pill ${getStatusClass(w.status)}">${w.status === 'submitted' ? 'Ingediend' : 'Concept'}</span></td>
          <td>
            <textarea class="mentor-feedback-input" data-id="${lb?.id}" rows="2" placeholder="Feedback voor deze week..." style="width:100%; min-width:160px; font-size:0.85rem;">${lb?.mentor_feedback || ''}</textarea>
            <button class="btn small save-feedback-btn" data-id="${lb?.id}" style="margin-top:0.25rem;">Opslaan</button>
          </td>
          <td>${actionCell}</td>
        </tr>
      `;
    }).join('');
  } catch (error) {
    console.error('Failed to load week overview:', error);
    tbody.innerHTML = currentLogbooks.map(lb => {
      let actionCell;
      if (lb.mentor_validated) {
        actionCell = '<span class="status-pill status-good">✓ Gevalideerd</span>';
      } else if (lb.status === 'submitted') {
        actionCell = `<button class="btn small validate-logbook-btn" data-id="${lb.id}">Valideren</button>`;
      } else {
        actionCell = '<span class="status-pill">Concept</span>';
      }

      return `
        <tr data-logbook-id="${lb.id}">
          <td>${lb.week_number}</td>
          <td>${lb.tasks || '-'}</td>
          <td>${lb.reflection || '-'}</td>
          <td><span class="status-pill ${getStatusClass(lb.status)}">${lb.status === 'submitted' ? 'Ingediend' : 'Concept'}</span></td>
          <td>
            <textarea class="mentor-feedback-input" data-id="${lb.id}" rows="2" placeholder="Feedback voor deze week..." style="width:100%; min-width:160px; font-size:0.85rem;">${lb.mentor_feedback || ''}</textarea>
            <button class="btn small save-feedback-btn" data-id="${lb.id}" style="margin-top:0.25rem;">Opslaan</button>
          </td>
          <td>${actionCell}</td>
        </tr>
      `;
    }).join('') || '<tr><td colspan="6">Geen logboeken gevonden voor deze stage.</td></tr>';
  }

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
    : '<button id="save-mentor-feedback" class="btn">Feedback Opslaan</button>';

  container.innerHTML = `
  <div style="margin-bottom: 1rem;">
    <span class="status-pill ${isReadOnly ? 'status-good' : 'status-info'}">${isReadOnly ? '✓ Afgeronde evaluatie' : 'Actieve evaluatie'}</span>
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