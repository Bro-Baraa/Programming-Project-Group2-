// ============================================
// Stage Monitoring Tool - Improved Prototype
// With localStorage persistence and async simulation
// ============================================

const roleViews = {
  student: ["dashboard", "voorstel", "logboek", "overeenkomst", "evaluaties"],
  commissie: ["voorstellen", "overzicht"],
  docent: ["opvolging", "evaluatie"],
  mentor: ["validatie"],
  admin: ["competenties"],
};

const stateGraph = {
  Ingediend: ["In Beoordeling"],
  "In Beoordeling": ["Goedgekeurd", "Afgekeurd", "Aanpassingen Vereist"],
  "Aanpassingen Vereist": ["Ingediend"],
  Goedgekeurd: ["Overeenkomst Ingediend"],
  "Overeenkomst Ingediend": ["Lopend"],
  Lopend: ["Afgerond"],
  Afgekeurd: [],
  Afgerond: [],
};

const templates = {
  student: "student-dashboard-template",
  "student-voorstel": "student-voorstel-template",
  "student-logboek": "student-logboek-template",
  "student-overeenkomst": "student-overeenkomst-template",
  "student-evaluaties": "student-evaluatie-template",
  commissie: "commissie-template",
  "commissie-overzicht": "commissie-overzicht-template",
  docent: "docent-template",
  "docent-evaluatie": "docent-evaluatie-template",
  mentor: "mentor-template",
  admin: "admin-template",
};

// Default data for initial load
const DEFAULT_DATA = {
  currentStatus: "Ingediend",
  agreementSigned: false,
  feedback: "",
  proposals: [
    { student: "Jan B.", company: "TechCorp", date: "14/03", status: "Ingediend" },
    { student: "Marie V.", company: "InnovateIT", date: "13/03", status: "In Beoordeling" },
    { student: "Pieter L.", company: "DataFlow", date: "12/03", status: "Aanpassingen vereist" },
  ],
  logbooks: [
    { week: 10, status: "Ingediend", mentor: "Goedgekeurd" },
    { week: 11, status: "Ingediend", mentor: "Goedgekeurd" },
    { week: 12, status: "Ontbrekend", mentor: "-" },
  ],
  competencies: [
    { name: "Analyseren", weight: 30, score: 4 },
    { name: "Ontwerpen", weight: 25, score: 3 },
    { name: "Realiseren", weight: 25, score: 4 },
    { name: "Testen", weight: 20, score: 3 },
  ],
  evaluations: [
    { type: "Tussentijds", date: "15/11/2026", status: "Afgerond" },
    { type: "Final", date: "-", status: "Nog niet" },
  ],
  currentProposal: null,
};

// State management
let appState = {};

// DOM elements
const roleSelect = document.getElementById("role-select");
const viewSelect = document.getElementById("view-select");
const content = document.getElementById("content");
const statusText = document.getElementById("current-status");
const statusActions = document.getElementById("status-actions");
const agreementToggle = document.getElementById("agreement-toggle");

// ============================================
// Storage & Persistence
// ============================================

function loadState() {
  try {
    const saved = localStorage.getItem("stageMonitoringState");
    if (saved) {
      appState = { ...DEFAULT_DATA, ...JSON.parse(saved) };
    } else {
      appState = { ...DEFAULT_DATA };
    }
  } catch (e) {
    console.warn("Failed to load state from localStorage", e);
    appState = { ...DEFAULT_DATA };
  }
}

function saveState() {
  try {
    localStorage.setItem("stageMonitoringState", JSON.stringify(appState));
  } catch (e) {
    console.warn("Failed to save state to localStorage", e);
  }
}

function resetData() {
  if (confirm("Alle data resetten naar standaardwaarden? Dit kan niet ongedaan gemaakt worden.")) {
    appState = { ...DEFAULT_DATA };
    saveState();
    loadState();
    updateStatusColor(appState.currentStatus);
    renderStatusActions();
    renderView();
    showToast("Data gereset naar standaardwaarden", "info");
  }
}

// ============================================
// Toast Notifications
// ============================================

function showToast(message, type = "success", duration = 3000) {
  // Remove existing toasts
  const existing = document.querySelector(".toast-notification");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.className = `toast-notification toast-${type}`;
  
  const icons = {
    success: "✓",
    error: "✗",
    warning: "⚠",
    info: "ℹ"
  };
  
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || "•"}</span>
    <span class="toast-message">${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">×</button>
  `;
  
  document.body.appendChild(toast);
  
  // Trigger animation
  requestAnimationFrame(() => {
    toast.classList.add("show");
  });
  
  // Auto remove
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ============================================
// Loading States
// ============================================

function showLoading(element, message = "Laden...") {
  if (!element) return;
  element.dataset.originalContent = element.innerHTML;
  element.innerHTML = `<span class="loading-spinner"></span> ${message}`;
  element.disabled = true;
}

function hideLoading(element) {
  if (!element) return;
  element.innerHTML = element.dataset.originalContent || element.innerHTML;
  element.disabled = false;
}

// Simulate async operation
function simulateAsync(callback, delay = 800) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const result = callback();
      resolve(result);
    }, delay);
  });
}

// ============================================
// View Rendering
// ============================================

function renderView() {
  const role = roleSelect.value;
  const currentView = viewSelect.value;

  // Populate dropdown if needed
  if (viewSelect.options.length === 0 || !currentView || !roleViews[role].includes(currentView)) {
    viewSelect.innerHTML = "";
    roleViews[role].forEach((view) => {
      const option = document.createElement("option");
      option.value = view;
      option.textContent = view.charAt(0).toUpperCase() + view.slice(1);
      viewSelect.appendChild(option);
    });
  }
  
  content.innerHTML = "";
  
  const view = viewSelect.value;
  const key = view ? `${role}-${view}` : role;
  const templateId = templates[key] || templates[role];
  

  
  const tpl = document.getElementById(templateId);
  if (tpl) {
    content.appendChild(tpl.content.cloneNode(true));
    
    // Add "last saved" indicator if data was modified
    addDataTimestamp();
  } else {
    console.error('Template not found:', templateId);
  }

  wireRoleInteractions(role);
}

function addDataTimestamp() {
  const timestamp = localStorage.getItem("stageMonitoringLastSave");
  if (timestamp) {
    const date = new Date(parseInt(timestamp));
    const timeStr = date.toLocaleString('nl-BE', { 
      hour: '2-digit', 
      minute: '2-digit',
      day: '2-digit',
      month: '2-digit'
    });
    
    const indicator = document.createElement("div");
    indicator.className = "data-timestamp";
    indicator.innerHTML = `Laatst opgeslagen: ${timeStr} <button onclick="resetData()" class="reset-link">Reset data</button>`;
    content.insertBefore(indicator, content.firstChild);
  }
}

// ============================================
// Status Machine
// ============================================

function updateStatusColor(status) {
  const stateClass =
    status === "Afgekeurd"
      ? "var(--bad)"
      : status === "Aanpassingen Vereist"
      ? "var(--warn)"
      : "var(--good)";

  statusText.textContent = status;
  statusText.style.background = `color-mix(in srgb, ${stateClass} 20%, white)`;
  statusText.style.color = `color-mix(in srgb, ${stateClass} 75%, black)`;
}

function renderStatusActions() {
  statusActions.innerHTML = "";
  const transitions = stateGraph[appState.currentStatus] || [];

  if (!transitions.length) {
    const done = document.createElement("p");
    done.className = "hint";
    done.textContent = "Geen verdere transities vanuit deze status.";
    statusActions.appendChild(done);
    return;
  }

  transitions.forEach((next) => {
    const btn = document.createElement("button");
    btn.className = "btn small";
    btn.textContent = next;
    btn.addEventListener("click", async () => {
      if (next === "Lopend" && !appState.agreementSigned) {
        showToast("Kan niet naar 'Lopend' zonder getekende overeenkomst", "error");
        return;
      }
      
      btn.disabled = true;
      await simulateAsync(() => {
        appState.currentStatus = next;
        saveState();
      });
      
      updateStatusColor(appState.currentStatus);
      renderStatusActions();
      showToast(`Status gewijzigd naar: ${next}`, "success");
    });
    statusActions.appendChild(btn);
  });
}

// ============================================
// Competency Management
// ============================================

function sumWeights() {
  return appState.competencies.reduce((sum, c) => sum + c.weight, 0);
}

function weightedScore() {
  return appState.competencies.reduce((sum, c) => sum + c.weight * c.score, 0) / 100;
}

function renderCompetencies() {
  const list = document.getElementById("competency-list");
  const scoreInputs = document.getElementById("score-inputs");
  const weightCheck = document.getElementById("weight-check");

  if (!list || !scoreInputs || !weightCheck) {
    return;
  }

  list.innerHTML = "";
  scoreInputs.innerHTML = "";

  appState.competencies.forEach((comp, index) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <span class="comp-name">${comp.name}</span>
      <span class="comp-weight">${comp.weight}%</span>
    `;

    const removeBtn = document.createElement("button");
    removeBtn.className = "btn small alt";
    removeBtn.textContent = "Verwijder";
    removeBtn.style.marginLeft = "0.6rem";
    removeBtn.addEventListener("click", async () => {
      if (confirm(`Competentie "${comp.name}" verwijderen?`)) {
        await simulateAsync(() => {
          appState.competencies.splice(index, 1);
          saveState();
        });
        renderCompetencies();
        showToast(`Competentie "${comp.name}" verwijderd`, "info");
      }
    });

    li.appendChild(removeBtn);
    list.appendChild(li);

    const row = document.createElement("div");
    row.className = "row score-row";
    
    const label = document.createElement("label");
    label.textContent = `${comp.name} (${comp.weight}%)`;

    const input = document.createElement("input");
    input.type = "number";
    input.min = "1";
    input.max = "5";
    input.value = String(comp.score);
    input.addEventListener("change", (e) => {
      comp.score = Number(e.target.value || 0);
      saveState();
    });

    row.appendChild(label);
    row.appendChild(input);
    scoreInputs.appendChild(row);
  });

  const total = sumWeights();
  const valid = total === 100;
  weightCheck.textContent = `Totaal gewicht: ${total}% ${valid ? "✓ OK" : "⚠ Moet 100% zijn"}`;
  weightCheck.className = `weight-check ${valid ? "valid" : "invalid"}`;
}

// ============================================
// Role Interactions
// ============================================

function wireRoleInteractions(role) {
  const view = viewSelect.value;
  
  // Sync agreement toggle with state
  if (agreementToggle) {
    agreementToggle.checked = appState.agreementSigned;
    agreementToggle.addEventListener("change", () => {
      appState.agreementSigned = agreementToggle.checked;
      saveState();
    });
  }
  
  // STUDENT VIEWS
  if (role === "student") {
    // Stagevoorstel form
    if (view === "voorstel") {
      const form = document.getElementById("proposal-form");
      const result = document.getElementById("proposal-result");
      
      // Fill form if we have saved data
      if (appState.currentProposal) {
        document.getElementById("company-name").value = appState.currentProposal.company || "";
        document.getElementById("contact-person").value = appState.currentProposal.contact || "";
        document.getElementById("contact-email").value = appState.currentProposal.email || "";
        if (appState.currentProposal.start) document.getElementById("start-date").value = appState.currentProposal.start;
        if (appState.currentProposal.end) document.getElementById("end-date").value = appState.currentProposal.end;
        document.getElementById("assignment-desc").value = appState.currentProposal.description || "";
      }
      
      form?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const submitBtn = form.querySelector('button[type="submit"]');
        
        const company = document.getElementById("company-name").value.trim();
        const contact = document.getElementById("contact-person").value.trim();
        const email = document.getElementById("contact-email").value.trim();
        const start = document.getElementById("start-date").value;
        const end = document.getElementById("end-date").value;
        const desc = document.getElementById("assignment-desc").value.trim();
        
        // Validation
        const errors = [];
        if (!company) errors.push("Bedrijfsnaam is verplicht");
        if (!contact) errors.push("Contactpersoon is verplicht");
        if (!email || !email.includes('@')) errors.push("Geldig e-mailadres is verplicht");
        if (!start) errors.push("Startdatum is verplicht");
        if (!end) errors.push("Einddatum is verplicht");
        if (start && end && new Date(start) > new Date(end)) errors.push("Einddatum moet na startdatum zijn");
        if (!desc || desc.length < 20) errors.push("Omschrijving moet minimaal 20 karakters bevatten");
        
        if (errors.length > 0) {
          showToast(errors.join("\n"), "error", 5000);
          return;
        }
        
        showLoading(submitBtn, "Indienen...");
        
        await simulateAsync(() => {
          appState.currentProposal = { company, contact, email, start, end, description: desc };
          appState.currentStatus = "Ingediend";
          saveState();
        });
        
        hideLoading(submitBtn);
        showToast(`Stagevoorstel ingediend voor ${company}!`, "success");
        
        updateStatusColor(appState.currentStatus);
        renderStatusActions();
      });
    }
    
    // Logboek form
    if (view === "logboek") {
      const form = document.getElementById("logbook-form");
      const submitBtn = document.getElementById("submit-logbook");
      
      submitBtn?.addEventListener("click", async () => {
        const week = document.getElementById("log-week")?.value;
        const tasks = document.getElementById("log-tasks")?.value?.trim();
        
        if (!week || !tasks) {
          showToast("Weeknummer en taken zijn verplicht", "error");
          return;
        }
        
        showLoading(submitBtn, "Indienen...");
        
        await simulateAsync(() => {
          // Check if logbook for this week exists
          const existing = appState.logbooks.find(lb => lb.week === parseInt(week));
          if (existing) {
            existing.status = "Ingediend";
          } else {
            appState.logbooks.push({ week: parseInt(week), status: "Ingediend", mentor: "In afwachting" });
          }
          saveState();
        });
        
        hideLoading(submitBtn);
        showToast(`Logboek week ${week} definitief ingediend!`, "success");
      });
      
      form?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const week = document.getElementById("log-week")?.value;
        const saveBtn = form.querySelector('button[type="submit"]');
        
        showLoading(saveBtn, "Opslaan...");
        
        await simulateAsync(() => {
          saveState();
        });
        
        hideLoading(saveBtn);
        showToast(`Logboek week ${week} opgeslagen als concept`, "info");
      });
    }
    
    // Overeenkomst upload
    if (view === "overeenkomst") {
      const form = document.getElementById("agreement-form");
      const statusText = document.getElementById("agreement-status-text");
      
      // Update status display
      if (appState.agreementSigned) {
        statusText.innerHTML = '<span class="status-approved">Ontvangen</span>';
      }
      
      form?.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById("agreement-file");
        const file = fileInput?.files[0];
        const submitBtn = form.querySelector('button[type="submit"]');
        
        if (!file) {
          showToast("Selecteer een PDF bestand", "error");
          return;
        }
        
        if (file.type !== "application/pdf") {
          showToast("Alleen PDF bestanden zijn toegestaan", "error");
          return;
        }
        
        // Size check (max 5MB)
        if (file.size > 5 * 1024 * 1024) {
          showToast("Bestand is te groot (max 5MB)", "error");
          return;
        }
        
        showLoading(submitBtn, "Uploaden...");
        
        await simulateAsync(() => {
          appState.agreementSigned = true;
          saveState();
        });
        
        hideLoading(submitBtn);
        
        if (statusText) {
          statusText.innerHTML = '<span class="status-approved">Ontvangen</span>';
        }
        
        agreementToggle.checked = true;
        showToast(`Overeenkomst '${file.name}' succesvol geüpload!`, "success");
      });
    }
    
    // Evaluaties view - populate with saved data
    if (view === "evaluaties") {
      const tbody = document.querySelector('table tbody');
      if (tbody && appState.evaluations) {
        tbody.innerHTML = appState.evaluations.map(ev => `
          <tr>
            <td>${ev.type}</td>
            <td>${ev.date}</td>
            <td>${ev.status}</td>
            <td>${ev.status === "Afgerond" ? '<button class="btn small">Bekijken</button>' : '-'}</td>
          </tr>
        `).join('');
      }
    }
  }

  // COMMISSIE VIEWS
  if (role === "commissie") {
    // Update proposals table with saved data
    const tbody = document.querySelector('table tbody');
    if (tbody && appState.proposals) {
      tbody.innerHTML = appState.proposals.map(p => `
        <tr>
          <td>${p.student}</td>
          <td>${p.company}</td>
          <td>${p.date}</td>
          <td><span class="status-pill status-${p.status.toLowerCase().replace(/\s+/g, '-')}">${p.status}</span></td>
        </tr>
      `).join('');
    }
    
    // Feedback form
    const feedbackBox = document.getElementById("feedback-box");
    const saveBtn = document.getElementById("save-feedback");
    
    if (appState.feedback && feedbackBox) {
      feedbackBox.value = appState.feedback;
    }
    
    saveBtn?.addEventListener("click", async () => {
      const feedback = feedbackBox?.value.trim() || "";
      showLoading(saveBtn, "Opslaan...");
      
      await simulateAsync(() => {
        appState.feedback = feedback;
        saveState();
      });
      
      hideLoading(saveBtn);
      showToast(feedback ? "Feedback opgeslagen" : "Geen feedback ingegeven", feedback ? "success" : "info");
    });
  }

  // DOCENT VIEWS
  if (role === "docent" && view === "evaluatie") {
    const evalForm = document.getElementById("eval-form");
    const finalizeBtn = document.getElementById("finalize-eval");
    const evalCompetencies = document.getElementById("eval-competencies");
    
    // Render competencies for evaluation
    if (evalCompetencies) {
      evalCompetencies.innerHTML = "";
      appState.competencies.forEach((comp) => {
        const row = document.createElement("div");
        row.className = "eval-row";
        
        row.innerHTML = `
          <label>${comp.name} (${comp.weight}%)</label>
          <div class="score-inputs">
            <select class="score-select" data-comp="${comp.name}">
              <option value="1">1 - Onvoldoende</option>
              <option value="2">2 - Matig</option>
              <option value="3" selected>3 - Voldoende</option>
              <option value="4">4 - Goed</option>
              <option value="5">5 - Uitstekend</option>
            </select>
            <input type="text" class="feedback-input" placeholder="Feedback voor deze competentie..." />
          </div>
        `;
        evalCompetencies.appendChild(row);
      });
    }
    
    finalizeBtn?.addEventListener("click", async () => {
      if (sumWeights() !== 100) {
        showToast("Kan niet afsluiten: gewichten moeten 100% zijn", "error");
        return;
      }
      
      if (!confirm("Evaluatie definitief afsluiten? Dit kan niet ongedaan gemaakt worden.")) {
        return;
      }
      
      showLoading(finalizeBtn, "Bezig...");
      
      await simulateAsync(() => {
        // Update the final evaluation
        const finalEval = appState.evaluations.find(e => e.type === "Final");
        if (finalEval) {
          finalEval.status = "Afgerond";
          finalEval.date = new Date().toLocaleDateString('nl-BE');
        }
        saveState();
      });
      
      hideLoading(finalizeBtn);
      showToast("Evaluatie definitief afgesloten!", "success");
    });
    
    evalForm?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const saveBtn = evalForm.querySelector('button[type="submit"]');
      
      showLoading(saveBtn, "Opslaan...");
      
      await simulateAsync(() => {
        saveState();
      });
      
      hideLoading(saveBtn);
      showToast("Evaluatie opgeslagen als concept", "info");
    });
  }

  // ADMIN VIEWS
  if (role === "admin") {
    const form = document.getElementById("competency-form");
    const nameInput = document.getElementById("comp-name");
    const weightInput = document.getElementById("comp-weight");
    const calcBtn = document.getElementById("calc-score");
    const scoreResult = document.getElementById("score-result");

    renderCompetencies();

    form?.addEventListener("submit", async (e) => {
      e.preventDefault();
      const name = nameInput?.value.trim();
      const weight = Number(weightInput?.value);
      const submitBtn = form.querySelector('button[type="submit"]');

      if (!name || Number.isNaN(weight)) {
        showToast("Vul alle velden in", "error");
        return;
      }
      
      // Check for duplicate
      if (appState.competencies.find(c => c.name.toLowerCase() === name.toLowerCase())) {
        showToast("Competentie met deze naam bestaat al", "error");
        return;
      }

      showLoading(submitBtn, "Toevoegen...");
      
      await simulateAsync(() => {
        appState.competencies.push({ name, weight, score: 3 });
        saveState();
      });
      
      hideLoading(submitBtn);
      
      if (nameInput) nameInput.value = "";
      if (weightInput) weightInput.value = "";
      
      renderCompetencies();
      showToast(`Competentie "${name}" toegevoegd`, "success");
    });

    calcBtn?.addEventListener("click", async () => {
      if (sumWeights() !== 100) {
        if (scoreResult) {
          scoreResult.textContent = "Kan niet berekenen: gewichten moeten exact 100% zijn";
          scoreResult.className = "result error";
        }
        showToast("Gewichten moeten 100% zijn", "error");
        return;
      }

      showLoading(calcBtn, "Berekenen...");
      
      const result = await simulateAsync(() => weightedScore());
      
      hideLoading(calcBtn);
      
      if (scoreResult) {
        scoreResult.textContent = `Gewogen eindscore: ${result.toFixed(2)} / 5`;
        scoreResult.className = "result success";
      }
      showToast(`Eindscore berekend: ${result.toFixed(2)} / 5`, "success");
    });
  }
}

// ============================================
// Event Listeners
// ============================================

roleSelect.addEventListener("change", () => {
  viewSelect.innerHTML = ""; // Force re-populate
  renderView();
});

viewSelect.addEventListener("change", () => {
  renderView();
});

// ============================================
// Initialization
// ============================================

function init() {
  loadState();
  
  // Track save time
  const originalSave = saveState;
  saveState = function() {
    originalSave();
    localStorage.setItem("stageMonitoringLastSave", Date.now());
  };
  
  // Sync UI with loaded state
  updateStatusColor(appState.currentStatus);
  if (agreementToggle) {
    agreementToggle.checked = appState.agreementSigned;
  }
  
  renderStatusActions();
  renderView();
  

}

// Start the app
init();