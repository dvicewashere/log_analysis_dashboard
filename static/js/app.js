var API = "/api";
var panels = document.querySelectorAll(".panel");
var tabs = document.querySelectorAll(".tab");

function setTab(name) {
  for (var i = 0; i < tabs.length; i++) {
    tabs[i].classList.toggle("active", tabs[i].dataset.tab === name);
  }
  for (var j = 0; j < panels.length; j++) {
    panels[j].classList.toggle("active", panels[j].id === name);
  }
  if (name === "alerts") refreshAlerts();
  if (name === "rules") loadRules();
  if (name === "overview") loadLogSources();
  if (name === "export") loadReports();
}

for (var t = 0; t < tabs.length; t++) {
  tabs[t].addEventListener("click", function() { setTab(this.dataset.tab); });
}

function fetchJson(path) {
  return fetch(API + path).then(function(r) {
    if (!r.ok) throw new Error(r.statusText);
    return r.json();
  });
}

function escapeHtml(s) {
  var div = document.createElement("div");
  div.textContent = s;
  return div.innerHTML;
}

function loadLogSources() {
  var el = document.getElementById("log-sources");
  fetchJson("/logs").then(function(sources) {
    var html = "";
    for (var i = 0; i < sources.length; i++) {
      var s = sources[i];
      var durum = (s.exists && s.readable) ? "ok" : "yok";
      html += '<div class="kart"><h3>' + s.id + '</h3><div class="yol">' + s.path + '</div><span class="durum ' + durum + '">' + (s.exists && s.readable ? "Okunabilir" : "Yok") + '</span></div>';
    }
    el.innerHTML = html;
  }).catch(function(e) { el.innerHTML = "<p>Yüklenemedi: " + e.message + "</p>"; });
}

document.getElementById("btn-analyze").addEventListener("click", function() {
  var source = document.getElementById("analyze-source").value;
  var summaryEl = document.getElementById("analyze-summary");
  var alertsEl = document.getElementById("analyze-alerts");
  var sampleEl = document.getElementById("analyze-sample-content");
  summaryEl.textContent = "Analiz ediliyor...";
  alertsEl.innerHTML = "";
  fetchJson("/analyze/" + source).then(function(data) {
    var s = data.summary;
    var ozet = "Kaynak: " + s.source + " | Okunan satır: " + s.total_lines + " | Anlamlı uyarı: " + s.alerts_count;
    if (s.rule_counts && Object.keys(s.rule_counts).length > 0) {
      var parts = [];
      for (var r in s.rule_counts) parts.push(s.rule_counts[r] + "× " + r);
      ozet += " — " + parts.join(", ");
    } else if (s.severity_counts && Object.keys(s.severity_counts).length > 0) {
      ozet += " | Önem: " + JSON.stringify(s.severity_counts);
    }
    summaryEl.textContent = ozet;
    if (data.alerts && data.alerts.length > 0) {
      var ahtml = "<h3>Anlamlı uyarılar (parse edilmiş, kurallarla eşleşen)</h3>";
      for (var i = 0; i < data.alerts.length; i++) {
        var a = data.alerts[i];
        ahtml += '<div class="alert-item ' + a.severity + '"><span>' + escapeHtml(a.rule_name) + '</span> <span>' + a.severity + '</span><div class="log-raw">' + escapeHtml(a.log_raw) + '</div></div>';
      }
      alertsEl.innerHTML = ahtml;
    }
    if (data.sample_entries && data.sample_entries.length > 0) {
      var lines = [];
      for (var k = 0; k < data.sample_entries.length; k++) lines.push(data.sample_entries[k].raw || JSON.stringify(data.sample_entries[k]));
      sampleEl.textContent = lines.join("\n");
    }
  }).catch(function(e) { summaryEl.textContent = "Hata: " + e.message; });
});

function refreshAlerts() {
  var el = document.getElementById("alerts-list");
  fetchJson("/tail/alerts?limit=100").then(function(arr) {
    if (!arr.length) { el.innerHTML = "<p>Henüz uyarı yok.</p>"; return; }
    var html = "";
    for (var i = arr.length - 1; i >= 0; i--) {
      var a = arr[i];
      html += '<div class="alert-item ' + a.severity + '"><span>' + escapeHtml(a.rule_name) + '</span> ' + a.severity + '<div class="log-raw">' + escapeHtml(a.log_raw) + '</div></div>';
    }
    el.innerHTML = html;
  }).catch(function(e) { el.innerHTML = "<p>Yüklenemedi.</p>"; });
}

document.getElementById("btn-refresh-alerts").addEventListener("click", refreshAlerts);

function loadRules() {
  var el = document.getElementById("rules-list");
  fetchJson("/rules").then(function(rules) {
    var html = "";
    for (var i = 0; i < rules.length; i++) {
      var r = rules[i];
      var kaynak = (r.sources && r.sources.length) ? r.sources.join(", ") : "hepsi";
      html += '<div class="rule-item"><div class="name">' + escapeHtml(r.name) + " (" + r.id + ')</div><div class="meta">Önem: ' + r.severity + " | Kaynak: " + kaynak + " | Aktif: " + (r.enabled ? "Evet" : "Hayır") + "</div></div>";
    }
    el.innerHTML = html;
  }).catch(function(e) { el.innerHTML = "<p>Yüklenemedi.</p>"; });
}

function loadReports() {
  var el = document.getElementById("reports-list");
  fetchJson("/reports").then(function(files) {
    if (!files.length) el.innerHTML = "<li>Rapor yok.</li>";
    else {
      var html = "";
      for (var i = 0; i < files.length; i++) html += "<li>" + escapeHtml(files[i].name) + " (" + (files[i].size / 1024).toFixed(1) + " KB)</li>";
      el.innerHTML = html;
    }
  }).catch(function() { el.innerHTML = "<li>Yüklenemedi.</li>"; });
}

var exportBtn = document.getElementById("btn-export");
var exportSource = document.getElementById("export-source");
var exportMax = document.getElementById("export-max");
function updateExportLink() {
  var max = exportMax.value || 5000;
  exportBtn.href = API + "/export/" + exportSource.value + "?max_lines=" + max;
  exportBtn.download = exportSource.value + "_export.csv";
}
exportSource.addEventListener("change", updateExportLink);
exportMax.addEventListener("input", updateExportLink);
updateExportLink();
exportBtn.addEventListener("click", function() {
  document.getElementById("export-status").textContent = "İndiriliyor...";
  setTimeout(function() { document.getElementById("export-status").textContent = ""; }, 2000);
});

var socket = io({ path: "/socket.io", transports: ["websocket", "polling"] });
var unreadAlertsCount = 0;
var alertsTabBtn = document.querySelector('.tab[data-tab="alerts"]');

function updateAlertsBadge() {
  var label = "Uyarılar";
  if (unreadAlertsCount > 0) label += " (" + unreadAlertsCount + ")";
  if (alertsTabBtn) alertsTabBtn.textContent = label;
}

socket.on("alert", function(alert) {
  var panel = document.getElementById("alerts");
  var list = document.getElementById("alerts-list");
  var div = document.createElement("div");
  div.className = "alert-item " + (alert.severity || "");
  div.innerHTML = "<span>" + escapeHtml(alert.rule_name) + "</span> " + (alert.severity || "") + "<div class=\"log-raw\">" + escapeHtml(alert.log_raw || "") + "</div>";
  if (list.firstChild) list.insertBefore(div, list.firstChild);
  else list.appendChild(div);

  if (!panel.classList.contains("active")) {
    unreadAlertsCount++;
    updateAlertsBadge();
    if (typeof Notification !== "undefined" && Notification.permission === "granted") {
      new Notification("Altay uyarı", { body: (alert.rule_name || "") + " – " + (alert.severity || ""), tag: "altay-alert" });
    }
  }
});

var statusEl = document.getElementById("socket-status");
function setSocketStatus(connected) {
  if (!statusEl) return;
  statusEl.textContent = "●";
  statusEl.classList.remove("connected", "disconnected");
  statusEl.classList.add(connected ? "connected" : "disconnected");
  statusEl.title = connected ? "Canlı bağlantı aktif" : "Bağlantı yok";
}

socket.on("connect", function() {
  setSocketStatus(true);
  unreadAlertsCount = 0;
  updateAlertsBadge();
});

socket.on("disconnect", function() {
  setSocketStatus(false);
});

var origSetTab = setTab;
setTab = function(name) {
  origSetTab(name);
  if (name === "alerts") {
    unreadAlertsCount = 0;
    updateAlertsBadge();
  }
};

loadLogSources();
