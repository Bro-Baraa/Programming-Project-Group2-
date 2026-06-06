// ============================================
// Studentweergaven
// ============================================

async function renderStudentDashboard() {
    if (!currentInternship) {
      content.innerHTML = `
        <div class="panel card">
          <h2>Geen stage gevonden</h2>
          <p>Je hebt nog geen stage ingediend.</p>
          <a href="?view=voorstel" class="btn">${iconHtml('plus', 16)} Stagevoorstel indienen</a>
        </div>
      `;
      return;
    }

    const hero = document.querySelector('.hero');
    if (hero) {
      const companyName = currentInternship.company?.name || 'Onbekend';
      const startDate = formatDate(currentInternship.start_date);
      const endDate = formatDate(currentInternship.end_date);
      const agreementStatus = currentInternship.agreement_status || 'Niet Ingediend';
      let agreementLabel;
      switch (agreementStatus) {
        case 'Niet Ingediend': agreementLabel = `${iconHtml('x-circle', 14)} Nog niet`; break;
        case 'Onvolledig': agreementLabel = `${iconHtml('alert-circle', 14)} Onvolledig`; break;
        default: agreementLabel = `${iconHtml('check-circle', 14)} ${agreementStatus}`;
      }
      const teacherName = currentInternship.teacher
        ? `${currentInternship.teacher.first_name} ${currentInternship.teacher.last_name}`
        : 'Nog niet toegewezen';
      const mentorName = currentInternship.mentor
        ? `${currentInternship.mentor.first_name} ${currentInternship.mentor.last_name}`
        : 'Nog niet toegewezen';

      hero.innerHTML = `
        <h2>Mijn Stage</h2>
        <p><strong>Bedrijf:</strong> ${companyName}</p>
        <p><strong>Periode:</strong> ${startDate} - ${endDate}</p>
        <p><strong>Status:</strong> <span class="status-pill ${getStatusClass(currentInternship.status)}">${currentInternship.status}</span></p>
        <p><strong>Overeenkomst:</strong> ${agreementLabel}</p>
        <p><strong>Docent:</strong> ${teacherName}</p>
        <p><strong>Mentor:</strong> ${mentorName}</p>
        <div style="margin-top: 1rem;">
          <a href="?view=voorstel" class="btn">${iconHtml('plus', 16)} Nieuw stagevoorstel</a>
        </div>
      `;
    }

    // Logboeken tabel bijwerken - toon alle weken inclusief ontbrekende (US-08)
    const tbody = document.querySelector('table tbody');
    if (tbody && currentInternship) {
      try {
        const weeks = await InternshipsAPI.getLogbookWeeks(currentInternship.id);
        const rows = weeks.map(w => {
          if (w.status === 'missing') {
            return `
              <tr class="missing-row">
                <td>${escapeHtml(w.week_number)}</td>
                <td><span class="status-pill status-warn">Ontbrekend</span></td>
                <td>-</td>
                <td>-</td>
              </tr>
            `;
          }
          return `
            <tr>
              <td>${escapeHtml(w.week_number)}</td>
              <td>${w.status === 'submitted' ? 'Ingediend' : 'Concept'}</td>
              <td>${w.mentor_validated ? 'Goedgekeurd' : (w.status === 'submitted' ? 'In afwachting' : '-')}</td>
              <td>${w.mentor_feedback ? escapeHtml(w.mentor_feedback) : '<span class="hint">-</span>'}</td>
            </tr>
          `;
        });
        tbody.innerHTML = rows.join('') || '<tr><td colspan="4">Geen logboekweken gevonden</td></tr>';
      } catch (error) {
        console.error('Failed to load week overview:', error);
        // Fallback to raw logbook list
        tbody.innerHTML = currentLogbooks.map(lb => `
          <tr>
            <td>${escapeHtml(lb.week_number)}</td>
            <td>${lb.status === 'submitted' ? 'Ingediend' : 'Concept'}</td>
            <td>${lb.mentor_validated ? 'Goedgekeurd' : (lb.status === 'submitted' ? 'In afwachting' : '-')}</td>
            <td>${lb.mentor_feedback ? escapeHtml(lb.mentor_feedback) : '<span class="hint">-</span>'}</td>
          </tr>
        `).join('') || '<tr><td colspan="4">Geen logboeken gevonden</td></tr>';
      }
    }

    // Competentie Progressie bijwerken
    const competencyPanel = Array.from(document.querySelectorAll('.panel.card')).find(
      p => p.querySelector('h2')?.textContent === 'Competentie Progressie'
    );
    if (competencyPanel) {
      // Only use finalized evaluations
      const finalizedEvals = currentEvaluations.filter(ev => ev.finalized);
      const competencyScores = {};

      for (const ev of finalizedEvals) {
        for (const rule of (ev.rules || [])) {
          const name = rule.competency?.name || 'Onbekend';
          if (rule.score != null) {
            const entry = competencyScores[name] || (competencyScores[name] = { total: 0, count: 0 });
            entry.total += rule.score;
            entry.count += 1;
          }
        }
      }

      const competencyItems = Object.entries(competencyScores).map(([name, data]) => {
        const avg = data.total / data.count;
        const pct = Math.round((avg / 5) * 100);
        return { name, pct, avg: avg.toFixed(1) };
      });

      if (competencyItems.length > 0) {
        competencyPanel.innerHTML = `
          <h2>Competentie Progressie</h2>
          ${competencyItems.map(c => `
            <div class="meter">
              <span style="width: ${c.pct}%">${escapeHtml(c.name)} ${c.pct}% (${c.avg}/5)</span>
            </div>
          `).join('')}
        `;
      } else {
        competencyPanel.innerHTML = `
          <h2>Competentie Progressie</h2>
          <p class="hint">Nog geen evaluaties beschikbaar.</p>
        `;
      }
    }

    // Feedback sectie bijwerken
    const feedbackDiv = document.getElementById('student-feedback');
    if (feedbackDiv) {
      if (currentFeedback.length > 0) {
        feedbackDiv.innerHTML = currentFeedback.map(fb => `
          <div style="margin-bottom: 0.75rem; padding: 0.75rem; background: rgba(0,121,140,0.08); border-radius: 8px;">
            <p style="margin: 0 0 0.25rem 0;"><strong>${escapeHtml(fb.from_user?.first_name || 'Onbekend')} ${escapeHtml(fb.from_user?.last_name || '')}</strong> (${formatDate(fb.created_at)})</p>
            <p style="margin: 0; color: var(--ink-soft);">${escapeHtml(fb.message)}</p>
          </div>
        `).join('');
      } else {
        feedbackDiv.innerHTML = '<p class="hint">Je hebt nog geen feedback ontvangen.</p>';
      }
    }
  }

  function wireProposalForm() {
    const container = content.querySelector('.panel.card');
    if (!container) return;

    // ── No internship yet: show the original creation form ──
    if (!currentInternship) {
      const form = document.getElementById('proposal-form');
      if (!form) return;

      // teacher en mentor dropdowns
      const teacherSelect = document.getElementById('teacher-select');
      const mentorSelect = document.getElementById('mentor-select');

      if (teacherSelect) {
        teacherSelect.innerHTML = '<option value="">Laden...</option>';
        teacherSelect.disabled = true;
        UsersAPI.list('teacher').then(teachers => {
          teacherSelect.innerHTML = '<option value="">-- Kies een docent --</option>';
          teachers.forEach(t => {
            const option = document.createElement('option');
            option.value = t.id;
            option.textContent = `${t.first_name} ${t.last_name} (${t.email})`;
            teacherSelect.appendChild(option);
          });
          teacherSelect.disabled = false;
        }).catch(() => {
          teacherSelect.innerHTML = '<option value="">Kon docenten niet laden</option>';
        });
      }

      if (mentorSelect) {
        mentorSelect.innerHTML = '<option value="">Laden...</option>';
        mentorSelect.disabled = true;
        UsersAPI.list('mentor').then(mentors => {
          mentorSelect.innerHTML = '<option value="">-- Kies een mentor --</option>';
          mentors.forEach(m => {
            const option = document.createElement('option');
            option.value = m.id;
            option.textContent = `${m.first_name} ${m.last_name} (${m.email})`;
            mentorSelect.appendChild(option);
          });
          mentorSelect.disabled = false;
        }).catch(() => {
          mentorSelect.innerHTML = '<option value="">Kon mentors niet laden</option>';
        });
      }

      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = form.querySelector('button[type="submit"]');

        const data = {
          company_name: document.getElementById('company-name').value,
          company_address: document.getElementById('company-address').value || null,
          company_sector: document.getElementById('company-sector').value || null,
          contact_person: document.getElementById('contact-person').value,
          contact_email: document.getElementById('contact-email').value,
          start_date: document.getElementById('start-date').value,
          end_date: document.getElementById('end-date').value,
          description: document.getElementById('assignment-desc').value,
        };

        const teacherId = parseInt(document.getElementById('teacher-select')?.value);
        const mentorId = parseInt(document.getElementById('mentor-select')?.value);
        if (teacherId) data.teacher_id = teacherId;
        if (mentorId) data.mentor_id = mentorId;

        showLoading(submitBtn, 'Indienen...');

        try {
          await InternshipsAPI.create(data);
          hideLoading(submitBtn);
          showToast('Stagevoorstel succesvol ingediend!', 'success');
          setTimeout(() => window.location.href = '?view=dashboard', 1000);
        } catch (error) {
          hideLoading(submitBtn);
          showToast(error.message, 'error');
        }
      });
      return;
    }

    // ── Student already has an internship: show proposal details ──
    const proposal = currentInternship.proposal;
    const company = currentInternship.company || {};
    const isChangesRequired = currentInternship.status === 'Aanpassingen Vereist';
    const isIngediend = currentInternship.status === 'Ingediend';
    const feedback = proposal?.feedback;
    const revisionCount = proposal?.revision_count || 0;
    const resubmittedAt = proposal?.resubmitted_at;
    const version = proposal?.version || 1;
    const revisedAt = proposal?.revised_at;

    let proposalStatusText;
    switch (currentInternship.status) {
      case 'In Beoordeling': proposalStatusText = 'in beoordeling'; break;
      case 'Afgekeurd': proposalStatusText = 'afgekeurd'; break;
      default: proposalStatusText = 'goedgekeurd';
    }

    container.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:0.5rem;">
        <h2 style="margin:0;">Mijn Stagevoorstel</h2>
        <button id="btn-new-proposal" class="btn">${iconHtml('plus', 16)} Nieuw stagevoorstel</button>
      </div>

      <div class="proposal-summary">
        <p><strong>Status:</strong> <span class="status-pill ${getStatusClass(currentInternship.status)}">${currentInternship.status}</span></p>
        <p><strong>Bedrijf:</strong> ${escapeHtml(company.name || 'Onbekend')}</p>
        ${company.address ? `<p><strong>Adres:</strong> ${escapeHtml(company.address)}</p>` : ''}
        ${company.sector ? `<p><strong>Sector:</strong> ${escapeHtml(company.sector)}</p>` : ''}
        <p><strong>Contactpersoon:</strong> ${escapeHtml(company.contact_person || 'Onbekend')}</p>
        <p><strong>E-mail:</strong> ${escapeHtml(company.contact_email || 'Onbekend')}</p>
        <p><strong>Periode:</strong> ${formatDate(currentInternship.start_date)} - ${formatDate(currentInternship.end_date)}</p>
        <p><strong>Versie:</strong> ${version}</p>
        ${revisionCount > 0 ? `<p><strong>Aantal herzieningen:</strong> ${revisionCount}</p>` : ''}
        ${revisedAt ? `<p><strong>Laatst bewerkt:</strong> ${formatDate(revisedAt)}</p>` : ''}
        ${resubmittedAt ? `<p><strong>Laatst herzien:</strong> ${formatDate(resubmittedAt)}</p>` : ''}
        <div class="proposal-description">
          <p><strong>Omschrijving opdracht:</strong></p>
          <div style="background: rgba(0,0,0,0.03); padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem;">
            ${escapeHtml(proposal?.description || 'Geen omschrijving beschikbaar.')}
          </div>
        </div>
      </div>

      ${feedback ? `
        <div class="info-message warning">
          <p><strong>Feedback van de commissie:</strong></p>
          <p>${escapeHtml(feedback)}</p>
        </div>
      ` : ''}

      ${isIngediend ? `
        <div class="btn-group" style="margin-top: 1rem;">
          <button id="btn-edit-proposal" class="btn">${iconHtml('edit', 14)} Wijzigen</button>
          <button id="btn-withdraw-proposal" class="btn danger">${iconHtml('trash', 14)} Intrekken</button>
        </div>
        <div id="edit-section" style="display: none; margin-top: 1.5rem;">
          <h3>Voorstel wijzigen</h3>
          <p class="hint">Pas je voorstel aan voor de commissie het beoordeelt.</p>
          <form id="edit-form">
            <div class="row full">
              <label>Bedrijfsnaam</label>
              <input type="text" id="edit-company-name" value="${escapeHtml(company.name || '')}" />
            </div>
            <div class="row full">
              <label>Adres</label>
              <input type="text" id="edit-company-address" value="${escapeHtml(company.address || '')}" />
            </div>
            <div class="row full">
              <label>Sector</label>
              <input type="text" id="edit-company-sector" value="${escapeHtml(company.sector || '')}" />
            </div>
            <div class="row full">
              <label>Contactpersoon</label>
              <input type="text" id="edit-contact-person" value="${escapeHtml(company.contact_person || '')}" />
            </div>
            <div class="row full">
              <label>E-mail contactpersoon</label>
              <input type="email" id="edit-contact-email" value="${escapeHtml(company.contact_email || '')}" />
            </div>
            <div class="row full">
              <label>Stageperiode</label>
              <div class="date-range">
                <div class="input-with-icon">
                  ${iconHtml('calendar', 16)}
                  <input type="date" id="edit-start-date" value="${currentInternship.start_date || ''}" />
                </div>
                <span>tot</span>
                <div class="input-with-icon">
                  ${iconHtml('calendar', 16)}
                  <input type="date" id="edit-end-date" value="${currentInternship.end_date || ''}" />
                </div>
              </div>
            </div>
            <div class="row full">
              <label>Omschrijving opdracht * (min. 20 karakters)</label>
              <textarea id="edit-description" rows="4" required minlength="20">${escapeHtml(proposal?.description || '')}</textarea>
            </div>
            <div class="btn-group">
              <button type="submit" class="btn">${iconHtml('check-circle', 16)} Wijzigingen opslaan</button>
              <button type="button" id="btn-cancel-edit" class="btn secondary">${iconHtml('x-circle', 14)} Annuleren</button>
            </div>
          </form>
        </div>
      ` : ''}

      ${isChangesRequired ? `
        <div class="resubmit-section" style="margin-top: 1.5rem;">
          <h3>Opnieuw indienen</h3>
          <p class="hint">Pas je voorstel aan op basis van de feedback en dien opnieuw in.</p>
          <form id="resubmit-form">
            <div class="row full">
              <label>Bedrijfsnaam</label>
              <input type="text" id="resubmit-company-name" value="${escapeHtml(company.name || '')}" />
            </div>
            <div class="row full">
              <label>Adres</label>
              <input type="text" id="resubmit-company-address" value="${escapeHtml(company.address || '')}" />
            </div>
            <div class="row full">
              <label>Sector</label>
              <input type="text" id="resubmit-company-sector" value="${escapeHtml(company.sector || '')}" />
            </div>
            <div class="row full">
              <label>Contactpersoon</label>
              <input type="text" id="resubmit-contact-person" value="${escapeHtml(company.contact_person || '')}" />
            </div>
            <div class="row full">
              <label>E-mail contactpersoon</label>
              <input type="email" id="resubmit-contact-email" value="${escapeHtml(company.contact_email || '')}" />
            </div>
            <div class="row full">
              <label>Stageperiode</label>
              <div class="date-range">
                <div class="input-with-icon">
                  ${iconHtml('calendar', 16)}
                  <input type="date" id="resubmit-start-date" value="${currentInternship.start_date || ''}" />
                </div>
                <span>tot</span>
                <div class="input-with-icon">
                  ${iconHtml('calendar', 16)}
                  <input type="date" id="resubmit-end-date" value="${currentInternship.end_date || ''}" />
                </div>
              </div>
            </div>
            <div class="row full">
              <label>Omschrijving opdracht * (min. 20 karakters)</label>
              <textarea id="resubmit-description" rows="4" required minlength="20">${escapeHtml(proposal?.description || '')}</textarea>
            </div>
            <button type="submit" class="btn">${iconHtml('check-circle', 16)} Voorstel Opnieuw Indienen</button>
          </form>
        </div>
      ` : ''}

      ${!isIngediend && !isChangesRequired ? `
        <div class="info-message" style="margin-top: 1rem;">
          <p>Je voorstel is ${proposalStatusText}. Je kunt het op dit moment niet meer wijzigen.</p>
        </div>
      ` : ''}

      ${allInternships.length > 1 ? `
        <div style="margin-top: 2rem;">
          <h3>Mijn andere stagevoorstellen</h3>
          ${allInternships.filter(i => i.id !== currentInternship.id).map(i => {
            const company = i.company || {};
            return `
              <div class="panel card" style="margin-top: 0.75rem;">
                <p><strong>Bedrijf:</strong> ${escapeHtml(company.name || 'Onbekend')}</p>
                <p><strong>Status:</strong> <span class="status-pill ${getStatusClass(i.status)}">${i.status}</span></p>
                <p><strong>Periode:</strong> ${formatDate(i.start_date)} - ${formatDate(i.end_date)}</p>
                <p><strong>Opdracht:</strong> ${escapeHtml(i.proposal?.description?.substring(0, 100) || 'Geen omschrijving')}${i.proposal?.description?.length > 100 ? '...' : ''}</p>
                <a href="?view=voorstel&internship=${i.id}" class="btn small">${iconHtml('eye', 14)} Bekijken</a>
              </div>
            `;
          }).join('')}
        </div>
      ` : ''}
    `;

    // Wire edit form
    const editBtn = document.getElementById('btn-edit-proposal');
    const editSection = document.getElementById('edit-section');
    const editForm = document.getElementById('edit-form');
    const cancelEditBtn = document.getElementById('btn-cancel-edit');

    editBtn?.addEventListener('click', () => {
      if (editSection) editSection.style.display = 'block';
      editBtn.style.display = 'none';
      const withdrawBtn = document.getElementById('btn-withdraw-proposal');
      if (withdrawBtn) withdrawBtn.style.display = 'none';
    });

    cancelEditBtn?.addEventListener('click', () => {
      if (editSection) editSection.style.display = 'none';
      editBtn.style.display = 'inline-block';
      const withdrawBtn = document.getElementById('btn-withdraw-proposal');
      if (withdrawBtn) withdrawBtn.style.display = 'inline-block';
    });

    editForm?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = editForm.querySelector('button[type="submit"]');
      const description = document.getElementById('edit-description').value;

      if (!description || description.length < 20) {
        showToast('Omschrijving moet minstens 20 karakters bevatten', 'error');
        return;
      }

      showLoading(submitBtn, 'Opslaan...');

      try {
        await ProposalsAPI.edit(currentInternship.id, {
          description,
          company_name: document.getElementById('edit-company-name').value || undefined,
          company_address: document.getElementById('edit-company-address').value || undefined,
          company_sector: document.getElementById('edit-company-sector').value || undefined,
          contact_person: document.getElementById('edit-contact-person').value || undefined,
          contact_email: document.getElementById('edit-contact-email').value || undefined,
          start_date: document.getElementById('edit-start-date').value || undefined,
          end_date: document.getElementById('edit-end-date').value || undefined,
        });
        hideLoading(submitBtn);
        showToast('Wijzigingen opgeslagen!', 'success');
        await refreshInternshipData();
        renderView();
      } catch (error) {
        hideLoading(submitBtn);
        showToast(error.message, 'error');
      }
    });

    // Wire withdraw button
    document.getElementById('btn-withdraw-proposal')?.addEventListener('click', async () => {
      try {
        await showConfirmModal({
          title: 'Voorstel intrekken',
          message: 'Weet je zeker dat je je stagevoorstel wilt intrekken? Dit kan niet ongedaan gemaakt worden.',
          okText: 'Intrekken',
          okClass: 'danger'
        });
        await ProposalsAPI.withdraw(currentInternship.id);
        showToast('Voorstel succesvol ingetrokken', 'success');
        await refreshInternshipData();
        renderView();
      } catch {
        // User cancelled — do nothing
      }
    });

    // Wire resubmit form
    const resubmitForm = document.getElementById('resubmit-form');
    resubmitForm?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const submitBtn = resubmitForm.querySelector('button[type="submit"]');
      const newDescription = document.getElementById('resubmit-description').value;

      if (!newDescription || newDescription.length < 20) {
        showToast('Omschrijving moet minstens 20 karakters bevatten', 'error');
        return;
      }

      showLoading(submitBtn, 'Indienen...');

      try {
        await ProposalsAPI.resubmit(currentInternship.id, newDescription, {
          company_name: document.getElementById('resubmit-company-name').value || undefined,
          company_address: document.getElementById('resubmit-company-address').value || undefined,
          company_sector: document.getElementById('resubmit-company-sector').value || undefined,
          contact_person: document.getElementById('resubmit-contact-person').value || undefined,
          contact_email: document.getElementById('resubmit-contact-email').value || undefined,
          start_date: document.getElementById('resubmit-start-date').value || undefined,
          end_date: document.getElementById('resubmit-end-date').value || undefined,
        });
        hideLoading(submitBtn);
        showToast('Voorstel succesvol opnieuw ingediend!', 'success');
        await refreshInternshipData();
        renderView();
      } catch (error) {
        hideLoading(submitBtn);
        showToast(error.message, 'error');
      }
    });

    // Wire new proposal button
    document.getElementById('btn-new-proposal')?.addEventListener('click', () => {
      container.innerHTML = `
        <h2>Nieuw stagevoorstel indienen</h2>
        <form id="new-proposal-form">
          <div class="row full">
            <label>Bedrijfsnaam *</label>
            <input type="text" id="new-company-name" placeholder="Naam van het bedrijf" required />
          </div>
          <div class="row full">
            <label>Adres</label>
            <input type="text" id="new-company-address" placeholder="Straat en nummer" />
          </div>
          <div class="row full">
            <label>Sector</label>
            <input type="text" id="new-company-sector" placeholder="Bijv. IT, Data & Analytics..." />
          </div>
          <div class="row full">
            <label>Contactpersoon *</label>
            <input type="text" id="new-contact-person" placeholder="Naam contactpersoon" required />
          </div>
          <div class="row full">
            <label>E-mail contactpersoon *</label>
            <input type="email" id="new-contact-email" placeholder="email@bedrijf.be" required />
          </div>
          <div class="row full">
            <label>Stageperiode *</label>
            <div class="date-range">
              <div class="input-with-icon">
                ${iconHtml('calendar', 16)}
                <input type="date" id="new-start-date" required />
              </div>
              <span>tot</span>
              <div class="input-with-icon">
                ${iconHtml('calendar', 16)}
                <input type="date" id="new-end-date" required />
              </div>
            </div>
          </div>
          <div class="row full">
            <label>Omschrijving opdracht * (min. 20 karakters)</label>
            <textarea id="new-assignment-desc" rows="4" placeholder="Beschrijf de stageopdracht in detail..." required minlength="20"></textarea>
          </div>
          <div class="row full">
            <label>Docent (optioneel)</label>
            <select id="new-teacher-select">
              <option value="">-- Kies een docent --</option>
            </select>
          </div>
          <div class="row full">
            <label>Mentor (optioneel)</label>
            <select id="new-mentor-select">
              <option value="">-- Kies een mentor --</option>
            </select>
          </div>
          <button type="submit" class="btn">${iconHtml('check-circle', 16)} Voorstel Indienen</button>
          <button type="button" id="btn-cancel-new-proposal" class="btn secondary">${iconHtml('x-circle', 14)} Annuleren</button>
        </form>
      `;

      const teacherSelect = document.getElementById('new-teacher-select');
      const mentorSelect = document.getElementById('new-mentor-select');

      if (teacherSelect) {
        teacherSelect.innerHTML = '<option value="">Laden...</option>';
        teacherSelect.disabled = true;
        UsersAPI.list('teacher').then(teachers => {
          teacherSelect.innerHTML = '<option value="">-- Kies een docent --</option>';
          teachers.forEach(t => {
            const option = document.createElement('option');
            option.value = t.id;
            option.textContent = `${t.first_name} ${t.last_name} (${t.email})`;
            teacherSelect.appendChild(option);
          });
          teacherSelect.disabled = false;
        }).catch(() => {
          teacherSelect.innerHTML = '<option value="">Kon docenten niet laden</option>';
        });
      }

      if (mentorSelect) {
        mentorSelect.innerHTML = '<option value="">Laden...</option>';
        mentorSelect.disabled = true;
        UsersAPI.list('mentor').then(mentors => {
          mentorSelect.innerHTML = '<option value="">-- Kies een mentor --</option>';
          mentors.forEach(m => {
            const option = document.createElement('option');
            option.value = m.id;
            option.textContent = `${m.first_name} ${m.last_name} (${m.email})`;
            mentorSelect.appendChild(option);
          });
          mentorSelect.disabled = false;
        }).catch(() => {
          mentorSelect.innerHTML = '<option value="">Kon mentors niet laden</option>';
        });
      }

      document.getElementById('btn-cancel-new-proposal')?.addEventListener('click', () => {
        renderView();
      });

      const newForm = document.getElementById('new-proposal-form');
      newForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = newForm.querySelector('button[type="submit"]');

        const data = {
          company_name: document.getElementById('new-company-name').value,
          company_address: document.getElementById('new-company-address').value || null,
          company_sector: document.getElementById('new-company-sector').value || null,
          contact_person: document.getElementById('new-contact-person').value,
          contact_email: document.getElementById('new-contact-email').value,
          start_date: document.getElementById('new-start-date').value,
          end_date: document.getElementById('new-end-date').value,
          description: document.getElementById('new-assignment-desc').value,
        };

        const teacherId = parseInt(document.getElementById('new-teacher-select')?.value);
        const mentorId = parseInt(document.getElementById('new-mentor-select')?.value);
        if (teacherId) data.teacher_id = teacherId;
        if (mentorId) data.mentor_id = mentorId;

        showLoading(submitBtn, 'Indienen...');

        try {
          await InternshipsAPI.create(data);
          hideLoading(submitBtn);
          showToast('Stagevoorstel succesvol ingediend!', 'success');
          setTimeout(() => window.location.href = '?view=dashboard', 1000);
        } catch (error) {
          hideLoading(submitBtn);
          showToast(error.message, 'error');
        }
      });
    });
  }

  function wireLogbookForm() {
    const form = document.getElementById('logbook-form');
    const submitBtn = document.getElementById('submit-logbook');
    const cancelBtn = document.getElementById('cancel-logbook');
    const gridEl = document.getElementById('logbook-week-grid');
    const formPanel = document.getElementById('logbook-form-panel');
    const formWeekLabel = document.getElementById('form-week-label');

    if (!currentInternship) {
      content.innerHTML = `
        <div class="panel card">
          <h2>Geen stage gevonden</h2>
          <p>Je moet eerst een stage indienen voordat je logboeken kunt invullen.</p>
        </div>
      `;
      return;
    }

    const canLog = currentInternship.status === 'Lopend' || currentInternship.status === 'Afgerond';
    if (!canLog) {
      content.innerHTML = `
        <div class="panel card">
          <h2>Logboeken</h2>
          <p>Je kunt pas logboeken invullen als je stage actief is.</p>
          <p>Huidige status: <strong>${currentInternship.status}</strong></p>
          <a href="?view=dashboard" class="btn">${iconHtml('home', 16)} Naar dashboard</a>
        </div>
      `;
      return;
    }

    let selectedWeek = null;
    let selectedLogbook = null;

    // ── Build week grid ──
    function renderWeekGrid() {
      if (!gridEl) return;
      const start = currentInternship.start_date ? new Date(currentInternship.start_date) : null;
      const end = currentInternship.end_date ? new Date(currentInternship.end_date) : null;
      let totalWeeks = 0;
      if (start && end && end > start) {
        const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
        totalWeeks = Math.max(1, Math.floor(days / 7) + 1);
      }
      if (!totalWeeks) {
        gridEl.innerHTML = '<p class="hint">Stageperiode niet ingesteld.</p>';
        return;
      }

      const logbookMap = new Map(currentLogbooks.map(lb => [lb.week_number, lb]));

      gridEl.innerHTML = '';
      for (let w = 1; w <= totalWeeks; w++) {
        const lb = logbookMap.get(w);
        let statusClass = 'status-missing';
        let statusLabel = 'Ontbrekend';
        if (lb) {
          if (lb.status === 'submitted') {
            statusClass = 'status-submitted';
            statusLabel = lb.mentor_validated ? 'Aftekend' : 'Ingediend';
          } else {
            statusClass = 'status-draft';
            statusLabel = 'Concept';
          }
        }

        const cell = document.createElement('div');
        cell.className = `week-cell ${statusClass}`;
        cell.dataset.week = w;
        cell.setAttribute('role', 'button');
        cell.setAttribute('tabindex', '0');
        cell.setAttribute('aria-label', `Week ${w}: ${statusLabel}`);
        cell.innerHTML = `
          <span class="week-number">${w}</span>
          <span class="week-status">${statusLabel}</span>
        `;
        cell.addEventListener('click', () => openWeek(w));
        cell.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            openWeek(w);
          }
        });
        gridEl.appendChild(cell);
      }
    }

    // ── Open a week in the form ──
    function openWeek(week) {
      selectedWeek = week;
      selectedLogbook = currentLogbooks.find(lb => lb.week_number === week) || null;

      // Highlight selected cell
      gridEl?.querySelectorAll('.week-cell').forEach(c => c.classList.remove('selected'));
      gridEl?.querySelector(`[data-week="${week}"]`)?.classList.add('selected');

      // Show form panel
      if (formPanel) formPanel.style.display = 'block';
      if (formWeekLabel) formWeekLabel.textContent = week;

      document.getElementById('log-week').value = week;
      document.getElementById('log-tasks').value = selectedLogbook?.tasks || '';
      document.getElementById('log-reflection').value = selectedLogbook?.reflection || '';
      document.getElementById('log-issues').value = selectedLogbook?.issues || '';

      // Disable submit if already submitted
      if (submitBtn) {
        submitBtn.disabled = selectedLogbook?.status === 'submitted';
        submitBtn.textContent = selectedLogbook?.status === 'submitted' ? 'Reeds ingediend' : 'Definitief Indienen';
      }
    }

    function closeForm() {
      if (formPanel) formPanel.style.display = 'none';
      gridEl?.querySelectorAll('.week-cell').forEach(c => c.classList.remove('selected'));
      selectedWeek = null;
      selectedLogbook = null;
    }

    // ── Save as draft ──
    form?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const saveBtn = form.querySelector('button[type="submit"]');
      const week = parseInt(document.getElementById('log-week').value);
      const tasks = document.getElementById('log-tasks').value;

      if (!week) {
        showToast('Selecteer een week', 'error');
        return;
      }

      showLoading(saveBtn, 'Opslaan...');

      try {
        const payload = {
          week_number: week,
          tasks: tasks,
          reflection: document.getElementById('log-reflection').value,
          issues: document.getElementById('log-issues').value,
          status: 'draft'
        };

        if (selectedLogbook) {
          await InternshipsAPI.updateLogbook(selectedLogbook.id, payload);
        } else {
          await InternshipsAPI.createLogbook(currentInternship.id, payload);
        }

        hideLoading(saveBtn);
        showToast('Logboek opgeslagen als concept', 'info');

        // Refresh data and re-render grid
        currentLogbooks = await InternshipsAPI.getLogbooks(currentInternship.id);
        renderWeekGrid();
        // Re-open same week to update selectedLogbook reference
        if (selectedWeek) openWeek(selectedWeek);
      } catch (error) {
        hideLoading(saveBtn);
        showToast(error.message, 'error');
      }
    });

    // ── Submit ──
    submitBtn?.addEventListener('click', async () => {
      const week = parseInt(document.getElementById('log-week').value);
      const tasks = document.getElementById('log-tasks').value;

      if (!week) {
        showToast('Selecteer een week', 'error');
        return;
      }
      if (!tasks) {
        showToast('Taken zijn verplicht', 'error');
        return;
      }
      if (selectedLogbook?.status === 'submitted') {
        showToast('Logboek is al ingediend', 'error');
        return;
      }

      showLoading(submitBtn, 'Indienen...');

      try {
        // Ensure logbook exists first
        let logbook = selectedLogbook;
        if (!logbook) {
          logbook = await InternshipsAPI.createLogbook(currentInternship.id, {
            week_number: week,
            tasks: tasks,
            reflection: document.getElementById('log-reflection').value,
            issues: document.getElementById('log-issues').value,
            status: 'draft'
          });
        }

        // Submit via dedicated endpoint
        await InternshipsAPI.submitLogbook(logbook.id);

        hideLoading(submitBtn);
        showToast(`Logboek week ${week} ingediend!`, 'success');

        // Refresh data and re-render grid
        currentLogbooks = await InternshipsAPI.getLogbooks(currentInternship.id);
        renderWeekGrid();
        if (selectedWeek) openWeek(selectedWeek);
      } catch (error) {
        hideLoading(submitBtn);
        showToast(error.message, 'error');
      }
    });

    // ── Cancel ──
    cancelBtn?.addEventListener('click', closeForm);

    // ── Initial render ──
    renderWeekGrid();
  }

  function wireAgreementUpload() {
    const form = document.getElementById('agreement-form');
    const statusText = document.getElementById('agreement-status-text');

    if (!currentInternship) {
      content.innerHTML = `
        <div class="panel card">
          <h2>Geen stage gevonden</h2>
          <p>Je moet eerst een stage indienen.</p>
        </div>
      `;
      return;
    }

    const agreementStatus = currentInternship.agreement_status;

    // If agreement is already validated, show success regardless of internship status
    if (agreementStatus === 'Gevalideerd') {
      if (statusText) {
        statusText.innerHTML = `<span class="status-pill status-good">Gevalideerd</span>`;
      }
      form.innerHTML = `
        <div class="info-message success">
          <p>${iconHtml('check-circle', 16)} Je overeenkomst is gevalideerd. De stage is actief.</p>
        </div>
      `;
      return;
    }

    const canUpload = currentInternship.status === 'Goedgekeurd' || currentInternship.status === 'Overeenkomst Ingediend';

    if (!canUpload) {
      form.innerHTML = `
        <div class="info-message warning">
          <p>${iconHtml('alert-circle', 16)} Je kan geen overeenkomst uploaden in deze fase.</p>
          <p>Huidige status: <strong>${currentInternship.status}</strong></p>
          <a href="?view=dashboard" class="btn">${iconHtml('home', 16)} Naar dashboard</a>
        </div>
      `;
      return;
    }
    const hint = document.getElementById('agreement-hint');

    function setStatusLabel(label, className) {
      if (statusText) {
        statusText.innerHTML = `<span class="status-pill ${className}">${label}</span>`;
      }
    }

    function setHint(text) {
      if (hint) hint.textContent = text;
    }

    if (agreementStatus === 'Onvolledig') {
      setStatusLabel('Onvolledig', 'status-warn');
      setHint('De commissie heeft je overeenkomst als onvolledig gemarkeerd. Upload een nieuwe versie.');
      form.insertAdjacentHTML('afterbegin', `
        <div class="info-message warning" style="margin-bottom: 1rem;">
          <p>${iconHtml('alert-circle', 16)} De commissie heeft je overeenkomst als onvolledig gemarkeerd. Upload een nieuwe versie.</p>
        </div>
      `);
    } else if (agreementStatus === 'Ingediend') {
      setStatusLabel('Ingediend', 'status-info');
      setHint('Je overeenkomst is ingediend en wacht op validatie door de commissie.');
    }

    form?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fileInput = document.getElementById('agreement-file');
      const file = fileInput?.files[0];
      const submitBtn = form.querySelector('button[type="submit"]');

      if (!file) {
        showToast('Selecteer een PDF bestand', 'error');
        return;
      }

      if (file.type !== 'application/pdf') {
        showToast('Alleen PDF bestanden zijn toegestaan', 'error');
        return;
      }

      if (file.size > 5 * 1024 * 1024) {
        showToast('Bestand is te groot (max 5MB)', 'error');
        return;
      }

      showLoading(submitBtn, 'Uploaden...');

      try {
        await InternshipsAPI.uploadAgreement(currentInternship.id, file);
        hideLoading(submitBtn);
        showToast('Overeenkomst succesvol geüpload!', 'success');

        await refreshInternshipData();

        if (statusText) {
          statusText.innerHTML = '<span class="status-pill status-good">Ontvangen</span>';
        }
      } catch (error) {
        hideLoading(submitBtn);
        showToast(error.message, 'error');
      }
    });
  }

  async function renderStudentEvaluations() {
    const tbody = document.querySelector('table tbody');
    if (tbody && currentEvaluations.length > 0) {
      tbody.innerHTML = currentEvaluations.map(ev => `
        <tr>
          <td>${getEvalTypeLabel(ev.eval_type)}</td>
          <td>${ev.finalized ? formatDate(ev.finalized_at) : '-'}</td>
          <td>${ev.finalized ? 'Afgerond' : 'In behandeling'}</td>
          <td>${ev.finalized ? `<button class="btn small">${iconHtml('eye', 14)} Bekijken</button>` : '-'}</td>
        </tr>
      `).join('');
    } else if (tbody) {
      tbody.innerHTML = '<tr><td colspan="4">Geen evaluaties gevonden</td></tr>';
    }

    // US-09: Eindoverzicht ophalen
    const finalSummary = document.getElementById('final-summary');
    if (finalSummary && currentInternship) {
      try {
        const report = await InternshipsAPI.getFinalReport(currentInternship.id);
        const evalData = report?.final_evaluation;
        if (!evalData || !evalData.rules || evalData.rules.length === 0) {
          finalSummary.innerHTML = `
            <p><strong>Status:</strong> Afwachten</p>
            <p>De finale evaluatie is nog niet ingediend.</p>
          `;
        } else {
          const rows = formatReportRows(evalData.rules);
          const weightedScore = report.weighted_final_score !== null && report.weighted_final_score !== undefined
            ? (report.weighted_final_score / 20).toFixed(2)
            : '-';

          finalSummary.innerHTML = `
            <p><strong>Gewogen eindscore:</strong> <span class="score-highlight">${weightedScore} / 5</span></p>
            <table style="margin-top: 0.5rem;">
              <thead>
                <tr><th>Competentie</th><th>Gewicht</th><th>Score</th><th>Mijn beschrijving</th><th>Feedback</th></tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          `;
        }
      } catch (error) {
        console.error('Failed to load final report:', error);
        finalSummary.innerHTML = '<p class="error">Kon eindoverzicht niet laden.</p>';
      }
    }

    // US-06: Student zelfevaluatie - beschrijving per competentie
    const selfEvalPanel = document.getElementById('student-self-eval-panel');
    const selfEvalForm = document.getElementById('student-self-eval-form');
    let saveBtn = document.getElementById('btn-save-self-eval');

    if (!selfEvalPanel || !selfEvalForm) return;

    const canEvaluate = currentInternship && (currentInternship.status === 'Lopend' || currentInternship.status === 'Afgerond');
    const activeEval = currentEvaluations.find(e => !e.finalized);

    if (!canEvaluate) {
      selfEvalPanel.style.display = 'none';
      return;
    }

    if (activeEval && activeEval.rules && activeEval.rules.length > 0) {
      selfEvalPanel.style.display = 'block';
      selfEvalForm.innerHTML = activeEval.rules.map(rule => {
        const compName = rule.competency?.name || 'Onbekend';
        return `
          <div class="row full" style="margin-bottom: 0.75rem;">
            <label>${compName}</label>
            <textarea class="student-desc-field" data-rule-id="${rule.id}" data-eval-id="${activeEval.id}" rows="2" placeholder="Beschrijf wat je geleerd hebt...">${rule.student_description || ''}</textarea>
          </div>
        `;
      }).join('');

      // Replace the save button to prevent duplicate event listeners
      const newSaveBtn = saveBtn.cloneNode(true);
      newSaveBtn.style.display = '';
      saveBtn.replaceWith(newSaveBtn);
      saveBtn = newSaveBtn;

      saveBtn.addEventListener('click', async () => {
        const fields = selfEvalForm.querySelectorAll('.student-desc-field');
        showLoading(saveBtn, 'Opslaan...');
        try {
          for (const field of fields) {
            const ruleId = parseInt(field.dataset.ruleId);
            const evalId = parseInt(field.dataset.evalId);
            const description = field.value || null;
            await EvaluationRulesAPI.update(evalId, ruleId, { student_description: description });
          }
          showToast('Beschrijvingen opgeslagen!', 'success');
          await refreshInternshipData();
        } catch (error) {
          showToast(error.message, 'error');
        } finally {
          hideLoading(saveBtn);
        }
      });
    } else {
      // No active evaluation: show a button to create a self-evaluation
      selfEvalPanel.style.display = 'block';
      selfEvalForm.innerHTML = `
        <p class="hint">Er is nog geen actieve evaluatie beschikbaar. Start een zelfevaluatie om per competentie te beschrijven wat je geleerd hebt.</p>
        <button id="btn-start-self-eval" class="btn" style="margin-top: 1rem;">${iconHtml('check-circle', 16)} Start Zelfevaluatie</button>
      `;

      if (saveBtn) saveBtn.style.display = 'none';

      const startBtn = document.getElementById('btn-start-self-eval');
      startBtn?.addEventListener('click', async () => {
        showLoading(startBtn, 'Aanmaken...');
        try {
          await InternshipsAPI.createEvaluation(currentInternship.id, {
            eval_type: 'tussentijds',
            comments: 'Zelfevaluatie gestart door student'
          });
          showToast('Zelfevaluatie aangemaakt!', 'success');
          await refreshInternshipData();
          renderStudentEvaluations();
        } catch (error) {
          hideLoading(startBtn);
          showToast(error.message, 'error');
        }
      });
    }
  }