function wireEvaluationForm() {
  const container = document.getElementById('eval-competencies');

  if (!currentInternship) {
    content.innerHTML = `
      <div class="panel card">
        <h2>Geen stage geselecteerd</h2>
        <p>Selecteer eerst een stage via het navigatiemenu links.</p>
      </div>
    `;
    return;
  }

  // Gebruik bestaande concept-evaluatie indien aanwezig, anders aanmaken bij opslaan
  // currentEvaluations is al geladen door renderView()
  const existingEval = currentEvaluations.find(e => !e.finalized);

    // Populate general comments if editing existing evaluation
    const commentsArea = document.getElementById('eval-comments');
    if (commentsArea && existingEval) {
      commentsArea.value = existingEval.comments || '';
    }

    if (container && currentCompetencies.length > 0) {
      container.innerHTML = currentCompetencies.map(comp => {
        // Zoek regel voor deze competentie als evaluatie bestaat
        let rule = null;
        if (existingEval && existingEval.rules) {
          rule = existingEval.rules.find(r => r.competency_id === comp.id);
        }
        return `
          <div class="eval-row" data-comp-id="${comp.id}">
            <label>${comp.name} (${comp.weight}%)</label>
            <div class="score-inputs">
              <select class="score-select" data-comp="${comp.id}" ${existingEval?.finalized ? 'disabled' : ''}>
                <option value="1" ${rule?.score == 1 ? 'selected' : ''}>1 - Onvoldoende</option>
                <option value="2" ${rule?.score == 2 ? 'selected' : ''}>2 - Matig</option>
                <option value="3" ${rule?.score == 3 ? 'selected' : ''}>3 - Voldoende</option>
                <option value="4" ${rule?.score == 4 ? 'selected' : ''}>4 - Goed</option>
                <option value="5" ${rule?.score == 5 ? 'selected' : ''}>5 - Uitstekend</option>
              </select>
              <input type="text" class="feedback-input" placeholder="Feedback..." value="${rule?.evaluator_feedback || ''}" ${existingEval?.finalized ? 'disabled' : ''} />
            </div>
            <textarea class="student-desc-input" rows="2" placeholder="Zelfreflectie van student (alleen lezen)..." readonly>${rule?.student_description || ''}</textarea>
          </div>
        `;
      }).join('');
    }

  const evalForm = document.getElementById('eval-form');
  const finalizeBtn = document.getElementById('finalize-eval');

  // Scores opslaan (maakt evaluatie aan indien nodig)
  evalForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = evalForm.querySelector('button[type="submit"]');
    const evalType = document.getElementById('eval-type')?.value || 'tussentijds';

    if (!currentInternship) {
      showToast('Geen stage geselecteerd', 'error');
      return;
    }

    showLoading(submitBtn, 'Opslaan...');

    try {
      // Stap 1: Evaluatie aanmaken (indien geen concept)
      let evaluation = currentEvaluations.find(e => !e.finalized && e.eval_type === evalType);
      if (!evaluation) {
        evaluation = await InternshipsAPI.createEvaluation(currentInternship.id, {
          eval_type: evalType,
          comments: document.getElementById('eval-comments')?.value || null
        });
        currentEvaluations.push(evaluation);
      }

      // Stap 2: Update general comments
      const comments = document.getElementById('eval-comments')?.value || null;
      if (comments !== null && comments !== (evaluation.comments || '')) {
        await EvaluationsAPI.update(evaluation.id, { comments });
      }

      // Stap 3: Werk elke regel bij met score, feedback en omschrijving
      const rows = container.querySelectorAll('.eval-row');
      for (const row of rows) {
        const compId = parseInt(row.dataset.compId);
        const score = parseInt(row.querySelector('.score-select')?.value);
        const feedback = row.querySelector('.feedback-input')?.value || null;
        // Vind regel-ID voor deze competentie
        const rule = evaluation.rules?.find(r => r.competency_id === compId);
        if (rule) {
          await EvaluationRulesAPI.update(evaluation.id, rule.id, {
            score,
            evaluator_feedback: feedback
          });
        }
      }

      hideLoading(submitBtn);
      showToast('Evaluatie opgeslagen!', 'success');
    } catch (error) {
      hideLoading(submitBtn);
      showToast(error.message, 'error');
    }
  });

  // Evaluatie finaliseren
  finalizeBtn?.addEventListener('click', async () => {
    try {
      await showConfirmModal({
        title: 'Evaluatie afsluiten',
        message: 'Evaluatie definitief afsluiten? Dit kan niet ongedaan gemaakt worden.',
        okText: 'Afsluiten',
        okClass: 'danger'
      });
    } catch {
      return;
    }

    if (!currentInternship) {
      showToast('Geen stage geselecteerd', 'error');
      return;
    }

    // Eerst huidige scores opslaan
    const submitBtn = evalForm.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.click();

    // Daarna evaluatie zoeken en finaliseren
    const evalType = document.getElementById('eval-type')?.value || 'tussentijds';
    const evaluation = currentEvaluations.find(e => !e.finalized && e.eval_type === evalType);

    if (!evaluation) {
      showToast('Geen evaluatie gevonden om af te sluiten', 'error');
      return;
    }

    showLoading(finalizeBtn, 'Bezig...');

    try {
      // Backend finalize endpoint: POST /evaluations/{id}/finalize
      await apiRequest(`/internships/evaluations/${evaluation.id}/finalize`, { method: 'POST' });
      hideLoading(finalizeBtn);
      showToast('Evaluatie definitief afgesloten!', 'success');
    } catch (error) {
      hideLoading(finalizeBtn);
      showToast(error.message, 'error');
    }
  });
}

async function renderTeacherFinalReport() {
  const container = document.getElementById('final-report-content');
  if (!container) return;

  if (!currentInternship) {
    container.innerHTML = '<p>Selecteer een stage via het navigatiemenu.</p>';
    return;
  }

  // Bereken eindoverzicht lokaal vanuit currentEvaluations (geen extra API call)
  const finalEval = currentEvaluations.find(e => e.eval_type === 'final' && e.finalized);
  if (!finalEval || !finalEval.rules || finalEval.rules.length === 0) {
    container.innerHTML = '<p>Geen eindoverzicht beschikbaar. Finaliseer eerst een evaluatie.</p>';
    return;
  }

  const rows = formatReportRows(finalEval.rules);
  let weightedScore = null;
  const scoredRules = finalEval.rules.filter(r => r.score != null && r.competency?.weight != null);
  if (scoredRules.length > 0) {
    const totalWeight = scoredRules.reduce((sum, r) => sum + r.competency.weight, 0);
    const weightedSum = scoredRules.reduce((sum, r) => sum + (r.score * r.competency.weight), 0);
    weightedScore = totalWeight > 0 ? (weightedSum / totalWeight / 20).toFixed(2) : '-';
  }

  container.innerHTML = `
    <div class="panel card" style="margin-top: 1rem;">
      <p><strong>Student:</strong> ${escapeHtml(currentInternship.student?.first_name || '')} ${escapeHtml(currentInternship.student?.last_name || 'Onbekend')}</p>
      <p><strong>Bedrijf:</strong> ${escapeHtml(currentInternship.company?.name || 'Onbekend')}</p>
      <p><strong>Periode:</strong> ${formatDate(currentInternship.start_date)} – ${formatDate(currentInternship.end_date)}</p>
      <p><strong>Gewogen eindscore:</strong> <span class="score-highlight">${weightedScore !== null ? weightedScore : '-'} / 5</span></p>
    </div>
    <table style="margin-top: 1rem;">
      <thead>
        <tr><th>Competentie</th><th>Gewicht</th><th>Score</th><th>Student beschrijving</th><th>Feedback</th></tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
    <button class="btn" style="margin-top: 1rem;" onclick="window.print()">${iconHtml('file-text', 16)} Afdrukken</button>
  `;
}

// ============================================
// Docent & Mentor logboekweergaven
// ============================================
async function renderTeacherLogbooks() {
  const tbody = document.querySelector('#teacher-logbooks-table tbody');
  if (!tbody) return;

  if (!currentInternship) {
    tbody.innerHTML = '<tr><td colspan="5">Selecteer een stage via het navigatiemenu.</td></tr>';
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
        </tr>
      `);
    } else {
      rows.push(`
        <tr>
          <td>${w}</td>
          <td>${escapeHtml(lb.tasks || '-')}</td>
          <td>${escapeHtml(lb.reflection || '-')}</td>
          <td><span class="status-pill ${getStatusClass(lb.status)}">${lb.status === 'submitted' ? 'Ingediend' : 'Concept'}</span></td>
          <td>${lb.mentor_validated ? `${iconHtml('check-circle', 14)} Gevalideerd` : 'In afwachting'}</td>
        </tr>
      `);
    }
  }
  tbody.innerHTML = rows.join('') || '<tr><td colspan="5">Geen logboekweken gevonden</td></tr>';

  // Feedbackknop verbinden
  const sendBtn = document.getElementById('teacher-send-feedback');
  sendBtn?.addEventListener('click', async () => {
    const msg = document.getElementById('teacher-feedback-msg')?.value;
    if (!msg) {
      showToast('Geen feedback ingevuld', 'warning');
      return;
    }
    if (!currentInternship) {
      showToast('Geen stage geselecteerd', 'error');
      return;
    }
    try {
      await InternshipsAPI.createFeedback(currentInternship.id, {
        message: msg,
        to_user_id: currentInternship.student_id
      });
      showToast('Feedback verstuurd!', 'success');
      document.getElementById('teacher-feedback-msg').value = '';
    } catch (error) {
      showToast(error.message, 'error');
    }
  });
}
