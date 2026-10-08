(() => {
  "use strict";

  const API_BASE = (new URLSearchParams(location.search).get("api") || location.origin).replace(/\/+$/, "");
  const TOKEN_KEY = "hf-demo.access-token";
  const USER_KEY = "hf-demo.username";
  const accountRoles = { doctor_demo: "doctor", nurse_demo: "nurse", pharmacist_demo: "pharmacist", admin_demo: "admin", patient_demo: "patient" };
  const supportedAccounts = Object.keys(accountRoles);
  const roleLabels = { doctor: "Bác sĩ", nurse: "Điều dưỡng", pharmacist: "Dược sĩ", admin: "Quản trị", patient: "Bệnh nhân" };
  const moduleLabels = { diagnosis: "Diagnosis", lab_test: "Lab/Test", treatment: "Treatment", medsafety: "MedSafety" };
  const observationLabels = { ef: "Phân suất tống máu", potassium: "Kali", egfr: "eGFR", creatinine: "Creatinin", bnp: "BNP", nt_probnp: "NT-proBNP", systolic_bp: "Huyết áp tâm thu", heart_rate: "Nhịp tim", dyspnea: "Khó thở", frailty: "Frailty", comorbidity: "Bệnh đồng mắc" };
  const observationUnits = { ef: "%", potassium: "mmol/L", egfr: "mL/min/1.73m2", creatinine: "umol/L", bnp: "pg/mL", nt_probnp: "pg/mL", systolic_bp: "mmHg", heart_rate: "bpm" };
  const navByRole = {
    doctor: [["overview", "Tổng quan", "grid"], ["cases", "Hồ sơ", "file"], ["encounter", "Encounter", "timeline"], ["evaluation", "Đánh giá demo", "check"], ["history", "Lịch sử đánh giá", "clock"]],
    nurse: [["overview", "Tổng quan", "grid"], ["cases", "Hồ sơ được phân quyền", "file"], ["encounter", "Encounter và observations", "timeline"]],
    pharmacist: [["overview", "Tổng quan", "grid"], ["medsafety", "Rà soát MedSafety", "med"]],
    admin: [["overview", "Tổng quan", "grid"], ["rules", "Quy tắc", "sliders"], ["audit", "Nhật ký", "list"]],
    patient: [["overview", "Tổng quan", "grid"], ["appointments", "Lịch hẹn", "clock"], ["measurements", "Số đo", "timeline"], ["prescriptions", "Đơn thuốc", "file"], ["reminders", "Nhắc nhở", "list"]]
  };
  const viewMeta = {
    overview: ["TỔNG QUAN", "Tổng quan", "Trạng thái Gateway và dữ liệu synthetic hiện có."],
    cases: ["HỒ SƠ", "Hồ sơ", "Danh sách hồ sơ do API trả về. Chỉ dùng dữ liệu synthetic."],
    encounter: ["ENCOUNTER", "Encounter và timeline", "Chọn encounter từ hồ sơ do API trả về; observations và notes gắn theo encounter."],
    evaluation: ["MODULES", "Đánh giá demo", "Mọi module đều ở trạng thái mock_not_evaluated."],
    history: ["LỊCH SỬ", "Lịch sử đánh giá", "API hiện trả lịch sử evaluation, không phải toàn bộ diễn biến lâm sàng."],
    medsafety: ["MEDSAFETY", "Rà soát MedSafety", "Dược sĩ chỉ gọi module MedSafety; trạng thái luôn mock_not_evaluated."],
    rules: ["QUẢN TRỊ", "Quy tắc", "Chỉ quản lý metadata và kiểm tra schema; không có xác nhận lâm sàng."],
    audit: ["NHẬT KÝ", "Nhật ký", "Sự kiện do API trả về cho role admin."],
    appointments: ["LỊCH HẸN", "Lịch hẹn", "Lịch hẹn synthetic lấy từ cổng bệnh nhân."],
    measurements: ["SỐ ĐO", "Số đo", "Bản ghi do API trả về; không thay thế đo đạc hoặc chăm sóc thật."],
    prescriptions: ["ĐƠN THUỐC", "Đơn thuốc", "Chỉ xem response từ API; bệnh nhân không sửa đơn, liều hoặc giờ uống."],
    reminders: ["NHẮC NHỞ", "Nhắc nhở", "Cập nhật trạng thái taken hoặc skipped theo API."]
  };
  const state = {
    token: null, username: null, role: null, view: "overview",
    cases: [], selectedCase: null, currentEncounter: null,
    encounterObservations: [], encounterMedications: [],
    pharmacyEncounterId: "", pharmacyRevision: "", pharmacyMedications: [],
    caseEncounters: [], encounterNotes: [], editingObservation: null,
    patientData: { doctors: [], appointments: [], measurements: [], prescriptions: [], reminders: [] },
    lastEvaluation: null, lastRuleTest: null
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

  function safeDetail(error) {
    if (!error || !error.status) return "Không kết nối được Gateway. Kiểm tra địa chỉ API và trạng thái máy chủ.";
    if (error.status === 401) return "Token thiếu, hết hạn hoặc thông tin đăng nhập không hợp lệ.";
    if (error.status === 403) return "Tài khoản không có quyền cho thao tác này.";
    if (error.status === 404) return "API không tìm thấy bản ghi hoặc route được yêu cầu.";
    if (error.status === 409) return error.detail || "Dữ liệu đã thay đổi; tải lại trước khi tiếp tục.";
    if (error.status === 422) return error.detail || "Dữ liệu gửi lên chưa hợp lệ.";
    if (error.status === 503) return error.detail || "Gateway chưa được cấu hình cho demo.";
    return error.detail || "Gateway trả HTTP " + error.status + ".";
  }

  function endSession(message) {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
    state.token = null; state.username = null; state.role = null;
    state.cases = []; state.selectedCase = null; state.currentEncounter = null; state.lastEvaluation = null;
    document.body.classList.remove("nav-open");
    scrim.hidden = true;
    $("#navToggle").setAttribute("aria-expanded", "false");
    appView.hidden = true;
    loginView.hidden = false;
    loginPassword.value = "";
    loginMessage.textContent = message || "";
    loginMessage.className = "form-message";
  }

  async function apiRequest(path, options) {
    const config = options || {};
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
      throw { status: 0, detail: "Network error" };
    }
    const raw = await response.text();
    let payload = null;
    if (raw) {
      try { payload = JSON.parse(raw); }
      catch (_) { payload = { detail: "Phản hồi Gateway không phải JSON." }; }
    }
    if (!response.ok) {
      const error = { status: response.status, detail: payload && payload.detail ? String(payload.detail) : "" };
      if (response.status === 401 && state.token) endSession(safeDetail(error));
      throw error;
    }
    return payload;
  }

  function showUnsupportedRole(role) {
    const supported = supportedAccounts.includes(role);
    unsupportedRole.hidden = true;
    unsupportedRole.textContent = "";
    loginPassword.disabled = !supported;
    $("#loginButton").disabled = !supported;
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
    if (state.currentEncounter && state.currentEncounter.id) badges.push('<span class="badge">Encounter ' + escapeHTML(state.currentEncounter.id) + "</span>");
    $("#contextBadges").innerHTML = badges.join("");
  }

  function closeNav() {
    document.body.classList.remove("nav-open");
    scrim.hidden = true;
    $("#navToggle").setAttribute("aria-expanded", "false");
  }

  function setView(view) {
    const allowed = (navByRole[state.role] || []).some(function (item) { return item[0] === view; });
    if (!allowed) { setGlobalMessage("Màn hình này chưa được hỗ trợ cho role đang đăng nhập.", "warning"); return; }
    state.view = view;
    renderNavigation();
    setHeading(view);
    setGlobalMessage("", "");
    viewContent.setAttribute("aria-busy", "true");
    viewContent.innerHTML = '<div class="loading-line" role="status">Đang tải dữ liệu từ Gateway…</div>';
    renderCurrentView().catch(function (error) {
      if (appView.hidden) return;
      setGlobalMessage(safeDetail(error), "error");
      viewContent.innerHTML = '<div class="empty-state"><strong>Không hiển thị được dữ liệu</strong>Không có dữ liệu mẫu thay thế. Thử tải lại sau khi API phản hồi.</div>';
    }).finally(function () {
      viewContent.setAttribute("aria-busy", "false");
      setHeading(view);
    });
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
      (description ? "<p>" + escapeHTML(description) + "</p>" : "") + "</div></header><div class=\"panel-body\">" + body + "</div></article>";
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
      gatewayStatus.innerHTML = '<span class="status-dot"></span><span>Gateway chưa kết nối</span>';
      return;
    }
    gatewayStatus.dataset.state = data && data.status === "ok" ? "ok" : "";
    const parts = [];
    if (data && data.status) parts.push(data.status);
    if (data && data.mode) parts.push(data.mode);
    if (data && data.persistence) parts.push(data.persistence);
    gatewayStatus.innerHTML = '<span class="status-dot"></span><span>Gateway: ' + escapeHTML(parts.join(" · ") || "Phản hồi không đủ trường") + "</span>";
  }

  async function renderOverview() {
    let health = null;
    let healthError = null;
    try { health = await apiRequest("/health", { auth: false }); }
    catch (error) { healthError = error; }
    setGatewayStatus(health, healthError);
    let lead = "";
    if (state.role === "doctor" || state.role === "nurse") {
      const cases = await apiRequest("/api/v1/cases");
      state.cases = Array.isArray(cases) ? cases : [];
      const description = state.role === "nurse"
        ? "Hồ sơ theo quyền điều dưỡng do API trả về; chỉ xem và ghi observation/nursing note theo scope."
        : "Số lượng lấy từ GET /api/v1/cases; Gateway lưu trong RAM.";
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
      lead = panel("Cổng bệnh nhân", "Thông tin lấy theo tài khoản patient_demo", '<p class="subtle">Dữ liệu chỉ lấy từ các endpoint patient. Đơn thuốc chỉ xem; không sửa đơn, liều hoặc giờ uống.</p><div class="quick-links"><button class="button" type="button" data-open-view="appointments">Lịch hẹn</button><button class="button" type="button" data-open-view="measurements">Số đo</button><button class="button" type="button" data-open-view="prescriptions">Đơn thuốc</button><button class="button" type="button" data-open-view="reminders">Nhắc nhở</button></div>', "half");
    } else {
      lead = panel("MedSafety", "Phạm vi dược sĩ", '<span class="status-label mock">mock_not_evaluated</span><p class="subtle">API không trả cảnh báo thuốc hoặc liều.</p><button class="button" type="button" data-open-view="medsafety">Mở rà soát</button>', "half");
    }
    const healthBody = health
      ? '<dl class="key-value"><div><dt>Trạng thái</dt><dd>' + escapeHTML(health.status || "Không có từ API") +
        '</dd></div><div><dt>Chế độ</dt><dd>' + escapeHTML(health.mode || "Không có từ API") +
        '</dd></div><div><dt>Lưu trữ</dt><dd>' + escapeHTML(health.persistence || "Không có từ API") + "</dd></div></dl>"
      : '<p class="subtle">Không nhận được phản hồi từ /health. Nội dung nghiệp vụ không được thay bằng fixture giả.</p>';
    const sourceBody = '<div class="callout neutral"><div><strong>Nguồn dữ liệu</strong><br>Giao diện chỉ hiển thị response từ Gateway và không bổ sung fixture hoặc kết quả tự dựng.</div></div>';
    viewContent.innerHTML = '<div class="panel-grid">' + lead + panel("Trạng thái dịch vụ", "Phản hồi từ GET /health", healthBody, "half") + panel("Giới hạn demo", "Không phải hệ thống chăm sóc", sourceBody) + "</div>";
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
      '<button class="button" type="button" data-open-view="encounter">Mở encounter</button></div>';
    if (!editable) return panel("Chi tiết API", "Chỉ đọc trong scope điều dưỡng.", head);
    const body = head +
      '<form id="updateCaseForm" class="inline-form"><div><label for="editSyntheticCode">Mã synthetic</label><input id="editSyntheticCode" name="synthetic_code" required pattern="SYN-[A-Z0-9-]{1,24}" maxlength="30" value="' + escapeHTML(item.synthetic_code) + '"></div>' +
      '<div><label for="editAge">Tuổi trong bản ghi synthetic</label><input id="editAge" name="age" type="number" min="0" max="120" required value="' + escapeHTML(item.age) + '"></div>' +
      '<div><label for="editSex">Giới tính trong bản ghi</label><select id="editSex" name="sex" required>' + caseSexOptions(item.sex) + "</select></div>" +
      '<input type="hidden" name="expected_revision" value="' + escapeHTML(item.revision) + '">' +
      '<div class="form-actions"><button class="button primary" type="submit">Cập nhật hồ sơ synthetic</button></div><p class="form-error span-all" id="updateCaseError" role="status"></p></form>';
    return panel("Chi tiết API", "Các trường được nạp từ bản ghi đã chọn.", body);
  }

  async function renderCases() {
    const result = await apiRequest("/api/v1/cases");
    state.cases = Array.isArray(result) ? result : [];
    if (state.selectedCase) {
      const fresh = state.cases.find(function (item) { return item.id === state.selectedCase.id; });
      if (fresh) state.selectedCase = fresh;
      else { state.selectedCase = null; state.currentEncounter = null; state.caseEncounters = []; }
    }
    const doctor = state.role === "doctor";
    const rows = state.cases.length
      ? state.cases.map(function (item) {
        return '<div class="case-row"><div><div class="case-code">' + escapeHTML(item.synthetic_code) + '</div><div class="row-meta">ID ' + escapeHTML(item.id) + "</div></div>" +
          '<div class="row-meta">' + escapeHTML(item.age) + " tuổi</div><div class=\"row-meta\">" + escapeHTML(sexLabel(item.sex)) + '</div>' +
          '<div class="row-actions"><button class="button" type="button" data-select-case="' + escapeHTML(item.id) + '">Mở</button></div></div>';
      }).join("")
      : emptyState("API trả về danh sách rỗng", doctor ? "Chưa có hồ sơ trong bộ nhớ Gateway. Chỉ tạo hồ sơ synthetic." : "Chưa có hồ sơ trong scope do API trả về.");
    const createBody = doctor
      ? '<p class="subtle">Chỉ nhập dữ liệu synthetic. Nếu để trống mã, Gateway sẽ tạo mã synthetic và trả về trong response.</p>' +
        '<form id="createCaseForm" class="inline-form"><div><label for="newAge">Tuổi</label><input id="newAge" name="age" type="number" min="0" max="120" required></div>' +
        '<div><label for="newSex">Giới tính</label><select id="newSex" name="sex" required>' + caseSexOptions("") + '</select></div>' +
        '<div class="span-all"><label for="newSyntheticCode">Mã synthetic (không bắt buộc)</label><input id="newSyntheticCode" name="synthetic_code" pattern="SYN-[A-Z0-9-]{1,24}" maxlength="30"><div class="input-help">Không nhập thông tin định danh cá nhân.</div></div>' +
        '<div class="form-actions"><button class="button primary" type="submit">Tạo hồ sơ</button></div><p class="form-error span-all" id="createCaseError" role="status"></p></form>'
      : '<div class="callout neutral"><div>Điều dưỡng chỉ xem hồ sơ trong scope do API trả về. Không tạo hoặc sửa hồ sơ.</div></div>';
    viewContent.innerHTML = '<div class="panel-grid">' + panel(doctor ? "Tạo hồ sơ synthetic" : "Quyền hồ sơ", doctor ? "POST /api/v1/cases" : "GET /api/v1/cases", createBody, "half") +
      panel("Hồ sơ do API trả về", "GET /api/v1/cases · " + state.cases.length + " bản ghi", '<div class="case-list">' + rows + "</div>", "half") +
      renderCaseDetail(state.selectedCase, doctor) + "</div>";

    const createForm = $("#createCaseForm");
    if (createForm) createForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      const form = new FormData(createForm);
      const body = { age: Number(form.get("age")), sex: String(form.get("sex")) };
      const code = String(form.get("synthetic_code") || "").trim();
      if (code) body.synthetic_code = code;
      const button = createForm.querySelector('button[type="submit"]');
      button.disabled = true;
      try {
        state.selectedCase = await apiRequest("/api/v1/cases", { method: "POST", body: body });
        state.currentEncounter = null;
        showToast("Hồ sơ đã được API tạo.");
        setView("cases");
      } catch (error) {
        $("#createCaseError").textContent = safeDetail(error);
        button.disabled = false;
      }
    });
    viewContent.querySelectorAll("[data-select-case]").forEach(function (button) {
      button.addEventListener("click", async function () {
        try {
          state.selectedCase = await apiRequest("/api/v1/cases/" + encodeURIComponent(button.dataset.selectCase));
          state.currentEncounter = null;
          state.caseEncounters = [];
          state.encounterObservations = [];
          state.encounterMedications = [];
          state.encounterNotes = [];
          setView("cases");
        } catch (error) { setGlobalMessage(safeDetail(error), "error"); }
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
    button.disabled = true;
    try {
      state.selectedCase = await apiRequest("/api/v1/cases/" + encodeURIComponent(state.selectedCase.id) + "?expected_revision=" + encodeURIComponent(revision), { method: "PUT", body: body });
      showToast("Hồ sơ synthetic đã được cập nhật qua API.");
      setView("cases");
    } catch (error) {
      $("#updateCaseError").textContent = safeDetail(error);
      button.disabled = false;
    }
  }

  function datetimePayload(value) {
    const date = new Date(value);
    return value && Number.isFinite(date.getTime()) ? date.toISOString() : null;
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
    state.selectedCase = caseData;
    state.currentEncounter = encounter;
    state.encounterObservations = Array.isArray(results[0]) ? results[0] : [];
    state.encounterNotes = Array.isArray(results[1]) ? results[1] : [];
    state.encounterMedications = state.role === "doctor" && Array.isArray(results[2]) ? results[2] : [];
  }
  function valueForObservation(item) {
    if (item.status !== "present") return "Không có giá trị: " + escapeHTML(item.status || "Không có trạng thái từ API");
    const value = item.value === true ? "true" : item.value === false ? "false" : item.value;
    return escapeHTML(value) + (item.unit ? " " + escapeHTML(item.unit) : "");
  }

  function timelineMarkup(encounter, observations) {
    const events = [{ time: encounter.occurred_at, title: "Encounter được API trả về", details: "ID " + encounter.id }];
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
        "<p>" + escapeHTML(item.details) + "</p></div></div>";
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
    const options = Object.keys(observationLabels).map(function (code) {
      return '<option value="' + escapeHTML(code) + '"' + (existing && existing.code === code ? " selected" : "") + '>' + escapeHTML(observationLabels[code]) + " · " + escapeHTML(code) + "</option>";
    }).join("");
    const selectedStatus = existing ? existing.status : "";
    const selectedSource = existing ? existing.source : "";
    const intro = state.role === "nurse"
      ? "Gateway giới hạn observation theo allowlist điều dưỡng; lỗi validation của API sẽ được hiển thị."
      : "Endpoint chỉ ghi dữ liệu synthetic và không xác nhận y khoa.";
    return '<div class="callout"><div><strong>Chỉ nhập dữ liệu synthetic.</strong><br>' + intro + " Không nhập số đo thật.</div></div>" +
      '<form id="observationForm" class="inline-form"><div><label for="obsCode">Loại dữ liệu</label><select id="obsCode" name="code" required><option value="">Chọn loại</option>' + options + "</select></div>" +
      '<div><label for="obsStatus">Trạng thái</label><select id="obsStatus" name="status" required><option value="">Chọn trạng thái</option>' +
      '<option value="present"' + (selectedStatus === "present" ? " selected" : "") + '>present</option><option value="not_measured"' + (selectedStatus === "not_measured" ? " selected" : "") + '>not_measured</option><option value="unknown"' + (selectedStatus === "unknown" ? " selected" : "") + '>unknown</option></select></div>' +
      '<div><label>Giá trị</label><div id="obsValueControl"></div></div>' +
      '<div id="obsUnitGroup" hidden><label for="obsUnit">Đơn vị</label><select id="obsUnit" name="unit" disabled><option value="">Chọn dữ liệu trước</option></select></div>' +
      '<div><label for="obsObservedAt">Thời điểm quan sát</label><input id="obsObservedAt" name="observed_at" type="datetime-local" required value="' + escapeHTML(datetimeLocalValue(existing && existing.observed_at)) + '"><div class="input-help">Chọn thời điểm từ bản ghi synthetic.</div></div>' +
      '<div><label for="obsSource">Nguồn</label><select id="obsSource" name="source" required><option value="">Chọn nguồn</option><option value="manual_synthetic"' + (selectedSource === "manual_synthetic" ? " selected" : "") + '>manual_synthetic</option><option value="mock_his"' + (selectedSource === "mock_his" ? " selected" : "") + '>mock_his</option><option value="mock_lis"' + (selectedSource === "mock_lis" ? " selected" : "") + '>mock_lis</option><option value="mock_pacs"' + (selectedSource === "mock_pacs" ? " selected" : "") + '>mock_pacs</option></select></div>' +
      '<div class="form-actions"><button class="button primary" type="submit">' + (existing ? "Cập nhật observation synthetic" : "Ghi observation synthetic") + "</button>" +
      (existing ? ' <button class="button" id="cancelObservationEdit" type="button">Hủy sửa</button>' : "") +
      '</div><p class="form-error span-all" id="observationError" role="status"></p></form>';
  }
  function medicationFormMarkup() {
    return '<div class="callout"><div><strong>Chỉ ghi bản ghi thuốc synthetic.</strong><br>Endpoint không tạo đơn thuốc, lịch uống hoặc hướng dẫn điều trị.</div></div>' +
      '<form id="medicationForm" class="inline-form"><div class="span-all"><label for="medIngredient">Mã hoạt chất synthetic</label><input id="medIngredient" name="ingredient_code" pattern="[a-z][a-z0-9_]{1,59}" required maxlength="60"></div>' +
      '<div><label for="medDose">Liều trong bản ghi synthetic</label><input id="medDose" name="dose" type="number" min="0.000001" step="any" required></div>' +
      '<div><label for="medDoseUnit">Đơn vị liều</label><select id="medDoseUnit" name="dose_unit" required><option value="">Chọn đơn vị</option><option>mg</option><option>mcg</option><option>g</option><option>mL</option></select></div>' +
      '<div><label for="medRoute">Đường dùng</label><select id="medRoute" name="route" required><option value="">Chọn đường dùng</option><option value="oral">oral</option><option value="iv">iv</option><option value="other">other</option></select></div>' +
      '<div><label for="medFrequency">Tần suất mỗi ngày</label><input id="medFrequency" name="frequency_per_day" type="number" min="1" max="24" required></div>' +
      '<div><label for="medKind">Loại bản ghi</label><select id="medKind" name="kind" required><option value="">Chọn loại</option><option value="current">current</option><option value="proposed">proposed</option></select></div>' +
      '<div class="form-actions"><button class="button primary" type="submit">Ghi thuốc synthetic</button></div><p class="form-error span-all" id="medicationError" role="status"></p></form>';
  }

  function datetimeLocalValue(value) {
    if (!value) return "";
    const date = new Date(value);
    if (!Number.isFinite(date.getTime())) return "";
    return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
  }

  function notesMarkup(items) {
    if (!items.length) return emptyState("API chưa trả note", "Danh sách notes rỗng.");
    return '<div class="record-list">' + items.map(function (item) {
      return '<article class="record-row"><div><strong>' + escapeHTML(item.kind || "Note") + '</strong><div class="row-meta">ID ' +
        escapeHTML(item.id || "Không có từ API") + " · " + escapeHTML(formatDate(item.recorded_at || item.created_at || item.occurred_at)) +
        '</div></div><p class="note-content">' + escapeHTML(item.content || "Không có nội dung từ API") + "</p></article>";
    }).join("") + "</div>";
  }

  function observationTableMarkup(items) {
    if (!items.length) return emptyState("API chưa trả observation", "Danh sách rỗng.");
    return '<div class="data-table-wrap"><table class="data-table"><thead><tr><th>Quan sát</th><th>Giá trị</th><th>Thời điểm</th><th>Nguồn</th>' +
      (state.role === "doctor" ? "<th>Thao tác</th>" : "") + "</tr></thead><tbody>" +
      items.map(function (item) {
        return "<tr><td>" + escapeHTML(observationLabels[item.code] || item.code) + " · " + escapeHTML(item.status) +
          "</td><td>" + valueForObservation(item) + "</td><td>" + escapeHTML(formatDate(item.observed_at)) +
          "</td><td>" + escapeHTML(item.source || "Không có từ API") + "</td>" +
          (state.role === "doctor" ? '<td><button class="button" type="button" data-edit-observation="' + escapeHTML(item.id) + '">Sửa</button></td>' : "") + "</tr>";
      }).join("") + "</tbody></table></div>";
  }

  function nursingNotesPanel() {
    const kind = state.role === "nurse" ? "nursing" : "examination";
    const label = state.role === "nurse" ? "Ghi nursing note synthetic" : "Ghi examination note synthetic";
    const body = '<div class="callout"><div><strong>Chỉ nhập nội dung synthetic.</strong><br>Gateway giới hạn loại note theo role; không nhập thông tin người bệnh thật.</div></div>' +
      '<form id="noteForm" class="inline-form"><div class="span-all"><label for="noteContent">' + label + '</label><textarea id="noteContent" name="content" required rows="4"></textarea></div>' +
      '<div class="form-actions"><button class="button primary" type="submit">Ghi note synthetic</button></div><p class="form-error span-all" id="noteError" role="status"></p></form>';
    return panel("Notes theo encounter", "GET/POST /api/v1/encounters/{id}/notes · kind " + kind, notesMarkup(state.encounterNotes) + body);
  }

  async function renderEncounter() {
    const doctor = state.role === "doctor";
    const nurse = state.role === "nurse";
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
          '</p><form id="createEncounterForm" class="inline-form"><div class="span-all"><label for="encounterDate">Thời điểm encounter</label><input id="encounterDate" name="occurred_at" type="datetime-local" required><div class="input-help">Chọn thời điểm từ dữ liệu synthetic.</div></div><div class="form-actions"><button class="button primary" type="submit">Tạo encounter</button></div><p class="form-error span-all" id="encounterCreateError" role="status"></p></form>'
        : '<p class="subtle">Chọn hồ sơ để tạo encounter.</p>')
      : nurse
        ? '<div class="callout neutral"><div>Điều dưỡng chỉ đọc encounter trong scope; không tạo encounter.</div></div>'
        : '<div class="callout neutral"><div>Role này không có màn hình clinical encounter.</div></div>';
    const encounterRows = state.caseEncounters.length
      ? '<div class="record-list">' + state.caseEncounters.map(function (item) {
          return '<div class="record-row"><div><strong>Encounter ' + escapeHTML(item.id) + '</strong><div class="row-meta">' + escapeHTML(formatDate(item.occurred_at)) +
            '</div></div><button class="button" type="button" data-select-encounter="' + escapeHTML(item.id) + '">Mở</button></div>';
        }).join("") + "</div>"
      : emptyState("API trả về danh sách encounter rỗng", "Không có encounter trong scope của hồ sơ.");
    const knownId = state.currentEncounter ? state.currentEncounter.id : "";
    let detail = "";
    let context = "";
    if (state.currentEncounter && (doctor || nurse)) {
      detail = panel("Timeline theo encounter", "Mốc và observation lấy từ response API.", timelineMarkup(state.currentEncounter, state.encounterObservations)) +
        panel("Observations", "GET/POST observations" + (doctor ? " · PUT chỉ dành cho doctor" : " · nurse chỉ ghi theo allowlist API"), observationTableMarkup(state.encounterObservations) +
          observationFormMarkup()) +
        nursingNotesPanel();
      if (doctor) detail += panel("Thuốc theo encounter", "Chỉ dữ liệu do API trả về; không phải hướng dẫn sử dụng.", medicationTable(state.encounterMedications)) +
        panel("Ghi bản ghi thuốc synthetic", "POST /api/v1/encounters/{id}/medications", medicationFormMarkup());
      context = panel("Phạm vi đang mở", "Response API", '<dl class="key-value"><div><dt>Encounter ID</dt><dd>' + escapeHTML(state.currentEncounter.id) +
        '</dd></div><div><dt>Thời điểm</dt><dd>' + escapeHTML(formatDate(state.currentEncounter.occurred_at)) +
        '</dd></div><div><dt>Hồ sơ</dt><dd>' + escapeHTML(state.selectedCase ? state.selectedCase.synthetic_code : state.currentEncounter.case_id) + "</dd></div></dl>");
    }
    const loadBody = '<p class="subtle">Có danh sách encounter theo hồ sơ từ API; có thể mở ID được cấp trực tiếp nếu cần.</p>' +
      '<form id="loadEncounterForm" class="inline-form"><div class="span-all"><label for="knownEncounterId">Encounter ID</label><input id="knownEncounterId" name="encounter_id" required value="' +
      escapeHTML(knownId) + '"></div><div class="form-actions"><button class="button" type="submit">Tải encounter</button></div><p class="form-error span-all" id="encounterLoadError" role="status"></p></form>';
    viewContent.innerHTML = intro + '<div class="panel-grid">' +
      panel(doctor ? "Tạo encounter" : "Quyền encounter", doctor ? "POST /api/v1/cases/{case_id}/encounters" : "Role nurse chỉ đọc encounter", createBody, "half") +
      panel("Encounter theo hồ sơ", "GET /api/v1/cases/{case_id}/encounters", encounterRows, "half") +
      panel("Mở encounter đã biết", "GET /api/v1/encounters/{id}", loadBody) + context + detail + "</div>";
    viewContent.querySelectorAll("[data-open-view]").forEach(function (button) {
      button.addEventListener("click", function () { setView(button.dataset.openView); });
    });
    viewContent.querySelectorAll("[data-select-encounter]").forEach(function (button) {
      button.addEventListener("click", async function () {
        try { await loadEncounterForRole(button.dataset.selectEncounter); state.editingObservation = null; setView("encounter"); }
        catch (error) { setGlobalMessage(safeDetail(error), "error"); }
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
      button.disabled = true;
      try {
        await loadEncounterForRole(id);
        state.editingObservation = null;
        setView("encounter");
      } catch (error) {
        $("#encounterLoadError").textContent = safeDetail(error);
        button.disabled = false;
      }
    });
    const createForm = $("#createEncounterForm");
    if (createForm) createForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      const date = datetimePayload(String(new FormData(createForm).get("occurred_at") || ""));
      if (!date) { $("#encounterCreateError").textContent = "Chọn thời điểm hợp lệ từ dữ liệu synthetic."; return; }
      const button = createForm.querySelector("button");
      button.disabled = true;
      try {
        const path = "/api/v1/cases/" + encodeURIComponent(state.selectedCase.id) + "/encounters?expected_revision=" + encodeURIComponent(state.selectedCase.revision);
        const created = await apiRequest(path, { method: "POST", body: { occurred_at: date } });
        await loadEncounterForRole(created.id);
        showToast("Encounter synthetic đã được API tạo.");
        setView("encounter");
      } catch (error) {
        $("#encounterCreateError").textContent = safeDetail(error);
        button.disabled = false;
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
    } else if (code === "dyspnea") {
      valueControl.innerHTML = '<select id="obsValue" name="value" required><option value="">Chọn giá trị</option><option value="true">true</option><option value="false">false</option></select>';
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
        value = observationUnits[code] ? Number(raw) : code === "dyspnea" ? raw === "true" : String(raw);
        unit = observationUnits[code] ? String(values.get("unit") || "") : null;
      }
      if (!observedAt) { $("#observationError").textContent = "Chọn thời điểm observation hợp lệ."; return; }
      const body = { code: code, value: value, unit: unit, status: status, observed_at: observedAt, source: String(values.get("source") || "") };
      const button = form.querySelector('button[type="submit"]');
      button.disabled = true;
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
        showToast("Observation synthetic đã được API lưu.");
        setView("encounter");
      } catch (error) {
        $("#observationError").textContent = safeDetail(error);
        button.disabled = false;
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
      button.disabled = true;
      try {
        const path = "/api/v1/encounters/" + encodeURIComponent(state.currentEncounter.id) + "/notes?expected_revision=" + encodeURIComponent(state.selectedCase.revision);
        await apiRequest(path, { method: "POST", body: { kind: kind, content: content } });
        await loadEncounterForRole(state.currentEncounter.id);
        showToast("Note synthetic đã được API lưu.");
        setView("encounter");
      } catch (error) {
        $("#noteError").textContent = safeDetail(error);
        button.disabled = false;
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
      button.disabled = true;
      try {
        await apiRequest("/api/v1/encounters/" + encodeURIComponent(state.currentEncounter.id) + "/medications", { method: "POST", body: body });
        await loadEncounterForRole(state.currentEncounter.id);
        showToast("Bản ghi thuốc synthetic đã được API lưu.");
        setView("encounter");
      } catch (error) {
        $("#medicationError").textContent = safeDetail(error);
        button.disabled = false;
      }
    });
  }

  function evaluationFormMarkup(pharmacist) {
    const encounterId = pharmacist ? state.pharmacyEncounterId : (state.currentEncounter ? state.currentEncounter.id : "");
    const revision = pharmacist ? state.pharmacyRevision : (state.selectedCase ? state.selectedCase.revision : "");
    const moduleItems = pharmacist ? [["medsafety", "MedSafety"]] : Object.keys(moduleLabels).map(function (key) { return [key, moduleLabels[key]]; });
    const modules = moduleItems.map(function (item) {
      return '<label class="module-option"><input type="checkbox" name="modules" value="' + escapeHTML(item[0]) + '"><span>' + escapeHTML(item[1]) + "</span></label>";
    }).join("");
    const note = pharmacist
      ? '<div class="callout"><div><strong>Giới hạn API:</strong> POST /evaluations yêu cầu expected_revision, nhưng chưa có route pharmacist để đọc revision. Chỉ gửi khi revision đến từ response API được cấp quyền; không tự đoán.</div></div>'
      : '<div class="callout"><div><strong>Chỉ trạng thái stub:</strong> API không trả gợi ý hoặc cảnh báo lâm sàng. Không thể chấp nhận gợi ý hoặc tạo y lệnh từ kết quả này.</div></div>';
    return note + '<form id="evaluationForm" class="inline-form"><div class="span-all"><label for="evalEncounterId">Encounter ID</label><input id="evalEncounterId" name="encounter_id" required value="' +
      escapeHTML(encounterId) + '"></div><div><label for="evalRevision">expected_revision</label><input id="evalRevision" name="expected_revision" type="number" min="1" required value="' + escapeHTML(revision) + '"></div>' +
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
    button.disabled = true;
    try {
      const created = await apiRequest("/api/v1/evaluations", { method: "POST", body: body });
      state.lastEvaluation = await apiRequest("/api/v1/evaluations/" + encodeURIComponent(created.id));
      if (pharmacist) state.pharmacyRevision = String(body.expected_revision);
      showToast("Gateway đã trả evaluation stub.");
      setView(pharmacist ? "medsafety" : "evaluation");
    } catch (error) {
      $("#evaluationError").textContent = safeDetail(error);
      button.disabled = false;
    }
  }

  async function renderEvaluation() {
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
    const medications = state.pharmacyMedications.length
      ? medicationTable(state.pharmacyMedications)
      : emptyState("Chưa tải danh sách thuốc", "Nhập encounter ID được API cấp để gọi GET /medications.");
    const resultBody = state.lastEvaluation
      ? evaluationResultMarkup(state.lastEvaluation)
      : emptyState("Chưa có evaluation trong phiên này", "Không tạo kết quả hoặc cảnh báo ngoài response API.");
    const loadBody = '<form id="pharmacyLoadForm" class="inline-form"><div class="span-all"><label for="pharmacyEncounterId">Encounter ID</label><input id="pharmacyEncounterId" name="encounter_id" required value="' +
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
      button.disabled = true;
      try {
        state.pharmacyEncounterId = id;
        state.pharmacyMedications = await apiRequest("/api/v1/encounters/" + encodeURIComponent(id) + "/medications");
        setView("medsafety");
      } catch (error) {
        $("#pharmacyLoadError").textContent = safeDetail(error);
        button.disabled = false;
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
    $("#exportHistory").addEventListener("click", async function () {
      try {
        const data = await apiRequest("/api/v1/cases/" + encodeURIComponent(state.selectedCase.id) + "/export");
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "synthetic-export-" + String(state.selectedCase.synthetic_code || "case") + ".json";
        link.click();
        URL.revokeObjectURL(url);
        showToast("Export lấy trực tiếp từ API.");
      } catch (error) { setGlobalMessage(safeDetail(error), "error"); }
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
      button.disabled = true;
      try {
        await apiRequest("/api/v1/rule-versions", { method: "POST", body: body });
        showToast("Draft metadata đã được API tạo.");
        setView("rules");
      } catch (error) { $("#ruleError").textContent = safeDetail(error); button.disabled = false; }
    });
    viewContent.querySelectorAll("[data-test-rule]").forEach(function (button) {
      button.addEventListener("click", async function () {
        button.disabled = true;
        try {
          state.lastRuleTest = await apiRequest("/api/v1/rule-versions/" + encodeURIComponent(button.dataset.testRule) + "/test", { method: "POST" });
          showToast("API chỉ xác nhận kiểm tra schema.");
          setView("rules");
        } catch (error) { setGlobalMessage(safeDetail(error), "error"); button.disabled = false; }
      });
    });
    viewContent.querySelectorAll("[data-activate-rule]").forEach(function (button) {
      button.addEventListener("click", async function () {
        button.disabled = true;
        try {
          await apiRequest("/api/v1/rule-versions/" + encodeURIComponent(button.dataset.activateRule) + "/activate", { method: "POST" });
          setGlobalMessage("API đã trả phản hồi kích hoạt; cần kiểm tra trạng thái từ API.", "warning");
          setView("rules");
        } catch (error) {
          setGlobalMessage(safeDetail(error), error.status === 409 ? "warning" : "error");
          button.disabled = false;
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
      : emptyState("API trả về nhật ký rỗng", "Chưa có event trong bộ nhớ Gateway.");
    viewContent.innerHTML = '<div class="panel-grid">' + panel("Audit events", "GET /api/v1/audit-events · " + events.length + " bản ghi", body) + "</div>";
  }

  function apiValueText(value) {
    if (value === null || value === undefined) return "null";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
  }

  function patientRecordsTable(items, action) {
    if (!items.length) return emptyState("API trả về danh sách rỗng", "Không có bản ghi từ endpoint này.");
    const keys = Array.from(new Set(items.flatMap(function (item) { return Object.keys(item || {}); })));
    if (!keys.length) return emptyState("API trả về bản ghi không có trường", "Không có nội dung để hiển thị.");
    return '<div class="data-table-wrap"><table class="data-table"><thead><tr>' +
      keys.map(function (key) { return "<th>" + escapeHTML(key) + "</th>"; }).join("") +
      (action ? "<th>Thao tác</th>" : "") + "</tr></thead><tbody>" +
      items.map(function (item) {
        const cells = keys.map(function (key) { return "<td>" + escapeHTML(apiValueText(item[key])) + "</td>"; }).join("");
        return "<tr>" + cells + (action ? "<td>" + action(item) + "</td>" : "") + "</tr>";
      }).join("") + "</tbody></table></div>";
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
        panel("Bác sĩ do API trả về", "GET /api/v1/patient/doctors", patientRecordsTable(state.patientData.doctors), "half");
      actions = function (item) {
        const id = item.id || item.appointment_id;
        return id ? '<button class="button" type="button" data-cancel-appointment="' + escapeHTML(id) + '">Hủy lịch</button>' : "Không có ID từ API";
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
        return id ? '<button class="button" type="button" data-reminder-id="' + escapeHTML(id) + '" data-reminder-status="taken">Đã dùng · taken</button> <button class="button" type="button" data-reminder-id="' + escapeHTML(id) + '" data-reminder-status="skipped">Bỏ qua · skipped</button>' : "Không có ID từ API";
      };
    }
    const title = view === "appointments" ? "Lịch hẹn" : view === "measurements" ? "Số đo" : view === "prescriptions" ? "Đơn thuốc" : "Nhắc nhở";
    const route = patientCollectionPath(view);
    viewContent.innerHTML = '<div class="panel-grid">' + extra +
      panel(title + " do API trả về", "GET " + route + " · " + state.patientData[view].length + " bản ghi",
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
      button.disabled = true;
      try {
        await apiRequest("/api/v1/patient/appointments", { method: "POST", body: body });
        showToast("Yêu cầu lịch hẹn đã được API xử lý.");
        setView(view);
      } catch (error) { $("#appointmentError").textContent = safeDetail(error); button.disabled = false; }
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
      button.disabled = true;
      try {
        await apiRequest("/api/v1/patient/measurements", { method: "POST", body: body });
        showToast("Số đo synthetic đã được API lưu.");
        setView(view);
      } catch (error) { $("#measurementError").textContent = safeDetail(error); button.disabled = false; }
    });
    viewContent.querySelectorAll("[data-cancel-appointment]").forEach(function (button) {
      button.addEventListener("click", async function () {
        button.disabled = true;
        try {
          await apiRequest("/api/v1/patient/appointments/" + encodeURIComponent(button.dataset.cancelAppointment) + "/cancel", { method: "POST" });
          showToast("API đã xử lý yêu cầu hủy lịch.");
          setView(view);
        } catch (error) { setGlobalMessage(safeDetail(error), error.status === 409 ? "warning" : "error"); button.disabled = false; }
      });
    });
    viewContent.querySelectorAll("[data-reminder-id]").forEach(function (button) {
      button.addEventListener("click", async function () {
        const id = button.dataset.reminderId;
        const status = button.dataset.reminderStatus;
        viewContent.querySelectorAll('[data-reminder-id="' + CSS.escape(id) + '"]').forEach(function (control) { control.disabled = true; });
        try {
          await apiRequest("/api/v1/patient/reminders/" + encodeURIComponent(id), { method: "PATCH", body: { status: status } });
          showToast("Trạng thái nhắc nhở đã được API cập nhật.");
          setView(view);
        } catch (error) {
          setGlobalMessage(safeDetail(error), error.status === 409 ? "warning" : "error");
          viewContent.querySelectorAll('[data-reminder-id="' + CSS.escape(id) + '"]').forEach(function (control) { control.disabled = false; });
        }
      });
    });
  }
  function showApp() {
    loginView.hidden = true;
    appView.hidden = false;
    $("#userLabel").textContent = state.username || "";
    $("#roleLabel").textContent = roleLabels[state.role] || "";
    $("#userInitial").textContent = (state.username || "U").slice(0, 1).toUpperCase();
    renderNavigation();
    setView("overview");
  }

  async function submitLogin(event) {
    event.preventDefault();
    loginMessage.textContent = "";
    const username = loginRole.value;
    if (!supportedAccounts.includes(username)) { showUnsupportedRole(username); return; }
    const button = $("#loginButton");
    button.disabled = true;
    button.querySelector("span").textContent = "Đang đăng nhập";
    try {
      const result = await apiRequest("/api/v1/auth/token", {
        method: "POST", auth: false,
        body: { username: username, password: loginPassword.value }
      });
      if (!result || !result.access_token) throw { status: 0, detail: "Token không có trong response API." };
      state.token = result.access_token;
      state.username = username;
      state.role = accountRoles[username];
      sessionStorage.setItem(TOKEN_KEY, result.access_token);
      sessionStorage.setItem(USER_KEY, username);
      loginPassword.value = "";
      showApp();
    } catch (error) {
      loginMessage.textContent = safeDetail(error);
    } finally {
      button.disabled = !supportedAccounts.includes(loginRole.value);
      button.querySelector("span").textContent = "Đăng nhập";
    }
  }

  loginRole.addEventListener("change", function () { showUnsupportedRole(loginRole.value); });
  loginForm.addEventListener("submit", submitLogin);
  async function logout() {
    if (!state.token) { endSession("Đã đăng xuất khỏi phiên demo."); return; }
    try {
      await apiRequest("/api/v1/auth/logout", { method: "POST" });
      endSession("Đã đăng xuất khỏi phiên demo.");
    } catch (error) {
      if (error && error.status === 401) {
        endSession("Phiên đã hết hạn hoặc bị thu hồi.");
        return;
      }
      setGlobalMessage("Không thể xác nhận thu hồi phiên trên máy chủ. Hãy thử lại khi Gateway sẵn sàng.", "error");
    }
  }
  $("#logoutButton").addEventListener("click", logout);
  $("#navToggle").addEventListener("click", function () {
    const open = !document.body.classList.contains("nav-open");
    document.body.classList.toggle("nav-open", open);
    scrim.hidden = !open;
    $("#navToggle").setAttribute("aria-expanded", open ? "true" : "false");
  });
  scrim.addEventListener("click", closeNav);

  function initialize() {
    showUnsupportedRole(loginRole.value);
    const savedToken = sessionStorage.getItem(TOKEN_KEY);
    const savedUser = sessionStorage.getItem(USER_KEY);
    if (savedToken && supportedAccounts.includes(savedUser)) {
      state.token = savedToken;
      state.username = savedUser;
      state.role = accountRoles[savedUser];
      loginRole.value = savedUser;
      showApp();
    }
  }

  initialize();
})();
