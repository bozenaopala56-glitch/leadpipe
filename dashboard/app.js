const state = {
  data: null,
  activeBatchId: null,
  activeView: "overview",
  selectedLeadId: null,
  selectedCampaign: "",
  filters: { search: "", campaign: "", status: "", date: "", domain: "" }
};

const campaignLabels = {
  REDESIGN_OUTDATED: "Stara strona, brak RWD, lata 90.",
  REDESIGN_ADS_WASTE: "Reklamy prowadza na slaba strone.",
  REDESIGN_CONVERSION: "Strona jest, ale nie konwertuje.",
  REDESIGN_TRUST: "Brak SSL albo niski poziom zaufania.",
  WORDPRESS_REWORK: "WordPress do przebudowy na custom kod.",
  MOBILE_REBUILD: "Strona nie dziala poprawnie na telefonie.",
  TECH_REBUILD: "Strona dziala, ale technicznie jest do wymiany."
};

const statusClass = {
  send: "ok",
  approved: "ok",
  exported: "ok",
  manual_review: "manual",
  t2_required: "manual",
  t2_optional: "info",
  retry: "warning",
  skip: "error",
  rejected: "error"
};

document.addEventListener("DOMContentLoaded", init);

async function init() {
  const response = await fetch("data/sample-batch.json", { cache: "no-store" });
  state.data = await response.json();
  state.activeBatchId = state.data.active_batch_id;
  state.selectedLeadId = getBatchLeads()[0]?.id || null;

  bindEvents();
  populateControls();
  render();
}

function bindEvents() {
  document.querySelectorAll(".nav-item").forEach(button => {
    button.addEventListener("click", () => setView(button.dataset.view));
  });
  document.querySelectorAll("[data-jump]").forEach(button => {
    button.addEventListener("click", () => setView(button.dataset.jump));
  });
  document.getElementById("batchSelect").addEventListener("change", event => {
    state.activeBatchId = event.target.value;
    state.selectedLeadId = getBatchLeads()[0]?.id || null;
    render();
  });
  [
    ["searchInput", "search"],
    ["campaignFilter", "campaign"],
    ["statusFilter", "status"],
    ["dateFilter", "date"],
    ["domainFilter", "domain"]
  ].forEach(([id, key]) => {
    document.getElementById(id).addEventListener("input", event => {
      state.filters[key] = event.target.value.trim();
      renderQa();
    });
  });
  document.getElementById("exportCsvBtn").addEventListener("click", exportCsv);
  document.getElementById("feedbackInput").addEventListener("change", importFeedback);
}

function populateControls() {
  document.getElementById("rulesetLabel").textContent = state.data.ruleset_version;
  const batchSelect = document.getElementById("batchSelect");
  batchSelect.innerHTML = state.data.batches.map(batch =>
    `<option value="${batch.id}">${batch.name}</option>`
  ).join("");
  batchSelect.value = state.activeBatchId;

  const campaigns = [...new Set(state.data.leads.map(lead => lead.campaign))].sort();
  const campaignFilter = document.getElementById("campaignFilter");
  campaignFilter.innerHTML = `<option value="">Wszystkie kampanie</option>` + campaigns.map(campaign =>
    `<option value="${campaign}">${campaign}</option>`
  ).join("");
}

function setView(view) {
  state.activeView = view;
  document.querySelectorAll(".nav-item").forEach(item => item.classList.toggle("active", item.dataset.view === view));
  document.querySelectorAll(".view").forEach(section => section.classList.toggle("active", section.id === view));
  document.getElementById("pageTitle").textContent = {
    overview: "Dashboard",
    qa: "QA workflow",
    campaigns: "Kampanie",
    exports: "Eksport",
    batches: "Batch"
  }[view];
  render();
}

function render() {
  renderOverview();
  renderQa();
  renderCampaigns();
  renderExports();
  renderBatches();
}

function getActiveBatch() {
  return state.data.batches.find(batch => batch.id === state.activeBatchId);
}

function getBatchLeads() {
  return state.data.leads.filter(lead => lead.batch_id === state.activeBatchId);
}

function filteredLeads() {
  const search = state.filters.search.toLowerCase();
  const domain = state.filters.domain.toLowerCase();
  return getBatchLeads().filter(lead => {
    const haystack = `${lead.company} ${lead.domain} ${lead.nip}`.toLowerCase();
    return (!search || haystack.includes(search))
      && (!state.filters.campaign || lead.campaign === state.filters.campaign)
      && (!state.filters.status || lead.decision === state.filters.status || lead.qa_status === state.filters.status)
      && (!state.filters.date || lead.decision_date === state.filters.date)
      && (!domain || lead.domain.toLowerCase().includes(domain));
  });
}

function computeStats(leads) {
  return {
    total: leads.length,
    scanned: leads.filter(lead => lead.scanned).length,
    decided: leads.filter(lead => lead.decision).length,
    exported: leads.filter(lead => lead.exported || lead.qa_status === "approved").length,
    suppressed: leads.filter(lead => lead.suppressed).length,
    qa: leads.filter(lead => ["manual_review", "t2_required", "t2_optional"].includes(lead.decision)).length
  };
}

function renderOverview() {
  const batch = getActiveBatch();
  const leads = getBatchLeads();
  const stats = computeStats(leads);
  const progress = Math.round((stats.decided / Math.max(stats.total, 1)) * 100);

  document.getElementById("statGrid").innerHTML = [
    ["Leady w batchu", stats.total, `${stats.qa} w QA`],
    ["Zeskanowane", stats.scanned, `${Math.round(stats.scanned / stats.total * 100)}% batcha`],
    ["Z decyzja", stats.decided, `${stats.suppressed} suppressed`],
    ["Wyeksportowane", stats.exported, "approved albo export"]
  ].map(([label, value, note]) => `<article class="stat-card"><span>${label}</span><strong>${value}</strong><small>${note}</small></article>`).join("");

  document.getElementById("batchStatusBadge").textContent = batch.status;
  document.getElementById("batchStatusBadge").className = `badge ${batch.status === "completed" ? "ok" : "info"}`;
  document.getElementById("batchProgressText").textContent = `${stats.decided}/${stats.total} decyzji`;
  document.getElementById("batchProgressPct").textContent = `${progress}%`;
  document.getElementById("batchProgressBar").style.width = `${progress}%`;
  document.getElementById("batchMiniMetrics").innerHTML = [
    ["T0 ok", batch.metrics.t0_ok],
    ["T1 ok", batch.metrics.t1_ok],
    ["T2 queue", batch.metrics.t2_queue],
    ["Avg conf", pct(avg(leads.map(lead => lead.confidence)))]
  ].map(([label, value]) => `<div><span class="muted">${label}</span><strong>${value}</strong></div>`).join("");

  const alerts = state.data.alerts.filter(alert => alert.batch_id === state.activeBatchId);
  document.getElementById("alertCount").textContent = alerts.length;
  document.getElementById("alertsList").innerHTML = alerts.map(alert =>
    `<div class="event"><div><strong>${alert.title}</strong><br><span class="muted">${alert.message}</span></div><span class="badge ${alert.level}">${alert.level}</span></div>`
  ).join("");

  document.getElementById("recentDecisions").innerHTML = leads.slice().sort((a, b) => b.decision_date.localeCompare(a.decision_date)).slice(0, 8).map(lead =>
    `<tr><td>${lead.company}</td><td>${lead.domain}</td><td>${lead.campaign}</td><td>${badge(lead.decision)}</td><td>${pct(lead.confidence)}</td><td>${lead.evidence[0] || ""}</td></tr>`
  ).join("");

  drawBarChart("campaignTrendChart", groupByDate(leads), ["#58a6ff", "#3fb950"]);
  drawBarChart("suppressionChart", { Suppressed: stats.suppressed, Clean: stats.total - stats.suppressed }, ["#f85149", "#3fb950"]);
  drawBarChart("contactChart", contactBuckets(leads), ["#d29922", "#58a6ff", "#3fb950"]);
}

function renderQa() {
  const leads = filteredLeads();
  if (!leads.find(lead => lead.id === state.selectedLeadId)) state.selectedLeadId = leads[0]?.id || null;
  document.getElementById("qaCount").textContent = `${leads.length} rekordow`;
  document.getElementById("leadList").innerHTML = leads.map(lead => `
    <article class="lead-row ${lead.id === state.selectedLeadId ? "active" : ""}" data-lead="${lead.id}">
      <div class="lead-row-main">
        <strong>${lead.company}</strong>
        ${badge(lead.decision)}
      </div>
      <small>${lead.domain} · ${lead.nip} · ${lead.campaign}</small>
      <div class="signal-grid">
        <span class="badge info">conf ${pct(lead.confidence)}</span>
        <span class="badge ${lead.contactability >= 70 ? "ok" : lead.contactability >= 45 ? "warning" : "error"}">contact ${lead.contactability}</span>
        <span class="badge manual">${lead.qa_status}</span>
      </div>
    </article>
  `).join("");
  document.querySelectorAll("[data-lead]").forEach(row => {
    row.addEventListener("click", () => {
      state.selectedLeadId = row.dataset.lead;
      renderQa();
    });
  });
  renderLeadDetail(leads.find(lead => lead.id === state.selectedLeadId));
}

function renderLeadDetail(lead) {
  const panel = document.getElementById("leadDetail");
  if (!lead) {
    panel.innerHTML = `<p class="muted">Brak leadow dla aktualnych filtrow.</p>`;
    return;
  }
  panel.innerHTML = `
    <div class="panel-head">
      <div><h2>${lead.company}</h2><span class="muted">${lead.domain}</span></div>
      ${badge(lead.qa_status)}
    </div>
    <div class="detail-grid">
      ${detail("NIP", lead.nip)}
      ${detail("Email", lead.email || "brak")}
      ${detail("Telefon", lead.phone || "brak")}
      ${detail("Kampania", lead.campaign)}
      ${detail("Decyzja", lead.decision)}
      ${detail("Regula", lead.rule_key)}
      ${detail("Confidence", pct(lead.confidence))}
      ${detail("Lead value", lead.lead_value)}
    </div>
    <h3>T0/T1 sygnaly</h3>
    <div class="signal-grid">
      ${Object.entries(lead.signals).map(([key, value]) => `<span class="badge info">${key}: ${value}</span>`).join("")}
    </div>
    <h3>Evidence</h3>
    <ul class="evidence-list">${lead.evidence.map(item => `<li>${item}</li>`).join("")}</ul>
    <div class="actions">
      <button class="success" data-action="approve">Approve</button>
      <button class="danger" data-action="reject">Reject</button>
      <button class="warning-btn" data-action="manual_review">Manual review</button>
      <select id="campaignChange">${Object.keys(campaignLabels).map(campaign => `<option value="${campaign}" ${campaign === lead.campaign ? "selected" : ""}>${campaign}</option>`).join("")}</select>
      <button class="ghost" data-action="change_campaign">Zmien kampanie</button>
    </div>
  `;
  panel.querySelectorAll("[data-action]").forEach(button => {
    button.addEventListener("click", () => handleQaAction(lead, button.dataset.action));
  });
}

function handleQaAction(lead, action) {
  if (action === "approve") {
    lead.qa_status = "approved";
    lead.decision = "send";
    lead.exported = true;
  }
  if (action === "reject") {
    lead.qa_status = "rejected";
    lead.decision = "skip";
    lead.exported = false;
  }
  if (action === "manual_review") {
    lead.qa_status = "manual_review";
    lead.decision = "manual_review";
  }
  if (action === "change_campaign") {
    lead.campaign = document.getElementById("campaignChange").value;
    lead.qa_status = "manual_review";
    lead.evidence.unshift(`QA changed campaign to ${lead.campaign}`);
  }
  state.data.alerts.unshift({
    batch_id: state.activeBatchId,
    level: action === "reject" ? "error" : "info",
    title: `QA ${action}`,
    message: `${lead.company} (${lead.domain})`,
    created_at: new Date().toISOString()
  });
  render();
}

function renderCampaigns() {
  const leads = getBatchLeads();
  const byCampaign = group(leads, lead => lead.campaign);
  const rows = Object.entries(byCampaign).sort((a, b) => b[1].length - a[1].length);
  if (!state.selectedCampaign && rows[0]) state.selectedCampaign = rows[0][0];
  document.getElementById("campaignTable").innerHTML = rows.map(([campaign, items]) => {
    const feedback = state.data.feedback[campaign] || { reply_rate: 0 };
    const manual = items.filter(lead => lead.qa_status === "manual_review").length;
    return `<tr class="clickable" data-campaign="${campaign}"><td>${campaign}</td><td>${items.length}</td><td>${pct(avg(items.map(lead => lead.confidence)))}</td><td>${pct(feedback.reply_rate)}</td><td>${manual}</td></tr>`;
  }).join("");
  document.querySelectorAll("[data-campaign]").forEach(row => {
    row.addEventListener("click", () => {
      state.selectedCampaign = row.dataset.campaign;
      renderCampaigns();
    });
  });
  document.getElementById("campaignSummaryPanel").innerHTML = `
    <div class="panel-head"><h2>${state.selectedCampaign || "Kampania"}</h2>${badge(`${(byCampaign[state.selectedCampaign] || []).length} leadow`)}</div>
    <p class="muted">${campaignLabels[state.selectedCampaign] || "Wybierz kampanie z tabeli."}</p>
  `;
  const campaignLeads = leads.filter(lead => lead.campaign === state.selectedCampaign);
  document.getElementById("campaignLeadTitle").textContent = `Leady: ${state.selectedCampaign || ""}`;
  document.getElementById("campaignLeadList").innerHTML = campaignLeads.map(lead =>
    `<div class="compact-row"><strong>${lead.company}</strong><br><small>${lead.domain} · ${badge(lead.decision)} · conf ${pct(lead.confidence)}</small></div>`
  ).join("");
  drawBarChart("campaignDistributionChart", Object.fromEntries(rows.map(([key, items]) => [key.replaceAll("_", " "), items.length])), ["#58a6ff", "#3fb950", "#d29922", "#bc8cff", "#39c5cf"]);
}

function renderExports() {
  const leads = getBatchLeads();
  const exportable = leads.filter(lead => (!lead.suppressed && ["send", "approved"].includes(lead.decision)) || lead.qa_status === "approved");
  document.getElementById("exportSummary").textContent = `${exportable.length} leadow gotowych do CSV w aktywnym batchu. Suppression i reject sa pomijane.`;
  document.getElementById("exportHistory").innerHTML = state.data.exports.map(item =>
    `<div class="event"><div><strong>${item.file}</strong><br><span class="muted">${item.created_at} · ${item.rows} rekordow</span></div><span class="badge ok">${item.status}</span></div>`
  ).join("");
}

function renderBatches() {
  document.getElementById("batchTable").innerHTML = state.data.batches.map(batch => {
    const leads = state.data.leads.filter(lead => lead.batch_id === batch.id);
    const stats = computeStats(leads);
    const progress = Math.round(stats.decided / Math.max(stats.total, 1) * 100);
    return `<tr><td>${batch.name}</td><td>${batch.created_at}</td><td>${badge(batch.status)}</td><td>${stats.total}</td><td>${progress}%</td><td><button class="ghost" data-batch="${batch.id}">Wybierz</button></td></tr>`;
  }).join("");
  document.querySelectorAll("[data-batch]").forEach(button => {
    button.addEventListener("click", () => {
      state.activeBatchId = button.dataset.batch;
      document.getElementById("batchSelect").value = state.activeBatchId;
      render();
    });
  });
}

function exportCsv() {
  const headers = ["company", "domain", "nip", "email", "phone", "campaign", "subject", "evidence_1", "evidence_2", "confidence", "decision"];
  const rows = getBatchLeads()
    .filter(lead => (!lead.suppressed && lead.decision === "send") || lead.qa_status === "approved")
    .map(lead => [lead.company, lead.domain, lead.nip, lead.email, lead.phone, lead.campaign, subjectFor(lead), lead.evidence[0], lead.evidence[1], lead.confidence, lead.decision]);
  const csv = [headers, ...rows].map(row => row.map(csvCell).join(",")).join("\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `${state.activeBatchId}-export.csv`;
  link.click();
  URL.revokeObjectURL(url);
  state.data.exports.unshift({ file: link.download, created_at: new Date().toISOString().slice(0, 16), rows: rows.length, status: "generated" });
  renderExports();
}

function importFeedback(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    const lines = reader.result.split(/\r?\n/).filter(Boolean);
    const headers = lines.shift().split(",").map(item => item.trim());
    let updated = 0;
    lines.forEach(line => {
      const values = parseCsvLine(line);
      const row = Object.fromEntries(headers.map((header, index) => [header, values[index]]));
      const lead = state.data.leads.find(item => item.domain === row.domain || item.email === row.email);
      if (lead) {
        lead.feedback = row.event || row.status || "feedback";
        updated += 1;
      }
    });
    document.getElementById("feedbackResult").textContent = `Zaimportowano feedback dla ${updated} leadow.`;
  };
  reader.readAsText(file);
}

function subjectFor(lead) {
  const name = lead.company.split(" ")[0];
  const map = {
    REDESIGN_OUTDATED: `Pierwsze wrazenie na ${lead.domain}`,
    REDESIGN_ADS_WASTE: `Czy ${lead.domain} wykorzystuje ruch z reklam?`,
    REDESIGN_CONVERSION: `Zapytania ze strony ${name}`,
    REDESIGN_TRUST: `Zaufanie klienta na ${lead.domain}`,
    WORDPRESS_REWORK: `Odswiezenie strony ${lead.domain} bez WordPressa`,
    MOBILE_REBUILD: `Wersja mobilna strony ${lead.domain}`,
    TECH_REBUILD: `Techniczna przebudowa strony ${name}`
  };
  return map[lead.campaign] || `Krotki audyt strony ${name}`;
}

function drawBarChart(id, data, colors) {
  const canvas = document.getElementById(id);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  const cssHeight = Number(canvas.getAttribute("height")) || 220;
  canvas.width = rect.width * dpr;
  canvas.height = cssHeight * dpr;
  canvas.style.height = `${cssHeight}px`;
  ctx.scale(dpr, dpr);
  const width = rect.width;
  const height = cssHeight;
  ctx.clearRect(0, 0, width, height);
  const entries = Object.entries(data);
  const max = Math.max(...entries.map(([, value]) => value), 1);
  const gap = 10;
  const barWidth = Math.max(16, (width - gap * (entries.length + 1)) / entries.length);
  ctx.font = "12px system-ui";
  entries.forEach(([label, value], index) => {
    const x = gap + index * (barWidth + gap);
    const barHeight = (height - 54) * (value / max);
    const y = height - 34 - barHeight;
    ctx.fillStyle = colors[index % colors.length];
    ctx.fillRect(x, y, barWidth, barHeight);
    ctx.fillStyle = "#e6edf3";
    ctx.fillText(String(value), x, y - 6);
    ctx.fillStyle = "#8b949e";
    ctx.save();
    ctx.translate(x, height - 12);
    ctx.rotate(-0.35);
    ctx.fillText(label.slice(0, 16), 0, 0);
    ctx.restore();
  });
}

function group(items, keyFn) {
  return items.reduce((acc, item) => {
    const key = keyFn(item);
    acc[key] = acc[key] || [];
    acc[key].push(item);
    return acc;
  }, {});
}

function groupByDate(leads) {
  return leads.reduce((acc, lead) => {
    acc[lead.decision_date] = (acc[lead.decision_date] || 0) + 1;
    return acc;
  }, {});
}

function contactBuckets(leads) {
  return {
    "0-39": leads.filter(lead => lead.contactability < 40).length,
    "40-69": leads.filter(lead => lead.contactability >= 40 && lead.contactability < 70).length,
    "70-100": leads.filter(lead => lead.contactability >= 70).length
  };
}

function avg(values) {
  return values.length ? values.reduce((sum, value) => sum + Number(value || 0), 0) / values.length : 0;
}

function pct(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function badge(value) {
  const text = String(value || "");
  return `<span class="badge ${statusClass[text] || "info"}">${text}</span>`;
}

function detail(label, value) {
  return `<div class="detail-item"><span>${label}</span><strong>${value}</strong></div>`;
}

function csvCell(value) {
  return `"${String(value || "").replaceAll('"', '""')}"`;
}

function parseCsvLine(line) {
  const values = [];
  let current = "";
  let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (char === '"' && line[index + 1] === '"') {
      current += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      values.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  values.push(current);
  return values;
}
