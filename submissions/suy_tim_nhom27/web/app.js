(() => {
  "use strict";

  const API_BASE = (new URLSearchParams(location.search).get("api") || location.origin).replace(/\/+$/, "");
  const TOKEN_KEY = "hf-demo.access-token";
  const USER_KEY = "hf-demo.username";
  const roleLabels = { doctor: "Bác sĩ", nurse: "Điều dưỡng", pharmacist: "Dược sĩ", admin: "Quản trị", patient: "Bệnh nhân" };
  const moduleLabels = { diagnosis: "Diagnosis", lab_test: "Lab/Test", treatment: "Treatment", medsafety: "MedSafety" };
  const observationLabels = { ef: "Phân suất tống máu", potassium: "Kali", egfr: "eGFR", creatinine: "Creatinin", bnp: "BNP", nt_probnp: "NT-proBNP", systolic_bp: "Huyết áp tâm thu", heart_rate: "Nhịp tim", diastolic_bp: "Huyết áp tâm trương", weight_kg: "Cân nặng", spo2: "SpO₂", temperature_c: "Nhiệt độ", edema: "Phù", fatigue: "Mệt mỏi", dyspnea: "Khó thở", frailty: "Frailty", comorbidity: "Bệnh đồng mắc" };
  const observationUnits = { ef: "%", potassium: "mmol/L", egfr: "mL/min/1.73m2", creatinine: "umol/L", bnp: "pg/mL", nt_probnp: "pg/mL", systolic_bp: "mmHg", heart_rate: "bpm", diastolic_bp: "mmHg", weight_kg: "kg", spo2: "%", temperature_c: "degC" };
  const observationStatuses = { present: "Đã ghi nhận", not_measured: "Chưa đo", unknown: "Chưa rõ" };
  const observationSources = { manual_synthetic: "Nhập thủ công (demo)", mock_his: "HIS (demo)", mock_lis: "LIS (demo)", mock_pacs: "PACS (demo)", mock_emr: "EMR (demo)" };
  const nursingCodes = ["systolic_bp", "diastolic_bp", "heart_rate", "weight_kg", "spo2", "temperature_c", "dyspnea", "edema", "fatigue"];
  const navByRole = {
    doctor: [["overview", "Tổng quan", "grid"], ["cases", "Hồ sơ", "file"], ["encounter", "Lần khám", "timeline"], ["evaluation", "Đánh giá demo", "check"], ["history", "Lịch sử đánh giá", "clock"]],
    nurse: [["overview", "Tổng quan", "grid"], ["cases", "Hồ sơ được phân quyền", "file"], ["encounter", "Lần khám và dữ liệu", "timeline"]],
    pharmacist: [["overview", "Tổng quan", "grid"], ["medsafety", "Rà soát MedSafety", "med"]],
    admin: [["overview", "Tổng quan", "grid"], ["rules", "Quy tắc", "sliders"], ["audit", "Nhật ký", "list"]],
    patient: [["overview", "Tổng quan", "grid"], ["appointments", "Lịch hẹn", "clock"], ["measurements", "Số đo", "timeline"], ["prescriptions", "Đơn thuốc", "file"], ["reminders", "Nhắc nhở", "list"]]
  };
  const viewMeta = {
    overview: ["TỔNG QUAN", "Tổng quan", "Chọn công việc để bắt đầu với dữ liệu synthetic hiện có."],
    cases: ["HỒ SƠ", "Hồ sơ", "Chọn hồ sơ để mở lần khám hoặc xem chi tiết. Chỉ dùng dữ liệu synthetic."],
    encounter: ["LẦN KHÁM", "Lần khám và dữ liệu ghi nhận", "Chọn lần khám để xem hoặc ghi dữ liệu synthetic theo quyền của bạn."],
    evaluation: ["MODULES", "Đánh giá demo", "Mọi module đều ở trạng thái mock_not_evaluated."],
    history: ["LỊCH SỬ", "Lịch sử đánh giá", "API hiện trả lịch sử evaluation, không phải toàn bộ diễn biến lâm sàng."],
    medsafety: ["MEDSAFETY", "Rà soát MedSafety", "Dược sĩ chỉ gọi module MedSafety; trạng thái luôn mock_not_evaluated."],
    rules: ["QUẢN TRỊ", "Quy tắc", "Chỉ quản lý metadata và kiểm tra schema; không có xác nhận lâm sàng."],
    audit: ["NHẬT KÝ", "Nhật ký", "Sự kiện do API trả về cho role admin."],
    appointments: ["LỊCH HẸN", "Lịch hẹn", "Xem lịch hẹn hoặc gửi yêu cầu hẹn trong môi trường synthetic."],
    measurements: ["SỐ ĐO", "Số đo", "Xem và ghi số đo synthetic. Không nhập số đo người bệnh thật."],
    prescriptions: ["ĐƠN THUỐC", "Đơn thuốc", "Xem thuốc, liều và giờ dùng trong đơn synthetic. Đơn thuốc chỉ đọc."],
    reminders: ["NHẮC NHỞ", "Nhắc nhở", "Xem lịch nhắc và ghi nhận đã dùng hoặc bỏ qua."]
  };
  let viewEpoch = 0;
  let pendingAction = null;
  let refreshNotice = "";
  let renderedCaseId = null;
  let renderedEncounterId = null;
  const observationDrafts = new Map();
  const state = {
    token: null, username: null, role: null, view: "overview",
    cases: [], selectedCase: null, currentEncounter: null, pendingCaseId: null, pendingEncounterId: null,
    encounterObservations: [], encounterMedications: [],
    pharmacyEncounterId: "", pharmacyRevision: "", pharmacyMedications: [],
    caseEncounters: [], encounterNotes: [], editingObservation: null,
    patientData: { doctors: [], appointments: [], measurements: [], prescriptions: [], reminders: [] },
    lastEvaluation: null, pendingEvaluationId: null, lastRuleTest: null
  };

  const $ = (selector, root) => (root || document).querySelector(selector);
  const loginView = $("#loginView");
  const appView = $("#appView");
  const loginForm = $("#loginForm");
  const loginRole = $("#loginRole");
  const loginPassword = $("#loginPassword");
  const loginMessage = $("#loginMessage");
  const unsupportedRole = $("#unsupportedRole");
  const roleNav = $("#roleNav");
  const viewContent = $("#viewContent");
  const globalMessage = $("#globalMessage");
  const gatewayStatus = $("#gatewayStatus");
  const scrim = document.createElement("button");

  $("#apiOriginLabel").textContent = API_BASE;
  scrim.type = "button";
  scrim.className = "mobile-scrim";
  scrim.setAttribute("aria-label", "Đóng điều hướng");
  scrim.hidden = true;
  document.body.appendChild(scrim);

  function escapeHTML(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (char) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[char];
    });
  }

  function iconSvg(name) {
    const paths = {
      grid: '<rect x="2.5" y="2.5" width="6" height="6"/><rect x="11.5" y="2.5" width="6" height="6"/><rect x="2.5" y="11.5" width="6" height="6"/><rect x="11.5" y="11.5" width="6" height="6"/>',
      file: '<path d="M5 2.5h7l4 4v11H5z"/><path d="M12 2.5v4h4M8 10h5M8 13h5"/>',
      timeline: '<path d="M4 3v14M4 5h3M4 10h3M4 15h3"/><circle cx="12.5" cy="5" r="1.5"/><circle cx="12.5" cy="10" r="1.5"/><circle cx="12.5" cy="15" r="1.5"/>',
      check: '<circle cx="10" cy="10" r="7"/><path d="m6.5 10 2.3 2.3 4.8-5"/>',
      clock: '<circle cx="10" cy="10" r="7"/><path d="M10 5.5V10l3 2"/>',
      med: '<path d="M6 4a3 3 0 0 1 4.2 0l5.8 5.8a3 3 0 0 1-4.2 4.2L6 8.2A3 3 0 0 1 6 4Z"/><path d="m8 10 4-4"/>',
      sliders: '<path d="M3 5h5M12 5h5M3 10h2M9 10h8M3 15h7M14 15h3"/><circle cx="10" cy="5" r="2"/><circle cx="7" cy="10" r="2"/><circle cx="12" cy="15" r="2"/>',
      list: '<path d="M7 5h10M7 10h10M7 15h10"/><circle cx="3.5" cy="5" r=".7" fill="currentColor"/><circle cx="3.5" cy="10" r=".7" fill="currentColor"/><circle cx="3.5" cy="15" r=".7" fill="currentColor"/>'
    };
    return '<svg viewBox="0 0 20 20" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="square" stroke-linejoin="miter">' + (paths[name] || paths.grid) + "</svg>";
  }

  function setGlobalMessage(message, kind) {
    globalMessage.textContent = message || "";
    globalMessage.className = "global-message" + (kind ? " " + kind : "");
    globalMessage.hidden = !message;
  }

  function showToast(message, isError) {
    const toast = $("#toast");
    toast.textContent = message;
    toast.className = "toast" + (isError ? " error" : "");
    toast.hidden = false;
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(function () { toast.hidden = true; }, 4200);
  }

  function stale(error) { return error && error.stale; }

  function startPending(button) {
    if (!button) return;
    const controls = Array.from(viewContent.querySelectorAll("button, input[type=submit]"));
    pendingAction = { epoch: viewEpoch, saved: false, controls: controls.map(function (control) { return [control, control.disabled]; }), button: button, label: button.textContent };
    controls.forEach(function (control) { control.disabled = true; });
    button.disabled = true;
    const reading = button.form && /load/i.test(button.form.id) || button.dataset.selectCase || button.dataset.selectEncounter || button.id === "exportHistory";
    button.textContent = reading ? "Đang tải…" : button.dataset.testRule ? "Đang kiểm tra…" : "Đang lưu…";
    button.setAttribute("aria-busy", "true");
    viewContent.setAttribute("aria-busy", "true");
    viewContent.querySelectorAll(".form-error").forEach(function (node) { node.textContent = ""; });
    setGlobalMessage("", "");
  }

  function finishPending(button, error) {
    const action = pendingAction;
    if (!action || action.epoch !== viewEpoch) return;
    action.controls.forEach(function (entry) { entry[0].disabled = entry[1]; });
    action.button.textContent = action.label;
    action.button.removeAttribute("aria-busy");
    viewContent.setAttribute("aria-busy", "false");
    if (action.saved || error && error.status === 409) {
      if (action.saved) { action.button.disabled = true; if (action.button.form && action.button.form.id !== "evaluationForm") action.button.form.dataset.saved = "true"; }
      const retry = document.createElement("button");
      retry.type = "button"; retry.className = "button"; retry.textContent = action.saved ? "Tải lại dữ liệu đã lưu" : "Tải phiên bản mới";
      retry.addEventListener("click", function () { setView(state.view, action.saved ? "Đã lưu thành công. Dữ liệu đã được tải lại." : "Đã tải phiên bản mới. Kiểm tra lại dữ liệu trước khi gửi."); });
      action.button.parentElement.appendChild(retry);
    }
    pendingAction = null;
  }

  // Requests belong to the screen/session that started them. A newer navigation
  // invalidates both their DOM writes and state commits, including 401 responses.
  function assertCurrent(epoch, token) {
    if (epoch !== viewEpoch || token !== state.token) throw { stale: true };
  }

  function snapshotForms() {
    return Array.from(viewContent.querySelectorAll("form")).map(function (form) {
      return { id: form.id, context: form.dataset.formContext || "", saved: form.dataset.saved === "true", fields: Array.from(form.elements).filter(function (field) { return field.name && field.type !== "hidden" && !["submit", "button"].includes(field.type); }).map(function (field) { return { name: field.name, value: field.value, checked: field.checked, type: field.type }; }) };
    });
  }

  function restoreForms(snapshot, submittedId) {
    snapshot.forEach(function (saved) {
      if (saved.id === submittedId || saved.saved) return;
      const form = document.getElementById(saved.id);
      if (!form || (form.dataset.formContext || "") !== saved.context) return;
      saved.fields.forEach(function (field) {
        const control = Array.from(form.elements).find(function (item) { return item.name === field.name && (field.type !== "checkbox" || item.value === field.value); });
        if (!control) return;
        if (field.type === "checkbox") control.checked = field.checked;
        else control.value = field.value;
      });
      if (saved.id === "observationForm") {
        setObservationControls();
        saved.fields.forEach(function (field) { const control = form.elements.namedItem(field.name); if (control && ["value", "unit"].includes(field.name)) control.value = field.value; });
      }
    });
  }

  function safeDetail(error) {
    if (error && error.saved) return "Đã lưu thành công, nhưng chưa tải lại được dữ liệu. Dùng Tải lại dữ liệu đã lưu; không gửi lại thao tác. " + safeDetail(Object.assign({}, error, { saved: false }));
    if (!error || !error.status) return "Không kết nối được máy chủ. Kiểm tra kết nối và thử lại.";
    if (error.status === 401) return "Token thiếu, hết hạn hoặc thông tin đăng nhập không hợp lệ.";
    if (error.status === 403) return "Tài khoản không có quyền cho thao tác này.";
    if (error.status === 404) return "API không tìm thấy bản ghi hoặc route được yêu cầu.";
    if (error.status === 409) return error.detail || "Dữ liệu đã thay đổi; tải lại trước khi tiếp tục.";
    if (error.status === 422) return error.detail || "Dữ liệu gửi lên chưa hợp lệ.";
    if (error.status === 429) return error.detail || "Đã thử nhiều lần. Thử lại sau một phút.";
    if (error.status === 503) return error.detail || "Gateway chưa được cấu hình cho demo.";
    return error.detail || "Gateway trả HTTP " + error.status + ".";
  }

  function endSession(message) {
    viewEpoch += 1; pendingAction = null; refreshNotice = ""; observationDrafts.clear();
    state.caseEncounters = []; state.encounterObservations = []; state.encounterMedications = []; state.encounterNotes = [];
    state.editingObservation = null; state.pharmacyEncounterId = ""; state.pharmacyRevision = ""; state.pharmacyMedications = [];
    state.lastRuleTest = null; state.patientData = { doctors: [], appointments: [], measurements: [], prescriptions: [], reminders: [] };
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
    state.token = null; state.username = null; state.role = null;
    state.pendingCaseId = null; state.pendingEncounterId = null; renderedCaseId = null; renderedEncounterId = null;
    state.cases = []; state.selectedCase = null; state.currentEncounter = null; state.lastEvaluation = null; state.pendingEvaluationId = null;
    document.body.classList.remove("nav-open");
    scrim.hidden = true;
    $("#navToggle").setAttribute("aria-expanded", "false");
    appView.hidden = true;
    viewContent.replaceChildren(); viewContent.setAttribute("aria-busy", "false");
    setGlobalMessage("", ""); $("#toast").hidden = true; window.clearTimeout(showToast.timer);
    loginView.hidden = false;
    loginPassword.value = "";
    loginMessage.textContent = message || "";
    loginMessage.className = "form-message";
  }

  async function apiRequest(path, options) {
    const config = options || {};
    const epoch = viewEpoch;
    const token = state.token;
    const action = pendingAction;
    const headers = { Accept: "application/json" };
    if (config.body !== undefined) headers["Content-Type"] = "application/json";
    if (config.auth !== false && state.token) headers.Authorization = "Bearer " + state.token;
    let response;
    try {
      response = await fetch(API_BASE + path, {
        method: config.method || "GET", headers: headers,
        body: config.body === undefined ? undefined : JSON.stringify(config.body),
        cache: "no-store"
      });
    } catch (_) {
      assertCurrent(epoch, token);
      throw { status: 0, detail: "Network error", saved: !!(action && action.saved) };
    }
    let raw;
    try { raw = await response.text(); }
    catch (_) { assertCurrent(epoch, token); throw { status: 0, saved: !!(action && action.saved) }; }
    assertCurrent(epoch, token);
    let payload = null;
    if (raw) {
      try { payload = JSON.parse(raw); }
      catch (_) { throw { status: 502, detail: "Phản hồi máy chủ không hợp lệ. Thử tải lại dữ liệu.", saved: !!(action && action.saved) }; }
    }
    if (!response.ok) {
      const detail = payload && payload.detail;
      const error = { status: response.status, detail: Array.isArray(detail) ? detail.map(function (item) { return (item.loc || []).filter(function (part) { return part !== "body"; }).join(".") + ": " + item.msg; }).join("; ") : detail ? String(detail) : "", saved: !!(action && action.saved) };
      if (response.status === 401 && state.token) endSession(safeDetail(error));
      throw error;
    }
    if (action && config.method && !["GET", "HEAD"].includes(config.method) && !path.startsWith("/api/v1/auth/")) action.saved = true;
    return payload;
  }

  function showUnsupportedRole() {
    unsupportedRole.hidden = true;
    loginPassword.disabled = false;
    $("#loginButton").disabled = false;
  }
  function renderNavigation() {
    const items = navByRole[state.role] || [];
    roleNav.innerHTML = items.map(function (item) {
      return '<button class="nav-item" type="button" data-view="' + escapeHTML(item[0]) + '" aria-current="' +
        (state.view === item[0] ? "page" : "false") + '">' + iconSvg(item[2]) + "<span>" + escapeHTML(item[1]) + "</span></button>";
    }).join("");
    roleNav.querySelectorAll("[data-view]").forEach(function (button) {
      button.addEventListener("click", function () { closeNav(); setView(button.dataset.view); });
    });
  }

  function setHeading(view) {
    const meta = viewMeta[view] || viewMeta.overview;
    $("#viewEyebrow").textContent = meta[0];
    $("#viewTitle").textContent = meta[1];
    $("#viewSubtitle").textContent = meta[2];
    const badges = ['<span class="badge accent">' + escapeHTML(roleLabels[state.role] || "") + "</span>", '<span class="badge">Synthetic API</span>'];
    if (state.selectedCase && state.selectedCase.synthetic_code) badges.push('<span class="badge">' + escapeHTML(state.selectedCase.synthetic_code) + "</span>");
    if (state.currentEncounter && state.currentEncounter.id) badges.push('<span class="badge">Lần khám ' + escapeHTML(formatDate(state.currentEncounter.occurred_at)) + "</span>");
    $("#contextBadges").innerHTML = badges.join("");
  }

  function syncNav() {
    const mobile = window.matchMedia("(max-width: 768px)").matches;
    $("#sidebar").inert = mobile && !document.body.classList.contains("nav-open");
    $("#mainContent").inert = mobile && document.body.classList.contains("nav-open");
  }
  function closeNav(returnFocus) {
    const wasOpen = document.body.classList.contains("nav-open");
    document.body.classList.remove("nav-open");
    scrim.hidden = true;
    $("#navToggle").setAttribute("aria-expanded", "false");
    syncNav();
    if (wasOpen && returnFocus) $("#navToggle").focus();
  }

  async function setView(view, notice) {
    const allowed = (navByRole[state.role] || []).some(function (item) { return item[0] === view; });
    if (!allowed) { setGlobalMessage("Màn hình này chưa được hỗ trợ cho vai trò đang đăng nhập.", "warning"); return; }
    const sameView = state.view === view;
    const sameContext = sameView && renderedCaseId === (state.selectedCase && state.selectedCase.id) && renderedEncounterId === (state.currentEncounter && state.currentEncounter.id);
    const allSnapshots = snapshotForms();
    const snapshot = sameContext ? allSnapshots : [];
    const openSections = sameView ? Array.from(viewContent.querySelectorAll("details[open][id]")).map(function (item) { return item.id; }) : [];
    const submittedId = pendingAction && pendingAction.saved && pendingAction.button.form && pendingAction.button.form.id !== "evaluationForm" ? pendingAction.button.form.id : null;
    const observationSnapshot = allSnapshots.find(function (item) { return item.id === "observationForm"; });
    if (observationSnapshot && observationSnapshot.context.endsWith(":create")) {
      if (observationSnapshot.saved || submittedId === "observationForm") observationDrafts.delete(observationSnapshot.context);
      else observationDrafts.set(observationSnapshot.context, observationSnapshot);
    }
    const saved = !!(pendingAction && pendingAction.saved);
    const priorAction = pendingAction;
    const previousNodes = sameView ? Array.from(viewContent.childNodes) : [];
    const epoch = ++viewEpoch;
    pendingAction = null;
    state.view = view;
    refreshNotice = notice || (saved ? "Đã lưu thành công. Dữ liệu đã được tải lại." : "");
    renderNavigation(); setHeading(view); setGlobalMessage("", "");
    viewContent.setAttribute("aria-busy", "true");
    viewContent.innerHTML = '<div class="loading-line" role="status">Đang tải dữ liệu…</div>';
    if (!sameView) { $("#viewTitle").focus({ preventScroll: true }); }
    try {
      await renderCurrentView();
      if (epoch !== viewEpoch || appView.hidden) return;
      renderedCaseId = state.selectedCase && state.selectedCase.id; renderedEncounterId = state.currentEncounter && state.currentEncounter.id;
      restoreForms(snapshot, submittedId);
      const observationForm = $("#observationForm");
      if (observationForm && observationForm.dataset.formContext.endsWith(":create")) {
        const draft = observationDrafts.get(observationForm.dataset.formContext);
        if (draft) restoreForms([draft], null);
      }
      openSections.forEach(function (id) { const section = document.getElementById(id); if (section) section.open = true; });
      if (refreshNotice) setGlobalMessage(refreshNotice, "success");
      if (state.editingObservation && view === "encounter") {
        const section = $("#observationSection"); if (section) section.open = true;
        const input = $("#obsCode"); if (input) { input.focus(); input.scrollIntoView({ block: "center" }); }
      }
    } catch (error) {
      if (stale(error) || epoch !== viewEpoch || appView.hidden) return;
      const requestedEditing = state.editingObservation;
      setGlobalMessage((saved ? "Đã lưu thành công, nhưng chưa tải lại được dữ liệu. " : "") + safeDetail(error), saved ? "warning" : "error");
      if (sameView && snapshot.length && previousNodes.length) {
        viewContent.replaceChildren.apply(viewContent, previousNodes);
        if (view === "encounter" && observationSnapshot) {
          const previousEditingId = observationSnapshot.context.split(":edit:")[1];
          state.editingObservation = previousEditingId ? state.encounterObservations.find(function (item) { return item.id === previousEditingId; }) || { id: previousEditingId } : null;
        }
        if (priorAction) {
          priorAction.controls.forEach(function (entry) { entry[0].disabled = entry[1]; });
          priorAction.button.textContent = priorAction.label; priorAction.button.removeAttribute("aria-busy");
          if (saved) { priorAction.button.disabled = true; if (priorAction.button.form && priorAction.button.form.id !== "evaluationForm") priorAction.button.form.dataset.saved = "true"; }
        }
        const oldRetry = $("#retryView"); if (oldRetry) oldRetry.remove();
        viewContent.insertAdjacentHTML("afterbegin", '<button class="button" id="retryView" type="button">Tải lại dữ liệu</button>');
      } else {
        viewContent.innerHTML = emptyState("Chưa tải được dữ liệu", "Thử tải lại khi kết nối sẵn sàng.") + '<button class="button" id="retryView" type="button">Tải lại dữ liệu</button>';
      }
      $("#retryView").addEventListener("click", function () { if (view === "encounter") state.editingObservation = requestedEditing; setView(view, saved ? "Đã lưu thành công. Dữ liệu đã được tải lại." : ""); });
    } finally {
      if (epoch === viewEpoch && !appView.hidden) { viewContent.setAttribute("aria-busy", "false"); setHeading(view); }
    }
  }

  async function renderCurrentView() {
    if (state.view === "overview") return renderOverview();
    if (state.view === "cases") return renderCases();
    if (state.view === "encounter") return renderEncounter();
    if (state.view === "evaluation") return renderEvaluation();
    if (state.view === "history") return renderHistory();
    if (state.view === "medsafety") return renderMedSafety();
    if (state.view === "rules") return renderRules();
    if (state.view === "audit") return renderAudit();
    if (["appointments", "measurements", "prescriptions", "reminders"].includes(state.view)) return renderPatientView(state.view);
  }

  function panel(title, description, body, extraClass) {
    return '<article class="panel ' + (extraClass || "") + '"><header class="panel-head"><div><h2>' + escapeHTML(title) + "</h2>" +
      (description ? (/\b(GET|POST|PUT|PATCH|expected_revision)\b/.test(description) ? '<details class="technical-description"><summary>Thông tin kỹ thuật</summary><p>' + escapeHTML(description) + '</p></details>' : "<p>" + escapeHTML(description) + "</p>") : "") + "</div></header><div class=\"panel-body\">" + body + "</div></article>";
  }

  function emptyState(title, text) {
    return '<div class="empty-state"><strong>' + escapeHTML(title) + "</strong>" + escapeHTML(text) + "</div>";
  }

  function formatDate(value, withTime) {
    if (!value) return "Không có thời điểm từ API";
    const date = new Date(value);
    if (!Number.isFinite(date.getTime())) return "Thời điểm API không hợp lệ";
    const options = withTime === false
      ? { year: "numeric", month: "2-digit", day: "2-digit", timeZone: "Asia/Ho_Chi_Minh" }
      : { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", timeZone: "Asia/Ho_Chi_Minh" };
    return new Intl.DateTimeFormat("vi-VN", options).format(date);
  }

  function sexLabel(value) {
    return { male: "Nam", female: "Nữ", unknown: "Chưa rõ" }[value] || String(value || "Không có từ API");
  }

  function setGatewayStatus(data, error) {
    if (error) {
      gatewayStatus.dataset.state = "error";
      gatewayStatus.innerHTML = '<span class="status-dot"></span><span>Chưa kết nối</span>';
      return;
    }
    gatewayStatus.dataset.state = data && data.status === "ok" ? "ok" : "";
    gatewayStatus.innerHTML = '<span class="status-dot"></span><span>' + (data && data.status === "ok" ? "Đã kết nối" : "Chưa xác nhận kết nối") + "</span>";
  }

  async function renderOverview() {
    let health = null;
    let healthError = null;
    try { health = await apiRequest("/health", { auth: false }); }
    catch (error) { if (stale(error)) return; healthError = error; }
    setGatewayStatus(health, healthError);
    let lead = "";
    if (state.role === "doctor" || state.role === "nurse") {
      const cases = await apiRequest("/api/v1/cases");
      state.cases = Array.isArray(cases) ? cases : [];
      const description = state.role === "nurse"
        ? "Hồ sơ theo quyền điều dưỡng do API trả về; chỉ xem và ghi observation/nursing note theo scope."
        : "Hồ sơ được lưu trong cơ sở dữ liệu demo.";
      lead = '<article class="panel half"><div class="panel-body"><div class="stat-row"><div><div class="stat-value">' +
        escapeHTML(state.cases.length) + '</div><div class="stat-label">' + (state.role === "nurse" ? "Hồ sơ trong scope API" : "Hồ sơ trong API hiện tại") + '</div></div><button class="button" type="button" data-open-view="cases">Xem hồ sơ</button></div>' +
        '<div class="stat-meta">' + escapeHTML(description) + '</div></div></article>';
    } else if (state.role === "admin") {
      const rules = await apiRequest("/api/v1/rule-versions");
      const list = Array.isArray(rules) ? rules : [];
      lead = '<article class="panel half"><div class="panel-body"><div class="stat-row"><div><div class="stat-value">' +
        escapeHTML(list.length) + '</div><div class="stat-label">Bản quy tắc do API trả về</div></div><button class="button" type="button" data-open-view="rules">Xem quy tắc</button></div>' +
        '<div class="stat-meta">Role admin không truy cập hồ sơ hoặc dữ liệu lâm sàng.</div></div></article>';
    } else if (state.role === "patient") {
      lead = panel("Cổng bệnh nhân", "Thông tin của tài khoản đang đăng nhập", '<p class="subtle">Dữ liệu chỉ lấy từ các endpoint patient. Đơn thuốc chỉ xem; không sửa đơn, liều hoặc giờ uống.</p><div class="quick-links"><button class="button" type="button" data-open-view="appointments">Lịch hẹn</button><button class="button" type="button" data-open-view="measurements">Số đo</button><button class="button" type="button" data-open-view="prescriptions">Đơn thuốc</button><button class="button" type="button" data-open-view="reminders">Nhắc nhở</button></div>', "half");
    } else {
      lead = panel("MedSafety", "Phạm vi dược sĩ", '<span class="status-label mock">mock_not_evaluated</span><p class="subtle">API không trả cảnh báo thuốc hoặc liều.</p><button class="button" type="button" data-open-view="medsafety">Mở rà soát</button>', "half");
    }
    const healthBody = health
      ? '<dl class="key-value"><div><dt>Trạng thái</dt><dd>' + escapeHTML(health.status || "Không có từ API") +
        '</dd></div><div><dt>Chế độ</dt><dd>' + escapeHTML(health.mode || "Không có từ API") +
        '</dd></div><div><dt>Lưu trữ</dt><dd>' + escapeHTML(health.persistence || "Không có từ API") + "</dd></div></dl>"
      : '<p class="subtle">Không nhận được phản hồi từ /health. Nội dung nghiệp vụ không được thay bằng fixture giả.</p>';
    const sourceBody = '<div class="callout neutral"><div><strong>Nguồn dữ liệu</strong><br>Giao diện chỉ hiển thị response từ Gateway và không bổ sung fixture hoặc kết quả tự dựng.</div></div>';
    viewContent.innerHTML = '<div class="panel-grid">' + lead + '<details class="panel" id="gatewayDetails"><summary>Thông tin kỹ thuật Gateway</summary><div class="panel-body">' + healthBody + "</div></details>" + panel("Giới hạn demo", "Không phải hệ thống chăm sóc", sourceBody) + "</div>";
    viewContent.querySelectorAll("[data-open-view]").forEach(function (button) {
      button.addEventListener("click", function () { setView(button.dataset.openView); });
    });
    if (healthError) setGlobalMessage(safeDetail(healthError), "warning");
  }
  function caseSexOptions(selected) {
    const options = [["", "Chọn trạng thái"], ["female", "Nữ"], ["male", "Nam"], ["unknown", "Chưa rõ"]];
    return options.map(function (entry) {
      return '<option value="' + entry[0] + '"' + (entry[0] === selected ? " selected" : "") + ">" + entry[1] + "</option>";
    }).join("");
  }

  function renderCaseDetail(item, editable) {
    if (!item) return "";
    const head = '<div class="case-detail-head"><div><div class="eyebrow">HỒ SƠ ĐANG CHỌN</div><div class="case-code">' +
      escapeHTML(item.synthetic_code) + '</div><div class="subtle">ID ' + escapeHTML(item.id) + " · revision " + escapeHTML(item.revision) + "</div></div>" +
      '<button class="button" type="button" data-open-view="encounter">Mở lần khám</button></div>';
    if (!editable) return panel("Chi tiết API", "Chỉ đọc trong scope điều dưỡng.", head);
    const body = head +
      '<form id="updateCaseForm" class="inline-form" data-form-context="' + escapeHTML(item.id) + '"><div><label for="editSyntheticCode">Mã synthetic</label><input id="editSyntheticCode" name="synthetic_code" required pattern="SYN-[A-Z0-9-]{1,24}" maxlength="30" value="' + escapeHTML(item.synthetic_code) + '"></div>' +
      '<div><label for="editAge">Tuổi trong bản ghi synthetic</label><input id="editAge" name="age" type="number" min="0" max="120" required value="' + escapeHTML(item.age) + '"></div>' +
      '<div><label for="editSex">Giới tính trong bản ghi</label><select id="editSex" name="sex" required>' + caseSexOptions(item.sex) + "</select></div>" +
      '<input type="hidden" name="expected_revision" value="' + escapeHTML(item.revision) + '">' +
      '<div class="form-actions"><button class="button primary" type="submit">Cập nhật hồ sơ synthetic</button></div><p class="form-error span-all" id="updateCaseError" role="status"></p></form>';
    return panel("Chi tiết API", "Các trường được nạp từ bản ghi đã chọn.", body);
  }

  async function renderCases() {
    const result = await apiRequest("/api/v1/cases");
    state.cases = Array.isArray(result) ? result : [];
    if (state.pendingCaseId) {
      clearEvaluationContext();
      state.selectedCase = state.cases.find(function (item) { return item.id === state.pendingCaseId; }) || null;
      state.pendingCaseId = null; state.currentEncounter = null;
    }
    if (state.selectedCase) {
      const fresh = state.cases.find(function (item) { return item.id === state.selectedCase.id; });
      if (fresh) state.selectedCase = fresh;
      else { clearEvaluationContext(); state.selectedCase = null; state.currentEncounter = null; state.caseEncounters = []; }
    }
    const doctor = state.role === "doctor";
    const rows = state.cases.length
      ? state.cases.map(function (item) {
        return '<div class="case-row' + (state.selectedCase && state.selectedCase.id === item.id ? ' selected' : '') + '" data-case-search="' + escapeHTML((item.synthetic_code + ' ' + item.id).toLowerCase()) + '"><div><div class="case-code">' + escapeHTML(item.synthetic_code) + '</div><div class="row-meta">ID ' + escapeHTML(item.id) + "</div></div>" +
          '<div class="row-meta">' + escapeHTML(item.age) + " tuổi</div><div class=\"row-meta\">" + escapeHTML(sexLabel(item.sex)) + '</div>' +
          '<div class="row-actions"><button class="button" type="button" data-select-case="' + escapeHTML(item.id) + '" data-case-target="encounter">Mở lần khám</button><button class="button quiet" type="button" data-select-case="' + escapeHTML(item.id) + '" data-case-target="cases">Chi tiết</button></div></div>';
      }).join("")
      : emptyState("API trả về danh sách rỗng", doctor ? "Chưa có hồ sơ trong cơ sở dữ liệu demo. Chỉ tạo hồ sơ synthetic." : "Chưa có hồ sơ trong scope do API trả về.");
    const createBody = doctor
      ? '<p class="subtle">Chỉ nhập dữ liệu synthetic. Nếu để trống mã, Gateway sẽ tạo mã synthetic và trả về trong response.</p>' +
        '<form id="createCaseForm" class="inline-form"><div><label for="newAge">Tuổi</label><input id="newAge" name="age" type="number" min="0" max="120" required></div>' +
        '<div><label for="newSex">Giới tính</label><select id="newSex" name="sex" required>' + caseSexOptions("") + '</select></div>' +
        '<div class="span-all"><label for="newSyntheticCode">Mã synthetic (không bắt buộc)</label><input id="newSyntheticCode" name="synthetic_code" pattern="SYN-[A-Z0-9-]{1,24}" maxlength="30"><div class="input-help">Không nhập thông tin định danh cá nhân.</div></div>' +
        '<div class="form-actions"><button class="button primary" type="submit">Tạo hồ sơ</button></div><p class="form-error span-all" id="createCaseError" role="status"></p></form>'
      : '<div class="callout neutral"><div>Điều dưỡng chỉ xem hồ sơ trong scope do API trả về. Không tạo hoặc sửa hồ sơ.</div></div>';
    const filter = '<label for="caseFilter">Tìm mã hồ sơ hoặc ID</label><input id="caseFilter" type="search" placeholder="Nhập mã hoặc ID"><p id="caseCount" class="subtle" role="status">' + state.cases.length + ' hồ sơ</p>';
    viewContent.innerHTML = '<div class="panel-grid">' +
      panel("Danh sách hồ sơ", "Mở lần khám trực tiếp hoặc xem chi tiết hồ sơ.", filter + '<div class="case-list">' + rows + '</div><p id="caseFilterEmpty" class="subtle" hidden>Không có hồ sơ khớp tìm kiếm.</p>') +
      renderCaseDetail(state.selectedCase, doctor) +
      (doctor ? '<details class="panel" id="createCaseSection"' + (state.cases.length ? '' : ' open') + '><summary>Tạo hồ sơ synthetic</summary><div class="panel-body">' + createBody + '</div></details>' : panel("Quyền hồ sơ", "Điều dưỡng", createBody)) + "</div>";
    $("#caseFilter").addEventListener("input", function (event) {
      const query = event.target.value.trim().toLowerCase(); let count = 0;
      viewContent.querySelectorAll("[data-case-search]").forEach(function (row) { row.hidden = !row.dataset.caseSearch.includes(query); if (!row.hidden) count += 1; });
      $("#caseCount").textContent = count + " / " + state.cases.length + " hồ sơ";
      $("#caseFilterEmpty").hidden = count !== 0;
    });

    const createForm = $("#createCaseForm");
    if (createForm) createForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      const form = new FormData(createForm);
      const body = { age: Number(form.get("age")), sex: String(form.get("sex")) };
      const code = String(form.get("synthetic_code") || "").trim();
      if (code) body.synthetic_code = code;
      const button = createForm.querySelector('button[type="submit"]');
      startPending(button);
      try {
        const created = await apiRequest("/api/v1/cases", { method: "POST", body: body });
        state.pendingCaseId = created.id;
        showToast("Đã tạo hồ sơ " + created.synthetic_code + ".");
        setView("cases");
      } catch (error) { if (stale(error)) return;
        $("#createCaseError").textContent = safeDetail(error);
        finishPending(button, error);
      }
    });
    viewContent.querySelectorAll("[data-select-case]").forEach(function (button) {
      button.addEventListener("click", async function () {
        startPending(button);
        try {
          state.selectedCase = await apiRequest("/api/v1/cases/" + encodeURIComponent(button.dataset.selectCase));
          state.currentEncounter = null; state.editingObservation = null; state.pendingEncounterId = null; state.pendingCaseId = null;
          state.caseEncounters = [];
          state.encounterObservations = [];
          state.encounterMedications = [];
          state.encounterNotes = [];
          clearEvaluationContext();
          setView(button.dataset.caseTarget || "encounter");
        } catch (error) { if (stale(error)) return; setGlobalMessage(safeDetail(error), "error"); finishPending(button, error); }
      });
    });
    viewContent.querySelectorAll("[data-open-view]").forEach(function (button) {
      button.addEventListener("click", function () { setView(button.dataset.openView); });
    });
    const updateForm = $("#updateCaseForm");
    if (updateForm) updateForm.addEventListener("submit", updateCase);
  }
  async function updateCase(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = new FormData(form);
    const body = { synthetic_code: String(values.get("synthetic_code")), age: Number(values.get("age")), sex: String(values.get("sex")) };
    const revision = Number(values.get("expected_revision"));
    const button = form.querySelector('button[type="submit"]');
    startPending(button);
    try {
      state.selectedCase = await apiRequest("/api/v1/cases/" + encodeURIComponent(state.selectedCase.id) + "?expected_revision=" + encodeURIComponent(revision), { method: "PUT", body: body });
      showToast("Hồ sơ synthetic đã được cập nhật qua API.");
      setView("cases");
    } catch (error) { if (stale(error)) return;
      $("#updateCaseError").textContent = safeDetail(error);
      finishPending(button, error);
    }
  }

  function datetimePayload(value) {
    const date = new Date(value);
    return value && Number.isFinite(date.getTime()) ? date.toISOString() : null;
  }

  function clearEvaluationContext() {
    state.lastEvaluation = null;
    state.pendingEvaluationId = null;
  }

  async function loadEncounterForRole(id) {
    const encounter = await apiRequest("/api/v1/encounters/" + encodeURIComponent(id));
    const caseData = await apiRequest("/api/v1/cases/" + encodeURIComponent(encounter.case_id));
    const paths = [
      apiRequest("/api/v1/encounters/" + encodeURIComponent(id) + "/observations"),
      apiRequest("/api/v1/encounters/" + encodeURIComponent(id) + "/notes")
    ];
    if (state.role === "doctor") paths.push(apiRequest("/api/v1/encounters/" + encodeURIComponent(id) + "/medications"));
    const results = await Promise.all(paths);
    const sameEncounter = state.currentEncounter && state.currentEncounter.id === encounter.id;
    if (!sameEncounter || !state.selectedCase || state.selectedCase.id !== caseData.id) clearEvaluationContext();
    const editingId = sameEncounter && state.editingObservation && state.editingObservation.id;
    state.editingObservation = editingId && Array.isArray(results[0]) ? results[0].find(function (item) { return item.id === editingId; }) || null : null;
    state.selectedCase = caseData;
    state.currentEncounter = encounter;
    state.encounterObservations = Array.isArray(results[0]) ? results[0] : [];
    state.encounterNotes = Array.isArray(results[1]) ? results[1] : [];
    state.encounterMedications = state.role === "doctor" && Array.isArray(results[2]) ? results[2] : [];
  }
  function valueForObservation(item) {
    if (item.status !== "present") return escapeHTML(observationStatuses[item.status] || item.status || "Chưa có trạng thái");
    const value = item.value === true ? "Có" : item.value === false ? "Không" : item.value;
    return escapeHTML(value) + (item.unit ? " " + escapeHTML(item.unit) : "");
  }

  function timelineMarkup(encounter, observations) {
    const events = [{ time: encounter.occurred_at, title: "Lần khám", details: "ID " + encounter.id }];
    observations.forEach(function (item) {
      events.push({
        time: item.observed_at, title: observationLabels[item.code] || item.code,
        value: valueForObservation(item),
        details: "Trạng thái " + (item.status || "không có") + " · nguồn " + (item.source || "không có") + " · ID " + item.id
      });
    });
    events.sort(function (a, b) {
      const aTime = a.time ? new Date(a.time).getTime() : Number.POSITIVE_INFINITY;
      const bTime = b.time ? new Date(b.time).getTime() : Number.POSITIVE_INFINITY;
      return aTime - bTime;
    });
    return '<div class="timeline">' + events.map(function (item) {
      return '<div class="timeline-item"><div class="timeline-time">' + escapeHTML(formatDate(item.time)) + '</div><div class="timeline-card"><h3>' +
        escapeHTML(item.title) + "</h3>" + (item.value ? '<p class="value-line">' + item.value + "</p>" : "") +
        '<details><summary>Dữ liệu kỹ thuật</summary><p>' + escapeHTML(item.details) + "</p></details></div></div>";
    }).join("") + "</div>";
  }

  function medicationTable(items) {
    if (!items.length) return emptyState("API chưa trả thuốc cho encounter này", "Danh sách rỗng không đồng nghĩa với đánh giá an toàn.");
    return '<div class="data-table-wrap"><table class="data-table"><thead><tr><th>Hoạt chất</th><th>Liều trong bản ghi</th><th>Đường dùng</th><th>Tần suất / ngày</th><th>Loại</th></tr></thead><tbody>' +
      items.map(function (item) {
        return "<tr><td>" + escapeHTML(item.ingredient_code) + "</td><td>" + escapeHTML(item.dose) + " " + escapeHTML(item.dose_unit) +
          "</td><td>" + escapeHTML(item.route) + "</td><td>" + escapeHTML(item.frequency_per_day) + "</td><td>" + escapeHTML(item.kind) + "</td></tr>";
      }).join("") + "</tbody></table></div>";
  }

  function observationFormMarkup() {
    const existing = state.editingObservation;
    const options = Object.keys(observationLabels).filter(function (code) { return state.role !== "nurse" || nursingCodes.includes(code); }).map(function (code) {
      return '<option value="' + escapeHTML(code) + '"' + (existing && existing.code === code ? " selected" : "") + '>' + escapeHTML(observationLabels[code]) + " · " + escapeHTML(code) + "</option>";
    }).join("");
    const selectedStatus = existing ? existing.status : "";
    const selectedSource = existing ? existing.source : "";
    const intro = state.role === "nurse"
      ? "Gateway giới hạn observation theo allowlist điều dưỡng; lỗi validation của API sẽ được hiển thị."
      : "Endpoint chỉ ghi dữ liệu synthetic và không xác nhận y khoa.";
    return '<div class="callout"><div><strong>Chỉ nhập dữ liệu synthetic.</strong><br>' + intro + " Không nhập số đo thật.</div></div>" +
      '<form id="observationForm" class="inline-form" data-form-context="' + escapeHTML(state.currentEncounter.id + (existing ? ':edit:' + existing.id : ':create')) + '"><div><label for="obsCode">Loại dữ liệu</label><select id="obsCode" name="code" required><option value="">Chọn loại</option>' + options + "</select></div>" +
      '<div><label for="obsStatus">Trạng thái</label><select id="obsStatus" name="status" required><option value="">Chọn trạng thái</option>' +
      '<option value="present"' + (selectedStatus === "present" ? " selected" : "") + '>Đã ghi nhận</option><option value="not_measured"' + (selectedStatus === "not_measured" ? " selected" : "") + '>Chưa đo</option><option value="unknown"' + (selectedStatus === "unknown" ? " selected" : "") + '>Chưa rõ</option></select></div>' +
      '<div><label for="obsValue">Giá trị</label><div id="obsValueControl"></div></div>' +
      '<div id="obsUnitGroup" hidden><label for="obsUnit">Đơn vị</label><select id="obsUnit" name="unit" disabled><option value="">Chọn dữ liệu trước</option></select></div>' +
      '<div><label for="obsObservedAt">Thời điểm quan sát</label><input id="obsObservedAt" name="observed_at" type="datetime-local" required value="' + escapeHTML(datetimeLocalValue(existing && existing.observed_at)) + '"><div class="input-help">Chọn thời điểm từ bản ghi synthetic.</div></div>' +
      '<div><label for="obsSource">Nguồn</label><select id="obsSource" name="source" required><option value="">Chọn nguồn</option><option value="manual_synthetic"' + (selectedSource === "manual_synthetic" ? " selected" : "") + '>Nhập thủ công (demo)</option><option value="mock_his"' + (selectedSource === "mock_his" ? " selected" : "") + '>HIS (demo)</option><option value="mock_lis"' + (selectedSource === "mock_lis" ? " selected" : "") + '>LIS (demo)</option><option value="mock_pacs"' + (selectedSource === "mock_pacs" ? " selected" : "") + '>PACS (demo)</option></select></div>' +
      '<div class="form-actions"><button class="button primary" type="submit">' + (existing ? "Cập nhật dữ liệu synthetic" : "Lưu dữ liệu synthetic") + "</button>" +
      (existing ? ' <button class="button" id="cancelObservationEdit" type="button">Hủy sửa</button>' : "") +
      '</div><p class="form-error span-all" id="observationError" role="status"></p></form>';
  }
  function medicationFormMarkup() {
    return '<div class="callout"><div><strong>Chỉ ghi bản ghi thuốc synthetic.</strong><br>Endpoint không tạo đơn thuốc, lịch uống hoặc hướng dẫn điều trị.</div></div>' +
      '<form id="medicationForm" class="inline-form" data-form-context="' + escapeHTML(state.currentEncounter.id) + '"><div class="span-all"><label for="medIngredient">Mã hoạt chất synthetic</label><input id="medIngredient" name="ingredient_code" pattern="[a-z][a-z0-9_]{1,59}" required maxlength="60"></div>' +
      '<div><label for="medDose">Liều trong bản ghi synthetic</label><input id="medDose" name="dose" type="number" min="0.000001" step="any" required></div>' +
      '<div><label for="medDoseUnit">Đơn vị liều</label><select id="medDoseUnit" name="dose_unit" required><option value="">Chọn đơn vị</option><option>mg</option><option>mcg</option><option>g</option><option>mL</option></select></div>' +
      '<div><label for="medRoute">Đường dùng</label><select id="medRoute" name="route" required><option value="">Chọn đường dùng</option><option value="oral">oral</option><option value="iv">iv</option><option value="other">other</option></select></div>' +
      '<div><label for="medFrequency">Tần suất mỗi ngày</label><input id="medFrequency" name="frequency_per_day" type="number" min="1" max="24" required></div>' +
      '<div><label for="medKind">Loại bản ghi</label><select id="medKind" name="kind" required><option value="">Chọn loại</option><option value="current">current</option><option value="proposed">proposed</option></select></div>' +
      '<div class="form-actions"><button class="button primary" type="submit">Lưu bản ghi thuốc synthetic</button></div><p class="form-error span-all" id="medicationError" role="status"></p></form>';
  }

  function datetimeLocalValue(value) {
    if (!value) return "";
    const date = new Date(value);
    if (!Number.isFinite(date.getTime())) return "";
    return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  }

  function notesMarkup(items) {
    if (!items.length) return emptyState("Chưa có ghi chú", "Ghi chú mới sẽ hiển thị ở đây sau khi lưu.");
    return '<div class="record-list">' + items.map(function (item) {
      return '<article class="record-row"><div><strong>' + escapeHTML({ nursing: "Ghi chú điều dưỡng", examination: "Ghi chú khám" }[item.kind] || item.kind || "Ghi chú") + '</strong><div class="row-meta">ID ' +
        escapeHTML(item.id || "Không có từ API") + " · " + escapeHTML(formatDate(item.recorded_at || item.created_at || item.occurred_at)) +
        '</div></div><p class="note-content">' + escapeHTML(item.content || "Không có nội dung từ API") + "</p></article>";
    }).join("") + "</div>";
  }

  function observationTableMarkup(items) {
    if (!items.length) return emptyState("Chưa có dữ liệu ghi nhận", "Thêm dữ liệu synthetic cho lần khám này.");
    return '<div class="data-table-wrap"><table class="data-table"><thead><tr><th>Quan sát</th><th>Giá trị</th><th>Thời điểm</th><th>Nguồn</th>' +
      (state.role === "doctor" ? "<th>Thao tác</th>" : "") + "</tr></thead><tbody>" +
      items.map(function (item) {
        return "<tr><td>" + escapeHTML(observationLabels[item.code] || item.code) + " · " + escapeHTML(observationStatuses[item.status] || item.status) +
          "</td><td>" + valueForObservation(item) + "</td><td>" + escapeHTML(formatDate(item.observed_at)) +
          "</td><td>" + escapeHTML(observationSources[item.source] || item.source || "Chưa có nguồn") + '<details><summary>Dữ liệu kỹ thuật</summary><pre>' + escapeHTML(JSON.stringify(item, null, 2)) + "</pre></details></td>" +
          (state.role === "doctor" ? '<td><button class="button" type="button" data-edit-observation="' + escapeHTML(item.id) + '">Sửa</button></td>' : "") + "</tr>";
      }).join("") + "</tbody></table></div>";
  }

  function nursingNotesPanel() {
    const kind = state.role === "nurse" ? "nursing" : "examination";
    const label = state.role === "nurse" ? "Ghi chú điều dưỡng synthetic" : "Ghi chú khám synthetic";
    const body = '<div class="callout"><div><strong>Chỉ nhập nội dung synthetic.</strong><br>Gateway giới hạn loại note theo role; không nhập thông tin người bệnh thật.</div></div>' +
      '<form id="noteForm" class="inline-form" data-form-context="' + escapeHTML(state.currentEncounter.id) + '"><div class="span-all"><label for="noteContent">' + label + '</label><textarea id="noteContent" name="content" required rows="4"></textarea></div>' +
      '<div class="form-actions"><button class="button primary" type="submit">Lưu ghi chú synthetic</button></div><p class="form-error span-all" id="noteError" role="status"></p></form>';
    return panel("Ghi chú lần khám", "GET/POST /api/v1/encounters/{id}/notes · kind " + kind, notesMarkup(state.encounterNotes) + body);
  }

  async function renderEncounter() {
    const doctor = state.role === "doctor";
    const nurse = state.role === "nurse";
    if ((state.pendingEncounterId || state.currentEncounter) && (doctor || nurse)) { await loadEncounterForRole(state.pendingEncounterId || state.currentEncounter.id); state.pendingEncounterId = null; }
    if (state.selectedCase && (doctor || nurse)) {
      const list = await apiRequest("/api/v1/cases/" + encodeURIComponent(state.selectedCase.id) + "/encounters");
      state.caseEncounters = Array.isArray(list) ? list : [];
    }
    const intro = !state.selectedCase
      ? '<div class="callout neutral"><div>Chọn hồ sơ trong scope trước. <button class="button" type="button" data-open-view="cases">Mở hồ sơ</button></div></div>'
      : "";
    const createBody = doctor
      ? (state.selectedCase
        ? '<p class="subtle">Hồ sơ ' + escapeHTML(state.selectedCase.synthetic_code) + " · revision " + escapeHTML(state.selectedCase.revision) +
          '</p><form id="createEncounterForm" class="inline-form" data-form-context="' + escapeHTML(state.selectedCase.id) + '"><div class="span-all"><label for="encounterDate">Thời điểm lần khám</label><input id="encounterDate" name="occurred_at" type="datetime-local" required><div class="input-help">Chọn thời điểm từ dữ liệu synthetic.</div></div><div class="form-actions"><button class="button primary" type="submit">Tạo lần khám</button></div><p class="form-error span-all" id="encounterCreateError" role="status"></p></form>'
        : '<p class="subtle">Chọn hồ sơ để tạo encounter.</p>')
      : nurse
        ? '<div class="callout neutral"><div>Điều dưỡng chỉ đọc encounter trong scope; không tạo encounter.</div></div>'
        : '<div class="callout neutral"><div>Role này không có màn hình clinical encounter.</div></div>';
    const encounterRows = state.caseEncounters.length
      ? '<div class="record-list">' + state.caseEncounters.map(function (item) {
          return '<div class="record-row"><div><strong>' + escapeHTML(formatDate(item.occurred_at)) + '</strong><div class="row-meta">ID ' + escapeHTML(item.id) +
            '</div></div><button class="button" type="button" data-select-encounter="' + escapeHTML(item.id) + '">Mở</button></div>';
        }).join("") + "</div>"
      : emptyState("API trả về danh sách encounter rỗng", "Không có encounter trong scope của hồ sơ.");
    const knownId = state.currentEncounter ? state.currentEncounter.id : "";
    let detail = "";
    let context = "";
    if (state.currentEncounter && (doctor || nurse)) {
      detail = panel("Dữ liệu ghi nhận", doctor ? "Bác sĩ có thể thêm hoặc sửa dữ liệu synthetic." : "Điều dưỡng ghi dữ liệu theo phạm vi được cấp.", observationTableMarkup(state.encounterObservations) +
          '<details id="observationSection"' + (state.editingObservation ? ' open' : '') + '><summary>' + (state.editingObservation ? 'Sửa dữ liệu ghi nhận' : 'Thêm dữ liệu ghi nhận') + '</summary>' + observationFormMarkup() + '</details>') +
        nursingNotesPanel() + panel("Diễn biến lần khám", "Các thời điểm từ bản ghi synthetic.", timelineMarkup(state.currentEncounter, state.encounterObservations));
      if (doctor) detail += panel("Thuốc theo encounter", "Chỉ dữ liệu do API trả về; không phải hướng dẫn sử dụng.", medicationTable(state.encounterMedications)) +
        panel("Ghi bản ghi thuốc synthetic", "POST /api/v1/encounters/{id}/medications", medicationFormMarkup());
      context = panel("Lần khám đang chọn", "Hồ sơ và thời điểm đang xem", '<dl class="key-value"><div><dt>Hồ sơ</dt><dd>' + escapeHTML(state.selectedCase ? state.selectedCase.synthetic_code : state.currentEncounter.case_id) +
        '</dd></div><div><dt>Thời điểm</dt><dd>' + escapeHTML(formatDate(state.currentEncounter.occurred_at)) + '</dd></div></dl><details><summary>Dữ liệu kỹ thuật</summary><dl class="key-value"><div><dt>Lần khám ID</dt><dd>' + escapeHTML(state.currentEncounter.id) +
        '</dd></div><div><dt>Phiên bản dữ liệu</dt><dd>' + escapeHTML(state.selectedCase && state.selectedCase.revision) + '</dd></div></dl></details>' + (doctor ? '<button class="button" type="button" data-open-view="evaluation">Đánh giá demo lần khám này</button>' : ''));
    }
    const loadBody = '<p class="subtle">Có danh sách encounter theo hồ sơ từ API; có thể mở ID được cấp trực tiếp nếu cần.</p>' +
      '<form id="loadEncounterForm" class="inline-form"><div class="span-all"><label for="knownEncounterId">Lần khám ID</label><input id="knownEncounterId" name="encounter_id" required value="' +
      escapeHTML(knownId) + '"></div><div class="form-actions"><button class="button" type="submit">Tải lần khám</button></div><p class="form-error span-all" id="encounterLoadError" role="status"></p></form>';
    viewContent.innerHTML = intro + '<div class="panel-grid">' + context + detail +
      panel("Các lần khám của hồ sơ", state.selectedCase ? state.selectedCase.synthetic_code : "Chọn hồ sơ trước", encounterRows) +
      (doctor && state.selectedCase ? '<details class="panel" id="createEncounterSection"' + (state.caseEncounters.length ? '' : ' open') + '><summary>Tạo lần khám synthetic</summary><div class="panel-body">' + createBody + '</div></details>' : '') +
      '<details class="panel" id="loadEncounterSection"><summary>Mở bằng ID</summary><div class="panel-body">' + loadBody + '</div></details></div>';
    viewContent.querySelectorAll("[data-open-view]").forEach(function (button) {
      button.addEventListener("click", function () { setView(button.dataset.openView); });
    });
    viewContent.querySelectorAll("[data-select-encounter]").forEach(function (button) {
      button.addEventListener("click", async function () {
        startPending(button);
        try { await loadEncounterForRole(button.dataset.selectEncounter); state.editingObservation = null; setView("encounter"); }
        catch (error) { if (stale(error)) return; setGlobalMessage(safeDetail(error), "error"); finishPending(button, error); }
      });
    });
    viewContent.querySelectorAll("[data-edit-observation]").forEach(function (button) {
      button.addEventListener("click", function () {
        state.editingObservation = state.encounterObservations.find(function (item) { return item.id === button.dataset.editObservation; }) || null;
        setView("encounter");
      });
    });
    const loadForm = $("#loadEncounterForm");
    loadForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      const id = String(new FormData(loadForm).get("encounter_id") || "").trim();
      const button = loadForm.querySelector("button");
      startPending(button);
      try {
        await loadEncounterForRole(id);
        state.editingObservation = null;
        setView("encounter");
      } catch (error) { if (stale(error)) return;
        $("#encounterLoadError").textContent = safeDetail(error);
        finishPending(button, error);
      }
    });
    const createForm = $("#createEncounterForm");
    if (createForm) createForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      const date = datetimePayload(String(new FormData(createForm).get("occurred_at") || ""));
      if (!date) { $("#encounterCreateError").textContent = "Chọn thời điểm hợp lệ từ dữ liệu synthetic."; return; }
      const button = createForm.querySelector("button");
      startPending(button);
      try {
        const path = "/api/v1/cases/" + encodeURIComponent(state.selectedCase.id) + "/encounters?expected_revision=" + encodeURIComponent(state.selectedCase.revision);
        const created = await apiRequest(path, { method: "POST", body: { occurred_at: date } });
        state.pendingEncounterId = created.id;
        await loadEncounterForRole(created.id);
        state.pendingEncounterId = null;
        showToast("Đã tạo lần khám synthetic.");
        setView("encounter");
      } catch (error) { if (stale(error)) return;
        $("#encounterCreateError").textContent = safeDetail(error);
        finishPending(button, error);
      }
    });
    bindObservationForm();
    bindMedicationForm();
    bindNoteForm();
  }
  function setObservationControls() {
    const code = $("#obsCode") ? $("#obsCode").value : "";
    const status = $("#obsStatus") ? $("#obsStatus").value : "";
    const valueControl = $("#obsValueControl");
    const unitSelect = $("#obsUnit");
    const unitGroup = $("#obsUnitGroup");
    if (!valueControl || !unitSelect || !unitGroup) return;
    const present = status === "present";
    const unit = observationUnits[code];
    unitGroup.hidden = !present || !unit;
    unitSelect.disabled = !present || !unit;
    unitSelect.innerHTML = unit
      ? '<option value="">Chọn đơn vị</option><option value="' + escapeHTML(unit) + '">' + escapeHTML(unit) + "</option>"
      : '<option value="">Không áp dụng</option>';
    if (!present || !code) {
      valueControl.innerHTML = '<input name="value" type="text" disabled aria-label="Giá trị không áp dụng">';
    } else if (["dyspnea", "edema", "fatigue"].includes(code)) {
      valueControl.innerHTML = '<select id="obsValue" name="value" required><option value="">Chọn giá trị</option><option value="true">Có</option><option value="false">Không</option></select>';
    } else if (unit) {
      valueControl.innerHTML = '<input id="obsValue" name="value" type="number" step="any" required>';
    } else {
      valueControl.innerHTML = '<input id="obsValue" name="value" type="text" required>';
    }
  }

  function bindObservationForm() {
    const form = $("#observationForm");
    if (!form) return;
    $("#obsCode").addEventListener("change", setObservationControls);
    $("#obsStatus").addEventListener("change", setObservationControls);
    setObservationControls();
    if (state.editingObservation && state.editingObservation.status === "present") {
      const existingValue = $("#obsValue");
      if (existingValue) existingValue.value = String(state.editingObservation.value);
      const existingUnit = $("#obsUnit");
      if (existingUnit && state.editingObservation.unit) existingUnit.value = state.editingObservation.unit;
    }
    const cancel = $("#cancelObservationEdit");
    if (cancel) cancel.addEventListener("click", function () { state.editingObservation = null; setView("encounter"); });
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      if (!state.currentEncounter || !state.selectedCase) return;
      const values = new FormData(form);
      const code = String(values.get("code") || "");
      const status = String(values.get("status") || "");
      const observedAt = datetimePayload(String(values.get("observed_at") || ""));
      let value = null;
      let unit = null;
      if (status === "present") {
        const raw = values.get("value");
        if (raw === null || raw === "") { $("#observationError").textContent = "Nhập giá trị có trong dữ liệu synthetic."; return; }
        value = observationUnits[code] ? Number(raw) : ["dyspnea", "edema", "fatigue"].includes(code) ? raw === "true" : String(raw);
        unit = observationUnits[code] ? String(values.get("unit") || "") : null;
      }
      if (!observedAt) { $("#observationError").textContent = "Chọn thời điểm ghi nhận hợp lệ."; return; }
      const body = { code: code, value: value, unit: unit, status: status, observed_at: observedAt, source: String(values.get("source") || "") };
      const button = form.querySelector('button[type="submit"]');
      startPending(button);
      try {
        const revision = encodeURIComponent(state.selectedCase.revision);
        let path;
        let method;
        if (state.editingObservation) {
          path = "/api/v1/cases/" + encodeURIComponent(state.selectedCase.id) + "/encounters/" +
            encodeURIComponent(state.currentEncounter.id) + "/observations/" + encodeURIComponent(state.editingObservation.id) + "?expected_revision=" + revision;
          method = "PUT";
        } else {
          path = "/api/v1/encounters/" + encodeURIComponent(state.currentEncounter.id) + "/observations?expected_revision=" + revision;
          method = "POST";
        }
        await apiRequest(path, { method: method, body: body });
        state.editingObservation = null;
        await loadEncounterForRole(state.currentEncounter.id);
        showToast("Đã lưu dữ liệu synthetic cho lần khám đang chọn.");
        setView("encounter");
      } catch (error) { if (stale(error)) return;
        $("#observationError").textContent = safeDetail(error);
        finishPending(button, error);
      }
    });
  }

  function bindNoteForm() {
    const form = $("#noteForm");
    if (!form) return;
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      if (!state.currentEncounter || !state.selectedCase) return;
      const content = String(new FormData(form).get("content") || "").trim();
      if (!content) { $("#noteError").textContent = "Nhập nội dung synthetic."; return; }
      const kind = state.role === "nurse" ? "nursing" : "examination";
      const button = form.querySelector("button");
      startPending(button);
      try {
        const path = "/api/v1/encounters/" + encodeURIComponent(state.currentEncounter.id) + "/notes?expected_revision=" + encodeURIComponent(state.selectedCase.revision);
        await apiRequest(path, { method: "POST", body: { kind: kind, content: content } });
        await loadEncounterForRole(state.currentEncounter.id);
        showToast("Đã lưu ghi chú synthetic cho lần khám đang chọn.");
        setView("encounter");
      } catch (error) { if (stale(error)) return;
        $("#noteError").textContent = safeDetail(error);
        finishPending(button, error);
      }
    });
  }
  function bindMedicationForm() {
    const form = $("#medicationForm");
    if (!form) return;
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      if (!state.currentEncounter) return;
      const values = new FormData(form);
      const body = {
        ingredient_code: String(values.get("ingredient_code") || "").trim(),
        dose: Number(values.get("dose")),
        dose_unit: String(values.get("dose_unit") || ""),
        route: String(values.get("route") || ""),
        frequency_per_day: Number(values.get("frequency_per_day")),
        kind: String(values.get("kind") || ""),
        expected_revision: Number(state.selectedCase && state.selectedCase.revision)
      };
      const button = form.querySelector("button");
      startPending(button);
      try {
        await apiRequest("/api/v1/encounters/" + encodeURIComponent(state.currentEncounter.id) + "/medications", { method: "POST", body: body });
        await loadEncounterForRole(state.currentEncounter.id);
        showToast("Bản ghi thuốc synthetic đã được API lưu.");
        setView("encounter");
      } catch (error) { if (stale(error)) return;
        $("#medicationError").textContent = safeDetail(error);
        finishPending(button, error);
      }
    });
  }

  function evaluationFormMarkup(pharmacist) {
    const encounterId = pharmacist ? state.pharmacyEncounterId : (state.currentEncounter ? state.currentEncounter.id : "");
    const revision = pharmacist ? state.pharmacyRevision : (state.selectedCase ? state.selectedCase.revision : "");
    const context = state.role + ":" + (pharmacist ? encounterId : ((state.selectedCase ? state.selectedCase.id : "") + ":" + encounterId));
    const moduleItems = pharmacist ? [["medsafety", "MedSafety"]] : Object.keys(moduleLabels).map(function (key) { return [key, moduleLabels[key]]; });
    const modules = moduleItems.map(function (item) {
      return '<label class="module-option"><input type="checkbox" name="modules" value="' + escapeHTML(item[0]) + '"><span>' + escapeHTML(item[1]) + "</span></label>";
    }).join("");
    const note = pharmacist
      ? '<div class="callout"><div><strong>Giới hạn API:</strong> POST /evaluations yêu cầu expected_revision, nhưng chưa có route pharmacist để đọc revision. Chỉ gửi khi revision đến từ response API được cấp quyền; không tự đoán.</div></div>'
      : '<div class="callout"><div><strong>Chỉ trạng thái stub:</strong> API không trả gợi ý hoặc cảnh báo lâm sàng. Không thể chấp nhận gợi ý hoặc tạo y lệnh từ kết quả này.</div></div>';
    return (!pharmacist && state.currentEncounter ? '<p class="context-strip">Hồ sơ ' + escapeHTML(state.selectedCase && state.selectedCase.synthetic_code) + " · Lần khám " + escapeHTML(formatDate(state.currentEncounter.occurred_at)) + "</p>" : "") + note + '<form id="evaluationForm" class="inline-form" data-form-context="' + escapeHTML(context) + '"><div class="span-all"><label for="evalEncounterId">Lần khám ID</label><input id="evalEncounterId" name="encounter_id" required value="' +
      escapeHTML(encounterId) + '"></div><div><label for="evalRevision">Phiên bản dữ liệu (revision)</label><input id="evalRevision" name="expected_revision" type="number" min="1" required value="' + escapeHTML(revision) + '"></div>' +
      (pharmacist ? '<div class="subtle align-end">Dược sĩ chỉ được gửi module MedSafety.</div>' : '<div class="span-all"><label>Module cần gọi</label><div class="module-grid">' + modules + "</div></div>") +
      '<div class="form-actions"><button class="button primary" type="submit">Gọi evaluation demo</button></div><p class="form-error span-all" id="evaluationError" role="status"></p></form>';
  }

  function evaluationResultMarkup(result) {
    if (!result || result.mode !== "stub" || !Array.isArray(result.results) || result.results.some(function (item) { return item.status !== "mock_not_evaluated"; })) {
      return '<div class="callout"><div><strong>Phản hồi không khớp hợp đồng stub.</strong><br>Không hiển thị nội dung lâm sàng.</div></div>';
    }
    if (!result.results.length) return emptyState("API không trả module", "Không có kết quả để hiển thị.");
    const cards = result.results.map(function (item) {
      const missing = Array.isArray(item.missing_fields) && item.missing_fields.length
        ? '<p class="subtle">Trường module demo báo thiếu: ' + item.missing_fields.map(escapeHTML).join(", ") + "</p>"
        : "";
      return '<article class="module-result"><div class="module-result-head"><strong>' + escapeHTML(moduleLabels[item.module] || item.module) +
        '</strong><span class="status-label mock">mock_not_evaluated</span></div><p>' + escapeHTML(item.message || "Không có thông điệp từ API.") + "</p>" + missing + "</article>";
    }).join("");
    return '<div class="subtle">Evaluation ' + escapeHTML(result.id) + " · " + escapeHTML(formatDate(result.created_at)) +
      " · rule " + escapeHTML(result.rule_version) + '</div><div class="module-results">' + cards + "</div>";
  }

  async function runEvaluation(form, pharmacist) {
    const values = new FormData(form);
    const modules = pharmacist ? ["medsafety"] : Array.from(form.querySelectorAll('input[name="modules"]:checked')).map(function (input) { return input.value; });
    if (!modules.length) { $("#evaluationError").textContent = "Chọn ít nhất một module."; return; }
    const body = {
      encounter_id: String(values.get("encounter_id") || "").trim(),
      expected_revision: Number(values.get("expected_revision")),
      modules: modules
    };
    if (pharmacist && !String(values.get("expected_revision") || "").trim()) {
      $("#evaluationError").textContent = "Chưa có revision được cấp từ API; chưa gửi yêu cầu.";
      return;
    }
    const button = form.querySelector("button");
    startPending(button);
    try {
      const created = await apiRequest("/api/v1/evaluations", { method: "POST", body: body });
      state.pendingEvaluationId = created.id;
      state.lastEvaluation = await apiRequest("/api/v1/evaluations/" + encodeURIComponent(created.id));
      state.pendingEvaluationId = null;
      if (pharmacist) state.pharmacyRevision = String(body.expected_revision);
      showToast("Gateway đã trả evaluation stub.");
      setView(pharmacist ? "medsafety" : "evaluation");
    } catch (error) { if (stale(error)) return;
      $("#evaluationError").textContent = safeDetail(error);
      finishPending(button, error);
    }
  }

  async function renderEvaluation() {
    if (state.pendingEvaluationId) { state.lastEvaluation = await apiRequest("/api/v1/evaluations/" + encodeURIComponent(state.pendingEvaluationId)); state.pendingEvaluationId = null; }
    const resultBody = state.lastEvaluation
      ? evaluationResultMarkup(state.lastEvaluation)
      : emptyState("Chưa có evaluation trong phiên này", "Gọi endpoint demo để nhận trạng thái API; không có kết quả được dựng sẵn.");
    viewContent.innerHTML = '<div class="panel-grid">' +
      panel("Gọi module stub", "POST /api/v1/evaluations", evaluationFormMarkup(false)) +
      panel("Phản hồi API", "Chỉ render status mock_not_evaluated.", resultBody) +
      panel("Decision lâm sàng", "Endpoint decision tồn tại nhưng UI không gửi quyết định cho output stub.", '<div class="callout"><div>Decision bị khóa khi evaluation chưa có đánh giá lâm sàng. Không tạo quyết định hoặc y lệnh giả.</div></div>') +
      "</div>";
    const form = $("#evaluationForm");
    form.addEventListener("submit", function (event) { event.preventDefault(); runEvaluation(form, false); });
  }

  async function renderMedSafety() {
    if (state.pendingEvaluationId) { state.lastEvaluation = await apiRequest("/api/v1/evaluations/" + encodeURIComponent(state.pendingEvaluationId)); state.pendingEvaluationId = null; }
    const medications = state.pharmacyMedications.length
      ? medicationTable(state.pharmacyMedications)
      : emptyState("Chưa tải danh sách thuốc", "Nhập encounter ID được API cấp để gọi GET /medications.");
    const resultBody = state.lastEvaluation
      ? evaluationResultMarkup(state.lastEvaluation)
      : emptyState("Chưa có evaluation trong phiên này", "Không tạo kết quả hoặc cảnh báo ngoài response API.");
    const loadBody = '<form id="pharmacyLoadForm" class="inline-form"><div class="span-all"><label for="pharmacyEncounterId">Lần khám ID</label><input id="pharmacyEncounterId" name="encounter_id" required value="' +
      escapeHTML(state.pharmacyEncounterId) + '"><div class="input-help">Chỉ nhập ID từ response API được cấp quyền.</div></div><div class="form-actions"><button class="button" type="submit">Tải danh sách thuốc</button></div><p class="form-error span-all" id="pharmacyLoadError" role="status"></p></form>';
    viewContent.innerHTML = '<div class="panel-grid">' +
      panel("Tải thuốc theo encounter", "GET /api/v1/encounters/{encounter_id}/medications", loadBody, "half") +
      panel("Thuốc API trả về", "Danh sách rỗng không có nghĩa là thuốc an toàn.", medications, "half") +
      panel("Yêu cầu MedSafety stub", "POST /api/v1/evaluations", evaluationFormMarkup(true)) +
      panel("Phản hồi", "Chỉ status mock_not_evaluated.", resultBody) + "</div>";
    const loadForm = $("#pharmacyLoadForm");
    loadForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      const id = String(new FormData(loadForm).get("encounter_id") || "").trim();
      const button = loadForm.querySelector("button");
      startPending(button);
      try {
        const medications = await apiRequest("/api/v1/encounters/" + encodeURIComponent(id) + "/medications");
        if (state.pharmacyEncounterId !== id) { state.pharmacyRevision = ""; clearEvaluationContext(); }
        state.pharmacyEncounterId = id; state.pharmacyMedications = Array.isArray(medications) ? medications : [];
        setView("medsafety");
      } catch (error) { if (stale(error)) return;
        $("#pharmacyLoadError").textContent = safeDetail(error);
        finishPending(button, error);
      }
    });
    const form = $("#evaluationForm");
    form.addEventListener("submit", function (event) { event.preventDefault(); runEvaluation(form, true); });
  }

  function historyRows(entries) {
    if (!entries.length) return emptyState("API trả về lịch sử rỗng", "Chưa có evaluation cho hồ sơ đang chọn.");
    return '<div class="record-list">' + entries.map(function (entry) {
      const validStatuses = Array.isArray(entry.results) && entry.results.every(function (item) { return item.status === "mock_not_evaluated"; });
      const statuses = validStatuses
        ? entry.results.map(function (item) {
            return '<span class="status-label mock">' + escapeHTML(moduleLabels[item.module] || item.module) + ": mock_not_evaluated</span>";
          }).join(" ")
        : '<span class="status-label">Phản hồi không khớp hợp đồng mock_not_evaluated</span>';
      return '<div class="record-row"><div><div class="case-code">Evaluation ' + escapeHTML(entry.id) + '</div><div class="row-meta">' +
        escapeHTML(formatDate(entry.created_at)) + "</div></div><div class=\"row-meta\">Encounter " + escapeHTML(entry.encounter_id) +
        "<br>Revision " + escapeHTML(entry.input_revision) + "</div><div>" + statuses +
        '<p class="subtle">Decision không hiển thị trong màn hình evaluation stub.</p></div><div class="row-actions"><span class="status-label mock">stub</span></div></div>';
    }).join("") + "</div>";
  }
  async function renderHistory() {
    if (!state.selectedCase) {
      viewContent.innerHTML = '<div class="panel-grid">' + panel("Chưa chọn hồ sơ", "Lịch sử theo case", '<div class="callout neutral"><div>Chọn hồ sơ trước. <button class="button" type="button" data-open-view="cases">Mở hồ sơ</button></div></div>') + "</div>";
      $("[data-open-view]", viewContent).addEventListener("click", function () { setView("cases"); });
      return;
    }
    const result = await apiRequest("/api/v1/cases/" + encodeURIComponent(state.selectedCase.id) + "/history");
    const entries = Array.isArray(result) ? result : [];
    const top = '<div class="section-title"><h2>' + escapeHTML(state.selectedCase.synthetic_code) +
      '</h2><div><button class="button" type="button" id="refreshHistory">Tải lại</button> <button class="button" type="button" id="exportHistory">Xuất JSON</button></div></div>';
    viewContent.innerHTML = top + '<div class="panel-grid">' + panel("Lịch sử evaluation", "GET /api/v1/cases/{case_id}/history · " + entries.length + " bản ghi", historyRows(entries)) + "</div>";
    $("#refreshHistory").addEventListener("click", function () { setView("history"); });
    $("#exportHistory").addEventListener("click", async function (event) {
      const button = event.currentTarget; startPending(button);
      try {
        const data = await apiRequest("/api/v1/cases/" + encodeURIComponent(state.selectedCase.id) + "/export");
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "synthetic-export-" + String(state.selectedCase.synthetic_code || "case") + ".json";
        link.click();
        URL.revokeObjectURL(url);
        showToast("Đã xuất lịch sử hồ sơ " + state.selectedCase.synthetic_code + ".");
        finishPending(button);
      } catch (error) { if (stale(error)) return; setGlobalMessage(safeDetail(error), "error"); finishPending(button, error); }
    });
  }

  async function renderRules() {
    const result = await apiRequest("/api/v1/rule-versions");
    const rules = Array.isArray(result) ? result : [];
    const rows = rules.length ? rules.map(function (rule) {
      return '<div class="rule-card"><div><div class="case-code">' + escapeHTML(rule.code) + " · v" + escapeHTML(rule.version) +
        '</div><div class="row-meta">Module ' + escapeHTML(rule.module) + " · trạng thái " + escapeHTML(rule.status) +
        " · kiểm tra " + escapeHTML(rule.test_status) + "</div><div class=\"subtle\">Nguồn: " + escapeHTML(rule.source_ref) +
        " · approval_ref: " + escapeHTML(rule.approval_ref || "không có từ API") + "</div></div><div class=\"rule-actions\">" +
        '<button class="button" type="button" data-test-rule="' + escapeHTML(rule.id) + '">Kiểm tra schema</button>' +
        '<button class="button" type="button" data-activate-rule="' + escapeHTML(rule.id) + '">Thử kích hoạt</button></div></div>';
    }).join("") : emptyState("API trả về danh sách quy tắc rỗng", "Không có quy tắc mẫu được dựng sẵn.");
    const formBody = '<div class="callout"><div><strong>Metadata stub giới hạn.</strong><br>API chỉ lưu mã/module/source_ref, không lưu logic lâm sàng. Chỉ tạo draft synthetic có nguồn tham chiếu; không nhập quy tắc y khoa.</div></div>' +
      '<form id="ruleForm" class="inline-form"><div><label for="ruleCode">Mã phiên bản</label><input id="ruleCode" name="code" pattern="[A-Z][A-Z0-9_-]{2,50}" required maxlength="51"></div>' +
      '<div><label for="ruleModule">Module</label><select id="ruleModule" name="module" required><option value="">Chọn module</option><option value="diagnosis">diagnosis</option><option value="lab_test">lab_test</option><option value="treatment">treatment</option><option value="medsafety">medsafety</option></select></div>' +
      '<div class="span-all"><label for="ruleSource">Nguồn tham chiếu</label><input id="ruleSource" name="source_ref" maxlength="300" required></div>' +
      '<div class="form-actions"><button class="button primary" type="submit">Tạo draft metadata</button></div><p class="form-error span-all" id="ruleError" role="status"></p></form>';
    viewContent.innerHTML = '<div class="panel-grid">' + panel("Tạo draft metadata", "POST /api/v1/rule-versions", formBody, "half") +
      panel("Danh sách từ API", "GET /api/v1/rule-versions · " + rules.length + " bản ghi", '<div class="record-list">' + rows + "</div>") +
      (state.lastRuleTest ? panel("Kết quả test", "Chỉ kiểm tra schema", '<div class="callout"><div>result: ' + escapeHTML(state.lastRuleTest.result) +
        " · clinical_validation: " + escapeHTML(state.lastRuleTest.clinical_validation) + "</div></div>") : "") + "</div>";
    $("#ruleForm").addEventListener("submit", async function (event) {
      event.preventDefault();
      const form = event.currentTarget;
      const values = new FormData(form);
      const body = { code: String(values.get("code") || "").trim(), module: String(values.get("module") || ""), source_ref: String(values.get("source_ref") || "").trim() };
      const button = form.querySelector("button");
      startPending(button);
      try {
        await apiRequest("/api/v1/rule-versions", { method: "POST", body: body });
        showToast("Draft metadata đã được API tạo.");
        setView("rules");
      } catch (error) { if (stale(error)) return; $("#ruleError").textContent = safeDetail(error); finishPending(button, error); }
    });
    viewContent.querySelectorAll("[data-test-rule]").forEach(function (button) {
      button.addEventListener("click", async function () {
        startPending(button);
        try {
          state.lastRuleTest = await apiRequest("/api/v1/rule-versions/" + encodeURIComponent(button.dataset.testRule) + "/test", { method: "POST" });
          showToast("API chỉ xác nhận kiểm tra schema.");
          setView("rules");
        } catch (error) { if (stale(error)) return; setGlobalMessage(safeDetail(error), "error"); finishPending(button, error); }
      });
    });
    viewContent.querySelectorAll("[data-activate-rule]").forEach(function (button) {
      button.addEventListener("click", async function () {
        startPending(button);
        try {
          await apiRequest("/api/v1/rule-versions/" + encodeURIComponent(button.dataset.activateRule) + "/activate", { method: "POST" });
          setView("rules", "Đã xử lý yêu cầu kích hoạt. Trạng thái quy tắc đã được tải lại từ API.");
        } catch (error) { if (stale(error)) return;
          setGlobalMessage(safeDetail(error), error.status === 409 ? "warning" : "error");
          finishPending(button, error);
        }
      });
    });
  }

  async function renderAudit() {
    const result = await apiRequest("/api/v1/audit-events");
    const events = Array.isArray(result) ? result : [];
    const body = events.length
      ? '<div class="data-table-wrap"><table class="data-table"><thead><tr><th>Thời điểm</th><th>Actor ID</th><th>Hành động</th><th>Entity ID</th></tr></thead><tbody>' +
        events.map(function (item) {
          return "<tr><td>" + escapeHTML(formatDate(item.created_at)) + "</td><td>" + escapeHTML(item.actor_id) +
            "</td><td>" + escapeHTML(item.action) + "</td><td>" + escapeHTML(item.entity_id) + "</td></tr>";
        }).join("") + "</tbody></table></div>"
      : emptyState("API trả về nhật ký rỗng", "Chưa có sự kiện trong cơ sở dữ liệu demo.");
    viewContent.innerHTML = '<div class="panel-grid">' + panel("Audit events", "GET /api/v1/audit-events · " + events.length + " bản ghi", body) + "</div>";
  }

  function apiValueText(value) {
    if (value === null || value === undefined) return "null";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
  }

  function patientStatus(value) {
    return { requested: "Chờ xác nhận", confirmed: "Đã xác nhận", completed: "Đã hoàn tất", cancelled: "Đã hủy", pending: "Chưa phản hồi", taken: "Đã dùng", skipped: "Đã bỏ qua" }[value] || String(value || "Chưa có trạng thái");
  }
  function patientRecordsTable(items, action, kind) {
    if (!items.length) return emptyState("Chưa có bản ghi", "Dữ liệu sẽ xuất hiện ở đây sau khi được lưu.");
    const text = function (value) { return escapeHTML(value == null || value === "" ? "—" : value); };
    const quantity = function (value, unit) { return value == null ? "—" : text(value) + " " + text(unit); };
    const doctorName = function (id) { const doctor = state.patientData.doctors.find(function (item) { return item.doctor_id === id; }); return text(doctor ? doctor.label : "Bác sĩ (xem ID trong chi tiết)"); };
    const schemas = {
      doctors: [["Bác sĩ", function (i) { return text(i.label); }], ["Khoa", function (i) { return text(i.department_name); }]],
      appointments: [["Thời điểm", function (i) { return text(formatDate(i.slot_at)); }], ["Bác sĩ", function (i) { return doctorName(i.doctor_id); }], ["Lý do", function (i) { return text(i.reason); }], ["Trạng thái", function (i) { return text(patientStatus(i.status)); }]],
      measurements: [["Thời điểm", function (i) { return text(formatDate(i.observed_at)); }], ["Huyết áp", function (i) { return i.systolic_bp == null ? "—" : text(i.systolic_bp) + "/" + quantity(i.diastolic_bp, "mmHg"); }], ["Nhịp tim", function (i) { return quantity(i.heart_rate, "bpm"); }], ["Cân nặng", function (i) { return quantity(i.weight_kg, "kg"); }], ["SpO₂", function (i) { return quantity(i.spo2, "%"); }], ["Nhiệt độ", function (i) { return quantity(i.temperature_c, "°C"); }], ["Triệu chứng", function (i) { return text(i.symptoms); }]],
      prescriptions: [["Thuốc", function (i) { return text(i.drug_product || i.ingredient); }], ["Liều", function (i) { return quantity(i.dose, i.dose_unit); }], ["Đường dùng", function (i) { return text({oral: "Uống", iv: "Tĩnh mạch", other: "Khác"}[i.route] || i.route); }], ["Lịch trong đơn", function (i) { return text(i.frequency_per_day) + " lần/ngày · " + text((i.dose_times || []).map(function (time) { return time.slice(0,5); }).join(", ")) + "<br>" + text(i.starts_on) + " → " + text(i.ends_on); }], ["Hướng dẫn trong đơn", function (i) { return text(i.instructions) + "<br>" + text(i.prescription_instructions); }], ["Trạng thái", function (i) { return text(patientStatus(i.status)); }]],
      reminders: [["Thời điểm", function (i) { return text(formatDate(i.due_at)); }], ["Thuốc / liều", function (i) { return text(i.ingredient) + " · " + quantity(i.dose, i.dose_unit); }], ["Hướng dẫn trong bản ghi", function (i) { return text(i.dose_instructions || i.instructions); }], ["Trạng thái", function (i) { return text(patientStatus(i.status)) + (i.responded_at ? "<br>" + text(formatDate(i.responded_at)) : ""); }]]
    };
    const columns = schemas[kind || state.view] || [];
    return '<div class="data-table-wrap"><table class="data-table patient-table"><thead><tr>' + columns.map(function (column) { return "<th>" + text(column[0]) + "</th>"; }).join("") + '<th>Chi tiết</th>' + (action ? '<th>Thao tác</th>' : '') + '</tr></thead><tbody>' + items.map(function (item) {
      return '<tr>' + columns.map(function (column) { return '<td data-label="' + text(column[0]) + '">' + column[1](item) + '</td>'; }).join('') + '<td data-label="Chi tiết"><details><summary>Dữ liệu kỹ thuật</summary><pre>' + escapeHTML(JSON.stringify(item, null, 2)) + '</pre></details></td>' + (action ? '<td data-label="Thao tác"><div class="row-actions">' + action(item) + '</div></td>' : '') + '</tr>';
    }).join('') + '</tbody></table></div>';
  }

  function patientCollectionPath(view) {
    return "/api/v1/patient/" + view;
  }

  async function renderPatientView(view) {
    const items = await apiRequest(patientCollectionPath(view));
    state.patientData[view] = Array.isArray(items) ? items : [];
    let extra = "";
    let actions = null;
    if (view === "appointments") {
      const doctors = await apiRequest("/api/v1/patient/doctors");
      state.patientData.doctors = Array.isArray(doctors) ? doctors : [];
      const doctorOptions = state.patientData.doctors.map(function (doctor) {
        const id = doctor.id || doctor.doctor_id;
        if (!id) return "";
        const name = doctor.display_name || doctor.name || doctor.label || id;
        return '<option value="' + escapeHTML(id) + '">' + escapeHTML(name) + "</option>";
      }).join("");
      const form = '<div class="callout"><div><strong>Dữ liệu synthetic.</strong><br>Không nhập thông tin cá nhân hoặc nội dung chăm sóc thật. Gateway kiểm tra slot trống, thời lượng và thời gian.</div></div>' +
        '<form id="appointmentForm" class="inline-form"><div><label for="appointmentDoctor">Bác sĩ từ API</label><select id="appointmentDoctor" name="doctor_id" required><option value="">Chọn bác sĩ</option>' + doctorOptions + '</select></div>' +
        '<div><label for="appointmentSlot">Thời điểm</label><input id="appointmentSlot" name="slot_at" type="datetime-local" required></div>' +
        '<div class="span-all"><label for="appointmentReason">Lý do synthetic</label><input id="appointmentReason" name="reason" maxlength="500" required></div>' +
        '<div class="form-actions"><button class="button primary" type="submit"' + (doctorOptions ? "" : " disabled") + '>Đặt lịch synthetic</button></div><p class="form-error span-all" id="appointmentError" role="status"></p></form>';
      extra = panel("Đặt lịch", "POST /api/v1/patient/appointments", form, "half") +
        panel("Bác sĩ do API trả về", "GET /api/v1/patient/doctors", patientRecordsTable(state.patientData.doctors, null, "doctors"), "half");
      actions = function (item) {
        const id = item.id || item.appointment_id;
        return id && ["requested", "confirmed"].includes(item.status) ? '<button class="button" type="button" data-cancel-appointment="' + escapeHTML(id) + '">Hủy lịch</button>' : escapeHTML(patientStatus(item.status));
      };
    } else if (view === "measurements") {
      const form = '<div class="callout"><div><strong>Chỉ nhập số đo synthetic.</strong><br>Không dùng form này để ghi số đo thật. Huyết áp cần nhập cả cặp tâm thu và tâm trương.</div></div>' +
        '<form id="measurementForm" class="inline-form"><div class="span-all"><label for="measurementAt">Thời điểm ghi nhận</label><input id="measurementAt" name="observed_at" type="datetime-local" required></div>' +
        '<div><label for="measurementSystolic">Huyết áp tâm thu</label><input id="measurementSystolic" name="systolic_bp" type="number" step="any"></div>' +
        '<div><label for="measurementDiastolic">Huyết áp tâm trương</label><input id="measurementDiastolic" name="diastolic_bp" type="number" step="any"></div>' +
        '<div><label for="measurementHeartRate">Nhịp tim</label><input id="measurementHeartRate" name="heart_rate" type="number" step="any"></div>' +
        '<div><label for="measurementWeight">Cân nặng (kg)</label><input id="measurementWeight" name="weight_kg" type="number" step="any"></div>' +
        '<div><label for="measurementSpo2">SpO₂ (%)</label><input id="measurementSpo2" name="spo2" type="number" min="0" max="100" step="any"></div>' +
        '<div><label for="measurementTemperature">Nhiệt độ (°C)</label><input id="measurementTemperature" name="temperature_c" type="number" step="any"></div>' +
        '<div class="span-all"><label for="measurementSymptoms">Triệu chứng synthetic (không bắt buộc)</label><textarea id="measurementSymptoms" name="symptoms" maxlength="500" rows="3"></textarea></div>' +
        '<div class="form-actions"><button class="button primary" type="submit">Ghi số đo synthetic</button></div><p class="form-error span-all" id="measurementError" role="status"></p></form>';
      extra = panel("Ghi số đo synthetic", "POST /api/v1/patient/measurements", form, "half");
    } else if (view === "prescriptions") {
      extra = panel("Quyền bệnh nhân", "Chỉ đọc", '<div class="callout neutral"><div>Bệnh nhân không sửa đơn, liều hoặc giờ uống. Không có thao tác thay đổi trong màn hình này.</div></div>', "half");
    } else if (view === "reminders") {
      actions = function (item) {
        const id = item.id || item.reminder_id;
        return id && item.status === "pending" ? '<button class="button" type="button" data-reminder-id="' + escapeHTML(id) + '" data-reminder-status="taken">Đã dùng</button> <button class="button" type="button" data-reminder-id="' + escapeHTML(id) + '" data-reminder-status="skipped">Bỏ qua</button>' : escapeHTML(patientStatus(item.status));
      };
    }
    const title = view === "appointments" ? "Lịch hẹn" : view === "measurements" ? "Số đo" : view === "prescriptions" ? "Đơn thuốc" : "Nhắc nhở";
    const route = patientCollectionPath(view);
    viewContent.innerHTML = '<div class="panel-grid">' + extra +
      panel(view === "reminders" ? "Lịch nhắc dùng thuốc" : title, state.patientData[view].length + " bản ghi",
        patientRecordsTable(state.patientData[view], actions)) + "</div>";
    bindPatientActions(view);
  }

  function bindPatientActions(view) {
    const appointmentForm = $("#appointmentForm");
    if (appointmentForm) appointmentForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      const values = new FormData(appointmentForm);
      const slotAt = datetimePayload(String(values.get("slot_at") || ""));
      if (!slotAt) { $("#appointmentError").textContent = "Chọn thời điểm hợp lệ."; return; }
      const reason = String(values.get("reason") || "").trim();
      if (!reason) { $("#appointmentError").textContent = "Nhập lý do synthetic không để trống."; return; }
      const body = { doctor_id: String(values.get("doctor_id") || ""), slot_at: slotAt, reason: reason };
      const button = appointmentForm.querySelector("button[type=submit]");
      startPending(button);
      try {
        await apiRequest("/api/v1/patient/appointments", { method: "POST", body: body });
        showToast("Yêu cầu lịch hẹn đã được API xử lý.");
        setView(view);
      } catch (error) { if (stale(error)) return; $("#appointmentError").textContent = safeDetail(error); finishPending(button, error); }
    });
    const measurementForm = $("#measurementForm");
    if (measurementForm) measurementForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      const values = new FormData(measurementForm);
      const systolicRaw = String(values.get("systolic_bp") || "").trim();
      const diastolicRaw = String(values.get("diastolic_bp") || "").trim();
      if (Boolean(systolicRaw) !== Boolean(diastolicRaw)) { $("#measurementError").textContent = "Nhập cả hai giá trị huyết áp hoặc để trống cả hai."; return; }
      const observedAt = datetimePayload(String(values.get("observed_at") || ""));
      if (!observedAt) { $("#measurementError").textContent = "Chọn thời điểm hợp lệ."; return; }
      const body = { observed_at: observedAt };
      ["systolic_bp", "diastolic_bp", "heart_rate", "weight_kg", "spo2", "temperature_c"].forEach(function (field) {
        const raw = String(values.get(field) || "").trim();
        if (raw !== "") body[field] = Number(raw);
      });
      const symptoms = String(values.get("symptoms") || "").trim();
      if (symptoms) body.symptoms = symptoms;
      if (Object.keys(body).length === 1) { $("#measurementError").textContent = "Nhập ít nhất một số đo synthetic."; return; }
      const button = measurementForm.querySelector("button[type=submit]");
      startPending(button);
      try {
        await apiRequest("/api/v1/patient/measurements", { method: "POST", body: body });
        showToast("Số đo synthetic đã được API lưu.");
        setView(view);
      } catch (error) { if (stale(error)) return; $("#measurementError").textContent = safeDetail(error); finishPending(button, error); }
    });
    viewContent.querySelectorAll("[data-cancel-appointment]").forEach(function (button) {
      button.addEventListener("click", async function () {
        startPending(button);
        try {
          await apiRequest("/api/v1/patient/appointments/" + encodeURIComponent(button.dataset.cancelAppointment) + "/cancel", { method: "POST" });
          showToast("API đã xử lý yêu cầu hủy lịch.");
          setView(view);
        } catch (error) { if (stale(error)) return; setGlobalMessage(safeDetail(error), error.status === 409 ? "warning" : "error"); finishPending(button, error); }
      });
    });
    viewContent.querySelectorAll("[data-reminder-id]").forEach(function (button) {
      button.addEventListener("click", async function () {
        const id = button.dataset.reminderId;
        const status = button.dataset.reminderStatus;
        startPending(button);
        try {
          await apiRequest("/api/v1/patient/reminders/" + encodeURIComponent(id), { method: "PATCH", body: { status: status } });
          showToast("Trạng thái nhắc nhở đã được API cập nhật.");
          setView(view);
        } catch (error) { if (stale(error)) return;
          setGlobalMessage(safeDetail(error), error.status === 409 ? "warning" : "error");
          finishPending(button, error);
        }
      });
    });
  }
  function showApp() {
    loginView.hidden = true;
    appView.hidden = false; appView.inert = false;
    $("#userLabel").textContent = state.username || "";
    $("#roleLabel").textContent = roleLabels[state.role] || "";
    $("#userInitial").textContent = (state.username || "U").slice(0, 1).toUpperCase();
    closeNav(); renderNavigation();
    setView("overview");
  }

  let loginPending = false;
  async function submitLogin(event) {
    event.preventDefault();
    if (loginPending) return;
    if (!loginForm.reportValidity()) return;
    loginPending = true;
    loginMessage.textContent = ""; loginMessage.className = "form-message";
    const username = loginRole.value.trim();
    const button = $("#loginButton");
    button.disabled = true;
    loginRole.disabled = true;
    button.querySelector("span").textContent = "Đang đăng nhập";
    try {
      const result = await apiRequest("/api/v1/auth/token", {
        method: "POST", auth: false,
        body: { username: username, password: loginPassword.value }
      });
      if (!result || !result.access_token) throw { status: 0, detail: "Token không có trong response API." };
      state.token = result.access_token;
      state.username = username;
      const actor = await apiRequest("/api/v1/auth/me");
      if (!actor || !navByRole[actor.role]) throw { status: 403, detail: "Vai trò tài khoản chưa được hỗ trợ." };
      state.role = actor.role;
      state.username = actor.username;
      sessionStorage.setItem(TOKEN_KEY, result.access_token);
      sessionStorage.setItem(USER_KEY, actor.username);
      loginPassword.value = "";
      showApp();
    } catch (error) { if (stale(error)) return;
      if (state.token) endSession(safeDetail(error));
      loginMessage.textContent = safeDetail(error);
    } finally {
      loginPending = false; loginRole.disabled = false;
      button.disabled = false;
      button.querySelector("span").textContent = "Đăng nhập";
    }
  }

  $("#demoAccount").addEventListener("change", function (event) { if (event.target.value) { loginRole.value = event.target.value; loginPassword.focus(); } });
  let registrationPending = false;
  function registrationMode(open) {
    viewEpoch += 1;
    document.body.classList.toggle("registration-open", open);
    $("#authFolio").textContent = open ? "ĐĂNG KÝ BỆNH NHÂN" : "ĐĂNG NHẬP";
    $("#authTitle").textContent = open ? "Đăng ký bệnh nhân" : "Đăng nhập";
    $("#authSubtitle").textContent = open ? "Tạo tài khoản bệnh nhân với hồ sơ synthetic mới." : "Đăng nhập bằng tài khoản của bạn hoặc tài khoản demo.";
    $("#registrationView").hidden = !open;
    loginForm.hidden = open; $("#showRegister").hidden = open;
    $("#registerPassword").value = ""; $("#registerConfirm").value = "";
    if (open) { $("#authTitle").focus({ preventScroll: true }); window.scrollTo({ top: 0 }); }
    else loginRole.focus({ preventScroll: true });
  }
  $("#showRegister").addEventListener("click", function () { registrationMode(true); });
  $("#backToLogin").addEventListener("click", function () { registrationMode(false); });
  $("#registrationForm").addEventListener("input", function () { if (!registrationPending) { $("#registrationMessage").textContent = ""; $("#registerConfirm").removeAttribute("aria-invalid"); } });
  $("#registrationForm").addEventListener("submit", async function (event) {
    event.preventDefault();
    if (registrationPending) return;
    const form = event.currentTarget; if (!form.reportValidity()) return;
    const message = $("#registrationMessage"); message.textContent = "";
    const password = $("#registerPassword").value;
    if (password !== $("#registerConfirm").value) { message.textContent = "Mật khẩu nhập lại chưa khớp."; $("#registerConfirm").setAttribute("aria-invalid", "true"); $("#registerConfirm").focus(); return; }
    if (!password.trim()) { message.textContent = "Mật khẩu không được chỉ gồm khoảng trắng."; return; }
    const username = $("#registerUsername").value.trim();
    registrationPending = true;
    const button = $("#registerButton"); button.disabled = true; button.textContent = "Đang đăng ký…";
    $("#backToLogin").disabled = true;
    try {
      const result = await apiRequest("/api/v1/auth/register", { method: "POST", auth: false, body: { username: username, password: password, age: Number($("#registerAge").value), sex: $("#registerSex").value } });
      form.reset(); loginRole.value = result.username; loginPassword.value = "";
      registrationMode(false);
      loginMessage.textContent = "Đã đăng ký tài khoản bệnh nhân " + result.username + ". Đăng nhập để bắt đầu.";
      loginMessage.className = "form-message success"; loginPassword.focus();
    } catch (error) { if (stale(error)) return; message.textContent = safeDetail(error); }
    finally { registrationPending = false; button.disabled = false; button.textContent = "Đăng ký bệnh nhân"; $("#backToLogin").disabled = false; }
  });

  loginRole.addEventListener("change", function () { showUnsupportedRole(loginRole.value); });
  loginForm.addEventListener("submit", submitLogin);
  let logoutPending = false;
  async function logout() {
    if (logoutPending) return;
    logoutPending = true; viewEpoch += 1; pendingAction = null; appView.inert = true;
    const button = $("#logoutButton"); button.disabled = true; button.textContent = "Đang đăng xuất…";
    if (!state.token) { endSession("Đã đăng xuất khỏi phiên demo."); logoutPending = false; button.disabled = false; button.textContent = "Đăng xuất"; return; }
    try {
      await apiRequest("/api/v1/auth/logout", { method: "POST" });
      endSession("Đã đăng xuất khỏi phiên demo.");
    } catch (error) { if (stale(error)) return;
      if (error && error.status === 401) {
        endSession("Phiên đã hết hạn hoặc bị thu hồi.");
        return;
      }
      await setView(state.view);
      setGlobalMessage("Không thể xác nhận thu hồi phiên trên máy chủ. Hãy thử lại khi Gateway sẵn sàng.", "error");
    } finally { logoutPending = false; appView.inert = false; button.disabled = false; button.textContent = "Đăng xuất"; }
  }
  $("#logoutButton").addEventListener("click", logout);
  $("#navToggle").addEventListener("click", function () {
    const open = !document.body.classList.contains("nav-open");
    document.body.classList.toggle("nav-open", open);
    scrim.hidden = !open;
    $("#navToggle").setAttribute("aria-expanded", open ? "true" : "false");
    syncNav();
    if (open) $(".nav-item", roleNav).focus();
  });
  scrim.addEventListener("click", function () { closeNav(true); });
  document.addEventListener("keydown", function (event) {
    if (!document.body.classList.contains("nav-open")) return;
    if (event.key === "Escape") { event.preventDefault(); closeNav(true); }
    if (event.key === "Tab") {
      const buttons = Array.from(roleNav.querySelectorAll("button")); const first = buttons[0]; const last = buttons[buttons.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
  window.addEventListener("resize", function () { if (!window.matchMedia("(max-width: 768px)").matches) closeNav(); syncNav(); });
  syncNav();

  async function initialize() {
    showUnsupportedRole(loginRole.value);
    const savedToken = sessionStorage.getItem(TOKEN_KEY);
    const savedUser = sessionStorage.getItem(USER_KEY);
    if (savedToken && savedUser) {
      state.token = savedToken;
      state.username = savedUser;
      loginRole.value = savedUser;
      const button = $("#loginButton"); button.disabled = true; loginPending = true;
      try {
        const actor = await apiRequest("/api/v1/auth/me");
        if (!actor || !navByRole[actor.role]) throw { status: 403 };
        state.role = actor.role; state.username = actor.username;
        showApp();
      } catch (error) { if (stale(error)) return; endSession(safeDetail(error)); }
      finally { button.disabled = false; loginPending = false; }

    }
  }

  viewContent.addEventListener("submit", function (event) { if (pendingAction && pendingAction.epoch === viewEpoch || event.target.dataset.saved === "true") { event.preventDefault(); event.stopImmediatePropagation(); } }, true);
  initialize();
})();
