function wireEvaluationForm() {
  const container = document.getElementById('eval-competencies');

  if (!currentInternship) {
    content.innerHTML = `
      <div class="panel card reveal">
        <h2>Geen stage geselecteerd</h2>
        <p>Selecteer eerst een stage via het navigatiemenu links.</p>
      </div>
    `;
    return;
  }

  // Haal bestaande evaluaties voor deze stage op
  InternshipsAPI.getEvaluations(currentInternship.id).then(evaluations => {
    currentEvaluations = evaluations;

    // Gebruik bestaande concept-evaluatie indien aanwezig, anders aanmaken bij opslaan
    const existingEval = evaluations.find(e => !e.finalized);

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
            <textarea class="student-desc-input" rows="2" placeholder="Student beschrijving..." ${existingEval?.finalized ? 'disabled' : ''}>${rule?.student_description || ''}</textarea>
          </div>
        `;
      }).join('');
    }
  }).catch(err => {
    console.error('Failed to load evaluations:', err);
  });

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
          eval_type: evalType
        });
        currentEvaluations.push(evaluation);
      }

      // Stap 2: Werk elke regel bij met score, feedback en omschrijving
      const rows = container.querySelectorAll('.eval-row');
      for (const row of rows) {
        const compId = parseInt(row.dataset.compId);
        const score = parseInt(row.querySelector('.score-select')?.value);
        const feedback = row.querySelector('.feedback-input')?.value || null;
        const studentDesc = row.querySelector('.student-desc-input')?.value || null;

        // Vind regel-ID voor deze competentie
        const rule = evaluation.rules?.find(r => r.competency_id === compId);
        if (rule) {
          await EvaluationRulesAPI.update(evaluation.id, rule.id, {
            score,
            evaluator_feedback: feedback,
            student_description: studentDesc
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
    if (!confirm('Evaluatie definitief afsluiten? Dit kan niet ongedaan gemaakt worden.')) return;

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
      await apiRequest(`/evaluations/${evaluation.id}/finalize`, { method: 'POST' });
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

  container.innerHTML = '<p>Laden...</p>';

  try {
    const report = await InternshipsAPI.getFinalReport(currentInternship.id);
    if (!report || !report.rules || report.rules.length === 0) {
      container.innerHTML = '<p>Geen eindoverzicht beschikbaar. Finaliseer eerst een evaluatie.</p>';
      return;
    }

    const rows = formatReportRows(report.rules);

    container.innerHTML = `
      <div class="panel card" style="margin-top: 1rem;">
        <p><strong>Student:</strong> ${currentInternship.student_name || 'Onbekend'}</p>
        <p><strong>Bedrijf:</strong> ${currentInternship.company_name || 'Onbekend'}</p>
        <p><strong>Periode:</strong> ${formatDate(currentInternship.start_date)} – ${formatDate(currentInternship.end_date)}</p>
        <p><strong>Gewogen eindscore:</strong> <span class="score-highlight">${report.weighted_average_score !== null ? report.weighted_average_score.toFixed(2) : '-'} / 5</span></p>
      </div>
      <table style="margin-top: 1rem;">
        <thead>
          <tr><th>Competentie</th><th>Gewicht</th><th>Score</th><th>Student beschrijving</th><th>Feedback</th></tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
      <button class="btn" style="margin-top: 1rem;" onclick="window.print()">Afdrukken</button>
    `;
  } catch (error) {
    console.error('Failed to load final report:', error);
    container.innerHTML = '<p class="error">Kon eindoverzicht niet laden.</p>';
  }
}

// ============================================
// Docent & Mentor logboekweergaven
// ============================================
function renderTeacherLogbooks() {
  const tbody = document.querySelector('#teacher-logbooks-table tbody');
  if (!tbody) return;

  if (!currentInternship) {
    tbody.innerHTML = '<tr><td colspan="5">Selecteer een stage via het navigatiemenu.</td></tr>';
    return;
  }

  if (currentLogbooks.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5">Geen logboeken gevonden voor deze stage.</td></tr>';
    return;
  }

  tbody.innerHTML = currentLogbooks.map(lb => `
    <tr>
      <td>${lb.week_number}</td>
      <td>${lb.tasks || '-'}</td>
      <td>${lb.reflection || '-'}</td>
      <td><span class="status-pill ${getStatusClass(lb.status)}">${lb.status === 'submitted' ? 'Ingediend' : 'Concept'}</span></td>
      <td>${lb.mentor_validated ? '✓ Gevalideerd' : 'In afwachting'}</td>
    </tr>
  `).join('');

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
