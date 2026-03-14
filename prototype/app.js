const roleViews = {
  student: ["dashboard"],
  commissie: ["voorstellen"],
  docent: ["opvolging"],
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
  commissie: "commissie-template",
  docent: "docent-template",
  mentor: "mentor-template",
  admin: "admin-template",
};

const roleSelect = document.getElementById("role-select");
const viewSelect = document.getElementById("view-select");
const content = document.getElementById("content");
const statusText = document.getElementById("current-status");
const statusActions = document.getElementById("status-actions");
const agreementToggle = document.getElementById("agreement-toggle");

let currentStatus = "Ingediend";
let feedback = "";
const competencies = [
  { name: "Analyseren", weight: 30, score: 4 },
  { name: "Ontwerpen", weight: 25, score: 3 },
  { name: "Realiseren", weight: 25, score: 4 },
  { name: "Testen", weight: 20, score: 3 },
];

function renderView() {
  const role = roleSelect.value;

  viewSelect.innerHTML = "";
  roleViews[role].forEach((view) => {
    const option = document.createElement("option");
    option.value = view;
    option.textContent = view.charAt(0).toUpperCase() + view.slice(1);
    viewSelect.appendChild(option);
  });

  content.innerHTML = "";
  const templateId = templates[role];
  const tpl = document.getElementById(templateId);
  content.appendChild(tpl.content.cloneNode(true));

  wireRoleInteractions(role);
}

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
  const transitions = stateGraph[currentStatus] || [];

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
    btn.addEventListener("click", () => {
      if (next === "Lopend" && !agreementToggle.checked) {
        alert("Kan niet naar Lopend zonder overeenkomst_getekend = true");
        return;
      }
      currentStatus = next;
      updateStatusColor(currentStatus);
      renderStatusActions();
    });
    statusActions.appendChild(btn);
  });
}

function sumWeights() {
  return competencies.reduce((sum, c) => sum + c.weight, 0);
}

function weightedScore() {
  return competencies.reduce((sum, c) => sum + c.weight * c.score, 0) / 100;
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

  competencies.forEach((comp, index) => {
    const li = document.createElement("li");
    li.textContent = `${comp.name} - ${comp.weight}%`;

    const removeBtn = document.createElement("button");
    removeBtn.className = "btn small alt";
    removeBtn.textContent = "Verwijder";
    removeBtn.style.marginLeft = "0.6rem";
    removeBtn.addEventListener("click", () => {
      competencies.splice(index, 1);
      renderCompetencies();
    });

    li.appendChild(removeBtn);
    list.appendChild(li);

    const row = document.createElement("div");
    row.className = "row";
    row.style.marginBottom = "0.45rem";

    const label = document.createElement("label");
    label.textContent = `${comp.name} (${comp.weight}%)`;
    label.style.margin = "0";

    const input = document.createElement("input");
    input.type = "number";
    input.min = "1";
    input.max = "5";
    input.value = String(comp.score);
    input.addEventListener("input", (e) => {
      comp.score = Number(e.target.value || 0);
    });

    row.appendChild(label);
    row.appendChild(input);
    scoreInputs.appendChild(row);
  });

  const total = sumWeights();
  const valid = total === 100;
  weightCheck.textContent = `Totaal gewicht: ${total}% ${valid ? "(OK)" : "(Moet 100% zijn)"}`;
  weightCheck.style.color = valid ? "#0b6a4f" : "#8a3f00";
}

function wireRoleInteractions(role) {
  if (role === "commissie") {
    const feedbackBox = document.getElementById("feedback-box");
    const saveBtn = document.getElementById("save-feedback");
    const feedbackResult = document.getElementById("feedback-result");

    saveBtn?.addEventListener("click", () => {
      feedback = feedbackBox.value.trim();
      feedbackResult.textContent = feedback
        ? `Feedback opgeslagen: \"${feedback}\"`
        : "Geen feedback ingegeven.";
    });
  }

  if (role === "admin") {
    const form = document.getElementById("competency-form");
    const nameInput = document.getElementById("comp-name");
    const weightInput = document.getElementById("comp-weight");
    const calcBtn = document.getElementById("calc-score");
    const scoreResult = document.getElementById("score-result");

    renderCompetencies();

    form?.addEventListener("submit", (e) => {
      e.preventDefault();
      const name = nameInput.value.trim();
      const weight = Number(weightInput.value);

      if (!name || Number.isNaN(weight)) {
        return;
      }

      competencies.push({ name, weight, score: 3 });
      nameInput.value = "";
      weightInput.value = "";
      renderCompetencies();
    });

    calcBtn?.addEventListener("click", () => {
      if (sumWeights() !== 100) {
        scoreResult.textContent = "Kan niet berekenen: gewichten moeten exact 100% zijn.";
        scoreResult.style.color = "#8b0000";
        return;
      }

      const result = weightedScore();
      scoreResult.textContent = `Gewogen eindscore: ${result.toFixed(2)} / 5`;
      scoreResult.style.color = "#053b2d";
    });
  }
}

roleSelect.addEventListener("change", renderView);
agreementToggle.addEventListener("change", () => {
  if (currentStatus === "Overeenkomst Ingediend") {
    renderStatusActions();
  }
});

updateStatusColor(currentStatus);
renderStatusActions();
renderView();
