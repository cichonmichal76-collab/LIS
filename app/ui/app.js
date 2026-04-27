const storageKey = "lis-core-token"

const navSections = [
  {
    label: "Command Center",
    items: [
      {
        id: "dashboard",
        icon: "CC",
        label: "Overview",
        blurb: "Task-oriented home, alert tiles, queue drill-down.",
      },
      {
        id: "fhir",
        icon: "FH",
        label: "FHIR Facade",
        blurb: "Interoperability surface and capability matrix.",
      },
    ],
  },
  {
    label: "Clinical Flow",
    items: [
      {
        id: "patients",
        icon: "PT",
        label: "Patients",
        blurb: "Registry, demographics, accession-ready lookup.",
      },
      {
        id: "catalog",
        icon: "TC",
        label: "Test Catalog",
        blurb: "Orderables, analytes, specimen rules, units.",
      },
      {
        id: "orders",
        icon: "OR",
        label: "Orders",
        blurb: "Requisitions, items, status transitions, intake.",
      },
      {
        id: "specimens",
        icon: "SP",
        label: "Specimens",
        blurb: "Barcode-first lifecycle and traceability timeline.",
      },
      {
        id: "tasks",
        icon: "TK",
        label: "Tasks",
        blurb: "Pending worklists, claims, bench ownership.",
      },
      {
        id: "observations",
        icon: "OB",
        label: "Observations",
        blurb: "Results, technical verification, abnormal flags.",
      },
      {
        id: "reports",
        icon: "RP",
        label: "Reports",
        blurb: "Sign-out workspace, versions, PDF delivery.",
      },
    ],
  },
  {
    label: "Quality and Rules",
    items: [
      {
        id: "qc",
        icon: "QC",
        label: "Quality Control",
        blurb: "Materials, lots, Westgard rules, release gates.",
      },
      {
        id: "autoverification",
        icon: "AV",
        label: "Autoverification",
        blurb: "Rule engines, evaluate/apply, held vs auto-finalized.",
      },
    ],
  },
  {
    label: "Connectivity",
    items: [
      {
        id: "devices",
        icon: "DV",
        label: "Devices",
        blurb: "Instrument registry, mappings, method configuration.",
      },
      {
        id: "integrations",
        icon: "IF",
        label: "Interfaces",
        blurb: "HL7, ASTM, device gateway ingest and trace logs.",
      },
      {
        id: "transport",
        icon: "TR",
        label: "Transport",
        blurb: "Sessions, retry policy, quarantine, replay telemetry.",
      },
    ],
  },
  {
    label: "Governance",
    items: [
      {
        id: "audit",
        icon: "AU",
        label: "Audit Trail",
        blurb: "Append-only audit and provenance workbench.",
      },
    ],
  },
]

const quickLinks = [
  { label: "Swagger UI", href: "/docs" },
  { label: "OpenAPI JSON", href: "/openapi.json" },
  { label: "Checked-in contract", href: "/openapi/lis-internal-v1.yaml" },
  { label: "FHIR metadata", href: "/fhir/R4/metadata" },
  { label: "Health endpoint", href: "/health" },
  { label: "JSON root", href: "/?format=json" },
]

const pageBlueprints = {
  dashboard: {
    section: "Command Center",
    title: "Laboratory command center",
    subtitle:
      "A task-oriented homepage modeled on current LIS patterns: work tiles, queue health, abnormal visibility, and one-screen drill-down.",
    context: [
      {
        title: "Task-oriented home",
        body: "The landing view favors workload and queue state over marketing cards, mirroring the job-list-first approach highlighted by major LIS vendors.",
      },
      {
        title: "Alert-led results",
        body: "Abnormal, urgent, held, and error states stay visible through chips and counts so users can prioritize review quickly.",
      },
      {
        title: "Single-screen drill-down",
        body: "Tiles and tables are arranged so users can jump from overview into orders, specimens, QC, interfaces, and audit without changing mental context.",
      },
    ],
    ribbon: [
      { label: "Patients", route: "patients", tone: "primary" },
      { label: "Orders", route: "orders", tone: "secondary" },
      { label: "Specimens", route: "specimens", tone: "secondary" },
      { label: "Bench tasks", route: "tasks", tone: "secondary" },
    ],
  },
  patients: {
    section: "Clinical Flow",
    title: "Patient registry",
    subtitle:
      "Fast demographic capture, identity lookup, and FHIR-facing patient records in a clean, accession-ready grid.",
    context: [
      {
        title: "Registration at a glance",
        body: "Patient views stay dense and scannable, with MRN and demographic data exposed in one compact registry.",
      },
      {
        title: "Minimal-click intake",
        body: "Create form and list stay together so front-desk or accessioning staff do not bounce between separate admin screens.",
      },
    ],
    ribbon: [
      { label: "Create patient", anchor: "patient-form", tone: "primary" },
      { label: "Orders", route: "orders", tone: "secondary" },
      { label: "FHIR Patient", href: "/fhir/R4/Patient", tone: "secondary" },
    ],
  },
  catalog: {
    section: "Clinical Flow",
    title: "Test catalog",
    subtitle:
      "Orderables, analytes, specimen constraints, and units presented as a configurable bench-ready dictionary.",
    context: [
      {
        title: "Shared master data",
        body: "Catalog rows drive orders, devices, QC, and autoverification, so this view behaves like a true LIS control plane.",
      },
      {
        title: "Dense but readable",
        body: "The layout keeps analyte code, specimen type, and result type visible in one scan line, mirroring enterprise LIS setup screens.",
      },
    ],
    ribbon: [
      { label: "Create test", anchor: "catalog-form", tone: "primary" },
      { label: "Devices", route: "devices", tone: "secondary" },
      { label: "QC", route: "qc", tone: "secondary" },
    ],
  },
  orders: {
    section: "Clinical Flow",
    title: "Order entry and worklists",
    subtitle:
      "A requisition-centric workspace with patient linkage, live item detail, and quick hold or cancel actions for order lines.",
    context: [
      {
        title: "Order browser plus detail",
        body: "Vendors often pair a master worklist with a single selected case detail pane; this page follows that pattern for rapid triage.",
      },
      {
        title: "Direct status control",
        body: "Order-item actions stay close to the selected requisition so interruptions and clarifications can be handled inline.",
      },
    ],
    ribbon: [
      { label: "New order", anchor: "order-form", tone: "primary" },
      { label: "Specimens", route: "specimens", tone: "secondary" },
      { label: "Reports", route: "reports", tone: "secondary" },
    ],
  },
  specimens: {
    section: "Clinical Flow",
    title: "Specimen flow and traceability",
    subtitle:
      "Accessioning, collection, receipt, acceptance, rejection, and trace events arranged as one barcode-first lifecycle screen.",
    context: [
      {
        title: "Barcode-first workflow",
        body: "Specimen pages are designed around accession numbers and event history because traceability is the operational center of a modern LIS.",
      },
      {
        title: "Timeline visibility",
        body: "Lifecycle events are shown as a readable chain so bench staff can understand state transitions without opening audit logs.",
      },
    ],
    ribbon: [
      { label: "Accession specimen", anchor: "specimen-form", tone: "primary" },
      { label: "Receive selected", clickHandler: "quickReceiveSelectedSpecimen", tone: "secondary" },
      { label: "Accept selected", clickHandler: "quickAcceptSelectedSpecimen", tone: "secondary" },
    ],
  },
  tasks: {
    section: "Clinical Flow",
    title: "Bench task orchestration",
    subtitle:
      "Digital pending lists, queue ownership, and quick task transitions shaped around the technician and pathologist workbench.",
    context: [
      {
        title: "Pending-list UX",
        body: "Task queues stay list-heavy and role-aware, reflecting how production LIS products expose daily bench work and follow-up items.",
      },
      {
        title: "One-click progression",
        body: "Claim, start, complete, pause, and fail actions are adjacent to the selected task so users keep momentum in repetitive workflows.",
      },
    ],
    ribbon: [
      { label: "Create task", anchor: "task-form", tone: "primary" },
      { label: "Claim selected", clickHandler: "claimSelectedTask", tone: "secondary" },
      { label: "Complete selected", clickHandler: "completeSelectedTask", tone: "secondary" },
    ],
  },
  observations: {
    section: "Clinical Flow",
    title: "Observation review",
    subtitle:
      "Manual entry, result flags, QC gate awareness, technical verification, and autoverification hooks on one analytical review page.",
    context: [
      {
        title: "Flag-first result reading",
        body: "Abnormal and interpretation markers appear directly in the table because vendors emphasize result exceptions, not hidden metadata.",
      },
      {
        title: "Verification nearby",
        body: "Verification and correction controls stay close to the selected result so technical review remains fast and accountable.",
      },
    ],
    ribbon: [
      { label: "Manual result", anchor: "observation-form", tone: "primary" },
      { label: "Verify selected", clickHandler: "verifySelectedObservation", tone: "secondary" },
      { label: "Autoverify page", route: "autoverification", tone: "secondary" },
    ],
  },
  reports: {
    section: "Clinical Flow",
    title: "Reporting and sign-out",
    subtitle:
      "Case-style reporting with versions, PDF placeholders, release status, and controlled amend or authorize actions.",
    context: [
      {
        title: "Case-centric sign-out",
        body: "Selected report detail behaves like a sign-out workspace, with versions and release status exposed before downstream distribution.",
      },
      {
        title: "Result-to-report continuity",
        body: "Observation linkage, authorization, and amendment remain visible together to reduce handoff friction between technical and clinical review.",
      },
    ],
    ribbon: [
      { label: "Generate report", anchor: "report-form", tone: "primary" },
      { label: "Authorize selected", clickHandler: "authorizeSelectedReport", tone: "secondary" },
      { label: "Open PDF", clickHandler: "openSelectedReportPdf", tone: "secondary" },
    ],
  },
  qc: {
    section: "Quality and Rules",
    title: "Quality control engine",
    subtitle:
      "QC materials, lots, rules, runs, result entry, and gate decisions in a dense operational layout built for continuous bench review.",
    context: [
      {
        title: "Rule and run coexistence",
        body: "Production QC screens usually put configuration and daily run state side-by-side; this page follows the same operational rhythm.",
      },
      {
        title: "Release-gate awareness",
        body: "QC is positioned as a precondition for release, not a side module, so failed or warning states remain visible near results workflows.",
      },
    ],
    ribbon: [
      { label: "New QC run", anchor: "qc-run-form", tone: "primary" },
      { label: "Evaluate selected run", clickHandler: "evaluateSelectedQcRun", tone: "secondary" },
      { label: "Observations", route: "observations", tone: "secondary" },
    ],
  },
  autoverification: {
    section: "Quality and Rules",
    title: "Autoverification rules",
    subtitle:
      "Rule maintenance, preview evaluation, and apply workflows arranged like a decision-support console instead of a hidden back-office form.",
    context: [
      {
        title: "Decision support visible to operators",
        body: "Rather than bury rule logic, the screen makes pass or hold reasons visible so bench staff understand why a result did or did not auto-finalize.",
      },
      {
        title: "Scoped rules",
        body: "Device, catalog, and specimen type scopes remain visible because real LIS products expose those filters prominently in rule maintenance.",
      },
    ],
    ribbon: [
      { label: "Create rule", anchor: "autoverification-form", tone: "primary" },
      { label: "Evaluate observation", clickHandler: "evaluateAutoverificationFromRibbon", tone: "secondary" },
      { label: "Apply observation", clickHandler: "applyAutoverificationFromRibbon", tone: "secondary" },
    ],
  },
  devices: {
    section: "Connectivity",
    title: "Device registry and mappings",
    subtitle:
      "Instrument onboarding, mapping maintenance, and method visibility arranged as a central integration registry.",
    context: [
      {
        title: "Registry-led configuration",
        body: "Devices and code mappings are grouped like an interface catalog, which mirrors how vendors present analyzer setup and test routing.",
      },
      {
        title: "Configuration next to usage",
        body: "Mappings sit beside the selected device so support staff can configure routing without leaving operational context.",
      },
    ],
    ribbon: [
      { label: "New device", anchor: "device-form", tone: "primary" },
      { label: "Add mapping", anchor: "mapping-form", tone: "secondary" },
      { label: "Transport", route: "transport", tone: "secondary" },
    ],
  },
  integrations: {
    section: "Connectivity",
    title: "Interfaces and ingest",
    subtitle:
      "HL7, ASTM, and gateway ingress designed as a message trace workspace with operational import controls close at hand.",
    context: [
      {
        title: "Message traceability",
        body: "Inbound and outbound logs remain visible next to import controls so analysts can correlate payloads with created entities quickly.",
      },
      {
        title: "Workflow plus payload",
        body: "Interface screens combine transport detail with business outcome, mirroring LIS integration consoles that blend messaging and clinical artifacts.",
      },
    ],
    ribbon: [
      { label: "HL7 order import", anchor: "hl7-oml-form", tone: "primary" },
      { label: "ASTM result import", anchor: "astm-form", tone: "secondary" },
      { label: "Gateway ingest", anchor: "gateway-form", tone: "secondary" },
    ],
  },
  transport: {
    section: "Connectivity",
    title: "Analyzer transport runtime",
    subtitle:
      "Profiles, sessions, retry states, queue counts, runtime events, and outbound payload control presented like an operations console.",
    context: [
      {
        title: "Operations-console structure",
        body: "Profiles, sessions, and runtime metrics coexist because transport work is primarily operational, not purely administrative.",
      },
      {
        title: "Retry and quarantine visibility",
        body: "Leases, reconnects, awaiting ACK, dead letters, and quarantines stay visible as first-class states instead of hidden diagnostics.",
      },
    ],
    ribbon: [
      { label: "Create profile", anchor: "transport-profile-form", tone: "primary" },
      { label: "Create session", anchor: "transport-session-form", tone: "secondary" },
      { label: "Queue outbound", anchor: "transport-queue-form", tone: "secondary" },
    ],
  },
  audit: {
    section: "Governance",
    title: "Audit and provenance",
    subtitle:
      "Append-only operational history with entity-level drill-down so traceability is readable without opening separate compliance tools.",
    context: [
      {
        title: "Read-first compliance",
        body: "Audit screens are dense and evidence-oriented, with entity type, action, timestamp, and upstream context exposed directly in the grid.",
      },
      {
        title: "Provenance stays operational",
        body: "Provenance is treated as part of the workflow record, not a detached document, which keeps traceability useful for day-to-day troubleshooting.",
      },
    ],
    ribbon: [
      { label: "Refresh view", clickHandler: "reloadCurrentRoute", tone: "primary" },
      { label: "Reports", route: "reports", tone: "secondary" },
      { label: "Transport", route: "transport", tone: "secondary" },
    ],
  },
  fhir: {
    section: "Command Center",
    title: "FHIR interoperability facade",
    subtitle:
      "Capability statement, resource coverage, and direct endpoint links arranged as an integration-facing launchpad.",
    context: [
      {
        title: "External facade awareness",
        body: "This view surfaces the current read and search interactions so interface teams can verify scope quickly.",
      },
      {
        title: "Bridging internal and external",
        body: "The page links resource-level FHIR endpoints back to the internal LIS workbench so staff can move between operational and integration perspectives.",
      },
    ],
    ribbon: [
      { label: "Open metadata", href: "/fhir/R4/metadata", tone: "primary" },
      { label: "Patients", route: "patients", tone: "secondary" },
      { label: "Reports", route: "reports", tone: "secondary" },
    ],
  },
}

const state = {
  authToken: localStorage.getItem(storageKey) || "",
  currentUser: null,
  health: null,
  route: "dashboard",
  searchQuery: "",
  notice: null,
  cache: {
    overview: null,
    patients: [],
    catalog: [],
    orders: [],
    orderDetails: {},
    specimens: [],
    specimenTrace: null,
    tasks: [],
    observations: [],
    observationDetail: null,
    observationGate: null,
    observationRuns: [],
    reports: [],
    reportDetail: null,
    qcMaterials: [],
    qcLots: [],
    qcRules: [],
    qcRuns: [],
    qcRunDetail: null,
    autoverificationRules: [],
    autoverificationPreview: null,
    devices: [],
    deviceMappings: [],
    interfaceMessages: [],
    rawMessages: [],
    transportProfiles: [],
    transportSessions: [],
    transportMessages: [],
    transportFrames: [],
    transportOverview: null,
    transportMetrics: null,
    transportEvents: [],
    audit: [],
    provenance: [],
    fhirMetadata: null,
  },
  selected: {
    patientId: null,
    orderId: null,
    specimenId: null,
    taskId: null,
    observationId: null,
    reportId: null,
    qcRunId: null,
    deviceId: null,
    transportSessionId: null,
  },
}

const elements = {
  authMessage: document.getElementById("authMessage"),
  bootstrapForm: document.getElementById("bootstrapForm"),
  bootstrapMessage: document.getElementById("bootstrapMessage"),
  commandRibbon: document.getElementById("commandRibbon"),
  contextPanel: document.getElementById("contextPanel"),
  globalSearch: document.getElementById("globalSearch"),
  loginForm: document.getElementById("loginForm"),
  logoutButton: document.getElementById("logoutButton"),
  pageContent: document.getElementById("pageContent"),
  pageHero: document.getElementById("pageHero"),
  pageNotice: document.getElementById("pageNotice"),
  pageSection: document.getElementById("pageSection"),
  pageSubtitle: document.getElementById("pageSubtitle"),
  pageTitle: document.getElementById("pageTitle"),
  quickLinks: document.getElementById("quickLinks"),
  ribbonStatus: document.getElementById("ribbonStatus"),
  sessionBadge: document.getElementById("sessionBadge"),
  sessionInfo: document.getElementById("sessionInfo"),
  sidebarHealth: document.getElementById("sidebarHealth"),
  sidebarNav: document.getElementById("sidebarNav"),
  sidebarVersion: document.getElementById("sidebarVersion"),
  topbarBadges: document.getElementById("topbarBadges"),
  usernameInput: document.getElementById("usernameInput"),
  passwordInput: document.getElementById("passwordInput"),
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;")
}

function formatDate(value) {
  if (!value) {
    return "Not set"
  }
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
  })
}

function formatDateTime(value) {
  if (!value) {
    return "Not set"
  }
  return new Date(value).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

function formatNumber(value) {
  return new Intl.NumberFormat().format(Number(value || 0))
}

function formatJsonPreview(value) {
  return escapeHtml(JSON.stringify(value ?? {}, null, 2))
}

function toneForStatus(status) {
  const normalized = String(status ?? "").toLowerCase()
  if (
    normalized.includes("final") ||
    normalized.includes("completed") ||
    normalized.includes("accepted") ||
    normalized.includes("authorized") ||
    normalized.includes("pass") ||
    normalized === "ok" ||
    normalized === "active"
  ) {
    return "ok"
  }
  if (
    normalized.includes("fail") ||
    normalized.includes("reject") ||
    normalized.includes("error") ||
    normalized.includes("quarantine") ||
    normalized.includes("dead") ||
    normalized.includes("warning")
  ) {
    return "warning"
  }
  if (
    normalized.includes("preliminary") ||
    normalized.includes("awaiting") ||
    normalized.includes("ready") ||
    normalized.includes("received") ||
    normalized.includes("held") ||
    normalized.includes("sending") ||
    normalized.includes("receiving") ||
    normalized.includes("in_progress")
  ) {
    return "brand"
  }
  return "neutral"
}

function statusPill(status) {
  const tone = toneForStatus(status)
  return `<span class="status-pill tone-${tone}">${escapeHtml(status)}</span>`
}

function miniTag(label, tone = "neutral") {
  return `<span class="mini-tag tone-${tone}">${escapeHtml(label)}</span>`
}

function readText(form, name) {
  return form.elements[name]?.value?.trim() ?? ""
}

function readOptionalText(form, name) {
  const value = readText(form, name)
  return value || null
}

function readNumber(form, name) {
  const value = readText(form, name)
  return value ? Number(value) : null
}

function readBoolean(form, name) {
  return Boolean(form.elements[name]?.checked)
}

function readDate(form, name) {
  const value = readText(form, name)
  return value || null
}

function readDateTime(form, name) {
  const value = readText(form, name)
  return value ? new Date(value).toISOString() : null
}

function readJson(form, name, fallback) {
  const raw = readText(form, name)
  if (!raw) {
    return fallback
  }
  return JSON.parse(raw)
}

function nowLocalInputValue() {
  const now = new Date()
  const minutes = String(now.getMinutes()).padStart(2, "0")
  const hours = String(now.getHours()).padStart(2, "0")
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")
  return `${now.getFullYear()}-${month}-${day}T${hours}:${minutes}`
}

function currentPage() {
  return pageBlueprints[state.route] || pageBlueprints.dashboard
}

function resolveRoute() {
  const hash = window.location.hash.replace(/^#\/?/, "")
  return pageBlueprints[hash] ? hash : "dashboard"
}

function setSessionBadge(kind, label) {
  elements.sessionBadge.textContent = label
  elements.sessionBadge.className = `utility-badge utility-badge-${kind}`
}

function setMessage(target, text, tone = "neutral") {
  target.textContent = text
  target.className = `message${tone === "neutral" ? "" : ` is-${tone}`}`
}

function setPageNotice(text, tone = "ok") {
  state.notice = { text, tone }
  renderPageNotice()
}

function clearPageNotice() {
  state.notice = null
  renderPageNotice()
}

function renderPageNotice() {
  if (!state.notice?.text) {
    elements.pageNotice.hidden = true
    elements.pageNotice.textContent = ""
    elements.pageNotice.className = "page-notice"
    return
  }

  elements.pageNotice.hidden = false
  elements.pageNotice.textContent = state.notice.text
  elements.pageNotice.className = `page-notice is-${state.notice.tone}`
}

function updateSidebarRuntime() {
  const health = state.health
  elements.sidebarVersion.textContent = health ? `v${health.version}` : "v-"
  elements.sidebarHealth.textContent = health ? `${health.status} / ${health.database_backend}` : "Unavailable"
  elements.sidebarHealth.className = "runtime-pill"
  if (!health) {
    elements.sidebarHealth.classList.add("is-warning")
    return
  }
  elements.sidebarHealth.classList.add(health.status === "ok" ? "is-ok" : "is-warning")
}

function renderQuickLinks() {
  elements.quickLinks.innerHTML = quickLinks
    .map(
      (link) =>
        `<a href="${link.href}" target="_blank" rel="noreferrer">${escapeHtml(link.label)}</a>`,
    )
    .join("")
}

function renderSidebar() {
  elements.sidebarNav.innerHTML = navSections
    .map(
      (section) => `
        <section class="nav-group">
          <p class="nav-group-label">${escapeHtml(section.label)}</p>
          ${section.items
            .map((item) => {
              const active = item.id === state.route ? " is-active" : ""
              return `
                <a class="nav-item${active}" href="#/${item.id}" data-nav-route="${item.id}">
                  <span class="nav-icon">${escapeHtml(item.icon)}</span>
                  <span class="nav-copy">
                    <strong>${escapeHtml(item.label)}</strong>
                    <span>${escapeHtml(item.blurb)}</span>
                  </span>
                </a>
              `
            })
            .join("")}
        </section>
      `,
    )
    .join("")
}

function renderTopbar(view) {
  const page = currentPage()
  elements.pageSection.textContent = view.section || page.section
  elements.pageTitle.textContent = view.title || page.title
  elements.pageSubtitle.textContent = view.subtitle || page.subtitle
  elements.topbarBadges.innerHTML = (view.badges || [])
    .map((badge) => `<span class="tone-${badge.tone || "neutral"}">${escapeHtml(badge.label)}</span>`)
    .join("")
}

function renderRibbon(actions) {
  elements.commandRibbon.innerHTML = (actions || [])
    .map((action) => {
      if (action.href) {
        return `<a class="button ${buttonToneClass(action.tone)}" href="${action.href}" target="_blank" rel="noreferrer">${escapeHtml(action.label)}</a>`
      }
      if (action.route) {
        return `<button class="button ${buttonToneClass(action.tone)}" type="button" data-nav-route="${action.route}">${escapeHtml(action.label)}</button>`
      }
      if (action.anchor) {
        return `<button class="button ${buttonToneClass(action.tone)}" type="button" data-click-handler="scrollToAnchor" data-anchor="${action.anchor}">${escapeHtml(action.label)}</button>`
      }
      if (action.clickHandler) {
        return `<button class="button ${buttonToneClass(action.tone)}" type="button" data-click-handler="${action.clickHandler}">${escapeHtml(action.label)}</button>`
      }
      return ""
    })
    .join("")
}

function renderContext(items) {
  elements.contextPanel.innerHTML = (items || [])
    .map(
      (item) => `
        <article class="context-item">
          <strong>${escapeHtml(item.title)}</strong>
          <p>${escapeHtml(item.body)}</p>
        </article>
      `,
    )
    .join("")
}

function buttonToneClass(tone) {
  if (tone === "primary") {
    return "button-primary"
  }
  if (tone === "secondary") {
    return "button-secondary"
  }
  if (tone === "danger") {
    return "button-danger"
  }
  return "button-ghost"
}

async function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {})
  headers.set("Accept", "application/json")
  if (state.authToken) {
    headers.set("Authorization", `Bearer ${state.authToken}`)
  }
  const response = await fetch(url, { ...options, headers })
  if (!response.ok) {
    let detail = response.statusText
    try {
      const payload = await response.json()
      detail = payload.detail || JSON.stringify(payload)
    } catch (error) {
      detail = response.statusText
    }
    if (response.status === 401) {
      state.authToken = ""
      localStorage.removeItem(storageKey)
      state.currentUser = null
      setSessionBadge("neutral", "Guest")
    }
    throw new Error(detail || "Request failed.")
  }
  const contentType = response.headers.get("content-type") || ""
  if (contentType.includes("application/json")) {
    return response.json()
  }
  return response.text()
}

async function loadHealth() {
  try {
    state.health = await apiFetch("/health")
  } catch (error) {
    state.health = null
    setPageNotice(`Health check failed: ${error.message}`, "error")
  }
  updateSidebarRuntime()
}

async function loadCurrentUser() {
  if (!state.authToken) {
    state.currentUser = null
    elements.sessionInfo.textContent =
      "Sign in to unlock live worklists, result review, QC controls, and connectivity pages."
    setSessionBadge("neutral", "Guest")
    return
  }
  state.currentUser = await apiFetch("/api/v1/auth/me")
  elements.sessionInfo.textContent =
    `${state.currentUser.display_name} (${state.currentUser.username}) is connected with ${state.currentUser.role_code} rights.`
  setSessionBadge("ok", state.currentUser.role_code)
}

function filterItems(items, fields) {
  if (!state.searchQuery) {
    return items
  }
  return items.filter((item) =>
    fields(item)
      .join(" ")
      .toLowerCase()
      .includes(state.searchQuery),
  )
}

function ensureSelection(key, items) {
  const existingValue = state.selected[key] ? String(state.selected[key]) : null
  if (existingValue && items.some((item) => String(item.id) === existingValue)) {
    return
  }
  state.selected[key] = items[0]?.id || null
}

function selectedFrom(items, key) {
  const current = state.selected[key]
  return items.find((item) => String(item.id) === String(current)) || null
}

async function loadGeneralLookups(force = false) {
  if (!state.authToken) {
    return
  }
  const tasks = []
  if (force || state.cache.patients.length === 0) {
    tasks.push(
      apiFetch("/api/v1/patients").then((payload) => {
        state.cache.patients = payload.items
      }),
    )
  }
  if (force || state.cache.catalog.length === 0) {
    tasks.push(
      apiFetch("/api/v1/test-catalog").then((payload) => {
        state.cache.catalog = payload.items
      }),
    )
  }
  if (force || state.cache.devices.length === 0) {
    tasks.push(
      apiFetch("/api/v1/devices").then((payload) => {
        state.cache.devices = payload.items
      }),
    )
  }
  if (force || state.cache.orders.length === 0) {
    tasks.push(
      apiFetch("/api/v1/orders").then((payload) => {
        state.cache.orders = payload.items
      }),
    )
  }
  await Promise.all(tasks)
}

async function loadOrderDetail(orderId, force = false) {
  if (!state.authToken || !orderId) {
    state.cache.orderDetails[String(orderId || "")] = null
    return
  }
  const key = String(orderId)
  if (!force && state.cache.orderDetails[key]) {
    return
  }
  state.cache.orderDetails[key] = await apiFetch(`/api/v1/orders/${orderId}`)
}

async function loadSpecimenTrace(specimenId, force = false) {
  if (!state.authToken || !specimenId) {
    state.cache.specimenTrace = null
    return
  }
  if (!force && state.cache.specimenTrace?.specimen?.id === specimenId) {
    return
  }
  state.cache.specimenTrace = await apiFetch(`/api/v1/specimens/${specimenId}/trace`)
}

async function loadObservationDetail(observationId, force = false) {
  if (!state.authToken || !observationId) {
    state.cache.observationDetail = null
    state.cache.observationGate = null
    state.cache.observationRuns = []
    return
  }
  if (!force && state.cache.observationDetail?.id === observationId) {
    return
  }
  const [detail, gate, runs] = await Promise.all([
    apiFetch(`/api/v1/observations/${observationId}`),
    apiFetch(`/api/v1/qc/observations/${observationId}/gate`),
    apiFetch(`/api/v1/autoverification/observations/${observationId}/runs`),
  ])
  state.cache.observationDetail = detail
  state.cache.observationGate = gate
  state.cache.observationRuns = runs.items
}

async function loadReportDetail(reportId, force = false) {
  if (!state.authToken || !reportId) {
    state.cache.reportDetail = null
    return
  }
  if (!force && state.cache.reportDetail?.id === reportId) {
    return
  }
  state.cache.reportDetail = await apiFetch(`/api/v1/reports/${reportId}`)
}

async function loadQcRunDetail(runId, force = false) {
  if (!state.authToken || !runId) {
    state.cache.qcRunDetail = null
    return
  }
  if (!force && state.cache.qcRunDetail?.run?.id === runId) {
    return
  }
  state.cache.qcRunDetail = await apiFetch(`/api/v1/qc/runs/${runId}`)
}

async function loadDeviceMappings(deviceId, force = false) {
  if (!state.authToken || !deviceId) {
    state.cache.deviceMappings = []
    return
  }
  const payload = await apiFetch(`/api/v1/devices/${deviceId}/mappings`)
  state.cache.deviceMappings = payload.items
}

async function loadTransportArtifacts(sessionId, force = false) {
  if (!state.authToken || !sessionId) {
    state.cache.transportMessages = []
    state.cache.transportFrames = []
    return
  }
  const [messages, frames] = await Promise.all([
    apiFetch(`/api/v1/analyzer-transport/sessions/${sessionId}/messages`),
    apiFetch(`/api/v1/analyzer-transport/sessions/${sessionId}/frames`),
  ])
  state.cache.transportMessages = messages.items
  state.cache.transportFrames = frames.items
}

async function loadDashboardData(force = false) {
  if (!state.authToken) {
    state.cache.overview = null
    return
  }
  if (!force && state.cache.overview) {
    return
  }
  state.cache.overview = await apiFetch("/api/v1/dashboard/overview")
}

async function loadPatientsData(force = false) {
  if (!state.authToken) {
    state.cache.patients = []
    return
  }
  if (!force && state.cache.patients.length) {
    return
  }
  const payload = await apiFetch("/api/v1/patients")
  state.cache.patients = payload.items
  ensureSelection("patientId", state.cache.patients)
}

async function loadCatalogData(force = false) {
  if (!state.authToken) {
    state.cache.catalog = []
    return
  }
  if (!force && state.cache.catalog.length) {
    return
  }
  const payload = await apiFetch("/api/v1/test-catalog")
  state.cache.catalog = payload.items
}

async function loadOrdersData(force = false) {
  if (!state.authToken) {
    state.cache.orders = []
    return
  }
  const payload = await apiFetch("/api/v1/orders")
  state.cache.orders = payload.items
  ensureSelection("orderId", state.cache.orders)
  if (state.selected.orderId) {
    await loadOrderDetail(state.selected.orderId, force)
  }
  await loadGeneralLookups(force)
}

async function loadSpecimensData(force = false) {
  if (!state.authToken) {
    state.cache.specimens = []
    state.cache.specimenTrace = null
    return
  }
  const payload = await apiFetch("/api/v1/specimens")
  state.cache.specimens = payload.items
  ensureSelection("specimenId", state.cache.specimens)
  if (state.selected.specimenId) {
    await loadSpecimenTrace(state.selected.specimenId, force)
  }
  await loadGeneralLookups(force)
}

async function loadTasksData(force = false) {
  if (!state.authToken) {
    state.cache.tasks = []
    return
  }
  const payload = await apiFetch("/api/v1/tasks")
  state.cache.tasks = payload.items
  ensureSelection("taskId", state.cache.tasks)
  await loadGeneralLookups(force)
}

async function loadObservationsData(force = false) {
  if (!state.authToken) {
    state.cache.observations = []
    return
  }
  const payload = await apiFetch("/api/v1/observations")
  state.cache.observations = payload.items
  ensureSelection("observationId", state.cache.observations)
  if (state.selected.observationId) {
    await loadObservationDetail(state.selected.observationId, force)
  }
  await loadGeneralLookups(force)
}

async function loadReportsData(force = false) {
  if (!state.authToken) {
    state.cache.reports = []
    return
  }
  const payload = await apiFetch("/api/v1/reports")
  state.cache.reports = payload.items
  ensureSelection("reportId", state.cache.reports)
  if (state.selected.reportId) {
    await loadReportDetail(state.selected.reportId, force)
  }
  await loadGeneralLookups(force)
}

async function loadQcData(force = false) {
  if (!state.authToken) {
    state.cache.qcMaterials = []
    state.cache.qcLots = []
    state.cache.qcRules = []
    state.cache.qcRuns = []
    return
  }
  const [materials, lots, rules, runs] = await Promise.all([
    apiFetch("/api/v1/qc/materials"),
    apiFetch("/api/v1/qc/lots"),
    apiFetch("/api/v1/qc/rules"),
    apiFetch("/api/v1/qc/runs"),
  ])
  state.cache.qcMaterials = materials.items
  state.cache.qcLots = lots.items
  state.cache.qcRules = rules.items
  state.cache.qcRuns = runs.items
  ensureSelection("qcRunId", state.cache.qcRuns)
  if (state.selected.qcRunId) {
    await loadQcRunDetail(state.selected.qcRunId, force)
  }
  await loadGeneralLookups(force)
}

async function loadAutoverificationData(force = false) {
  if (!state.authToken) {
    state.cache.autoverificationRules = []
    return
  }
  const payload = await apiFetch("/api/v1/autoverification/rules")
  state.cache.autoverificationRules = payload.items
  await loadGeneralLookups(force)
  if (!state.cache.observations.length) {
    await loadObservationsData(force)
  }
}

async function loadDevicesData(force = false) {
  if (!state.authToken) {
    state.cache.devices = []
    state.cache.deviceMappings = []
    return
  }
  const payload = await apiFetch("/api/v1/devices")
  state.cache.devices = payload.items
  ensureSelection("deviceId", state.cache.devices)
  if (state.selected.deviceId) {
    await loadDeviceMappings(state.selected.deviceId, force)
  }
  await loadCatalogData(force)
}

async function loadIntegrationsData(force = false) {
  if (!state.authToken) {
    state.cache.interfaceMessages = []
    state.cache.rawMessages = []
    return
  }
  const [messages, raw] = await Promise.all([
    apiFetch("/api/v1/integrations/messages"),
    apiFetch("/api/v1/integrations/device-gateway/messages"),
  ])
  state.cache.interfaceMessages = messages.items
  state.cache.rawMessages = raw.items
  await loadGeneralLookups(force)
}

async function loadTransportData(force = false) {
  if (!state.authToken) {
    state.cache.transportProfiles = []
    state.cache.transportSessions = []
    state.cache.transportOverview = null
    state.cache.transportMetrics = null
    state.cache.transportEvents = []
    return
  }
  const [profiles, sessions, overview, metrics, events] = await Promise.all([
    apiFetch("/api/v1/analyzer-transport/profiles"),
    apiFetch("/api/v1/analyzer-transport/sessions"),
    apiFetch("/api/v1/analyzer-transport/runtime/overview"),
    apiFetch("/api/v1/analyzer-transport/runtime/metrics"),
    apiFetch("/api/v1/analyzer-transport/runtime/events"),
  ])
  state.cache.transportProfiles = profiles.items
  state.cache.transportSessions = sessions.items
  state.cache.transportOverview = overview
  state.cache.transportMetrics = metrics
  state.cache.transportEvents = events.items
  ensureSelection("transportSessionId", state.cache.transportSessions)
  if (state.selected.transportSessionId) {
    await loadTransportArtifacts(state.selected.transportSessionId, force)
  }
  await loadDevicesData(force)
}

async function loadAuditData(force = false) {
  if (!state.authToken) {
    state.cache.audit = []
    state.cache.provenance = []
    return
  }
  const [audit, provenance] = await Promise.all([
    apiFetch("/api/v1/audit"),
    apiFetch("/api/v1/provenance"),
  ])
  state.cache.audit = audit.items
  state.cache.provenance = provenance.items
}

async function loadFhirData(force = false) {
  if (!force && state.cache.fhirMetadata) {
    return
  }
  state.cache.fhirMetadata = await apiFetch("/fhir/R4/metadata")
}

const pageLoaders = {
  dashboard: loadDashboardData,
  patients: loadPatientsData,
  catalog: loadCatalogData,
  orders: loadOrdersData,
  specimens: loadSpecimensData,
  tasks: loadTasksData,
  observations: loadObservationsData,
  reports: loadReportsData,
  qc: loadQcData,
  autoverification: loadAutoverificationData,
  devices: loadDevicesData,
  integrations: loadIntegrationsData,
  transport: loadTransportData,
  audit: loadAuditData,
  fhir: loadFhirData,
}

async function loadCurrentRoute(force = false) {
  const loader = pageLoaders[state.route] || pageLoaders.dashboard
  try {
    await loader(force)
  } catch (error) {
    setPageNotice(error.message, "error")
  }
}

function metricCard(label, value, note) {
  return `
    <article class="metric-card">
      <p class="card-kicker">${escapeHtml(label)}</p>
      <strong>${escapeHtml(value)}</strong>
      <p>${escapeHtml(note)}</p>
    </article>
  `
}

function moduleTile(route, title, description) {
  return `
    <a class="module-tile" href="#/${route}" data-nav-route="${route}">
      <p class="card-kicker">${escapeHtml(route)}</p>
      <strong>${escapeHtml(title)}</strong>
      <span>${escapeHtml(description)}</span>
    </a>
  `
}

function tableCard({ title, subtitle, columns, rows, emptyLabel = "No data yet.", compact = false }) {
  return `
    <section class="table-card ${compact ? "table-density-compact" : ""}">
      <div class="table-card-header">
        <div>
          <p class="table-caption">${escapeHtml(title)}</p>
          <h3>${escapeHtml(subtitle)}</h3>
        </div>
      </div>
      <div class="table-wrap">
        ${
          rows.length
            ? `
          <table>
            <thead>
              <tr>${columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr>
            </thead>
            <tbody>${rows.join("")}</tbody>
          </table>
        `
            : `<div class="empty-state">${escapeHtml(emptyLabel)}</div>`
        }
      </div>
    </section>
  `
}

function detailGrid(items) {
  return `
    <div class="detail-list">
      ${items
        .map(
          (item) => `
            <div class="detail-item">
              <span>${escapeHtml(item.label)}</span>
              <strong class="${item.mono ? "mono" : ""}">${escapeHtml(item.value)}</strong>
            </div>
          `,
        )
        .join("")}
    </div>
  `
}

function renderDisabledEmptyState(copy) {
  return `<div class="empty-state">${escapeHtml(copy)}</div>`
}

function selectOptions(items, labelBuilder, selectedValue, placeholder = "Select one") {
  const selectedNormalized = selectedValue ? String(selectedValue) : ""
  return `
    <option value="">${escapeHtml(placeholder)}</option>
    ${items
      .map((item) => {
        const value = String(item.id)
        const selected = value === selectedNormalized ? " selected" : ""
        return `<option value="${escapeHtml(value)}"${selected}>${escapeHtml(labelBuilder(item))}</option>`
      })
      .join("")}
  `
}

function actionLink(route, label) {
  return `<button class="inline-button" type="button" data-nav-route="${route}">${escapeHtml(label)}</button>`
}

function renderDashboardPage() {
  const overview = state.cache.overview
  const auth = Boolean(state.authToken && state.currentUser)
  const stats = overview
    ? overview.metrics.slice(0, 6).map((metric) => metricCard(metric.label, formatNumber(metric.value), metric.hint)).join("")
    : [
        metricCard("Queues", "Live after sign-in", "Workload tiles unlock with an authenticated runtime session."),
        metricCard("Results", "Flagged review", "Result, QC, and release states stay visible in the workbench."),
        metricCard("Interfaces", "Transport-aware", "Connectivity, analyzer sessions, and logs are part of the same shell."),
      ].join("")

  const moduleMarkup = [
    moduleTile("patients", "Patients", "Registry and demographic capture."),
    moduleTile("orders", "Orders", "Requisitions and line-item state."),
    moduleTile("specimens", "Specimens", "Traceability and lifecycle events."),
    moduleTile("tasks", "Bench tasks", "Claims, queue pressure, and ownership."),
    moduleTile("observations", "Observations", "Manual results and verification."),
    moduleTile("reports", "Reports", "Sign-out, authorize, amend, deliver."),
    moduleTile("qc", "Quality control", "Runs, rules, and gate decisions."),
    moduleTile("integrations", "Interfaces", "HL7, ASTM, and gateway ingest."),
  ].join("")

  const queueRows = overview
    ? overview.task_queues.map(
        (item) => `
          <tr>
            <td><strong>${escapeHtml(item.queue_code)}</strong></td>
            <td>${item.total}</td>
            <td>${item.ready}</td>
            <td>${item.in_progress}</td>
            <td>${item.completed}</td>
          </tr>
        `,
      )
    : []

  const recentRows = (items, kind) =>
    items.map(
      (item) => `
        <tr>
          <td><strong>${escapeHtml(item.label)}</strong></td>
          <td>${escapeHtml(item.secondary)}</td>
          <td>${statusPill(item.status)}</td>
          <td>${formatDateTime(item.timestamp)}</td>
          <td>${kind}</td>
        </tr>
      `,
    )

  const recentActivity =
    overview?.recent_orders || overview?.recent_specimens || overview?.recent_tasks
      ? [
          ...(overview?.recent_orders ? recentRows(overview.recent_orders, "Order") : []),
          ...(overview?.recent_specimens ? recentRows(overview.recent_specimens, "Specimen") : []),
          ...(overview?.recent_tasks ? recentRows(overview.recent_tasks, "Task") : []),
        ].slice(0, 12)
      : []

  return {
    badges: [
      { label: auth ? `${state.currentUser.role_code} session` : "Guest mode", tone: auth ? "ok" : "neutral" },
      {
        label: state.health ? `${state.health.database_backend} runtime` : "Database pending",
        tone: state.health?.status === "ok" ? "brand" : "warning",
      },
      { label: auth && overview ? `${overview.metrics.length} live KPIs` : "Design shell active", tone: "neutral" },
    ],
    hero: `
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Task-oriented homepage</p>
          <h2>Operational dashboard inspired by current LIS vendor patterns.</h2>
          <p>
            This homepage prioritizes what laboratory staff actually need to see first: queue
            pressure, flagged states, specimen readiness, report throughput, and connectivity
            issues. The structure is based on recurring motifs across current LIS products,
            translated into a cleaner browser-first shell for this repo.
          </p>
          <div class="status-strip">
            ${miniTag(auth ? "Live runtime connected" : "Guest preview", auth ? "ok" : "neutral")}
            ${miniTag("Worklist drill-down", "brand")}
            ${miniTag("Barcode-centric specimen flow", "neutral")}
            ${miniTag("QC and integration aware", "neutral")}
          </div>
        </div>
        <div class="metric-grid">${stats}</div>
      </div>
    `,
    content: `
      <div class="dashboard-grid">
        <div class="card-stack">
          <section class="panel">
            <div class="panel-header">
              <div>
                <p class="panel-label">Workspace map</p>
                <h2>Core modules</h2>
              </div>
              <span class="panel-microcopy">All subpages share one shell</span>
            </div>
            <div class="module-grid">${moduleMarkup}</div>
          </section>

          ${tableCard({
            title: "Worklists",
            subtitle: "Bench queue pressure",
            columns: ["Queue", "Total", "Ready", "In progress", "Completed"],
            rows: queueRows,
            emptyLabel: auth
              ? "No task queues are available yet for this runtime."
              : "Sign in to load live queue telemetry.",
          })}
        </div>

        <div class="card-stack">
          ${tableCard({
            title: "Operational feed",
            subtitle: "Recent activity across orders, specimens, and tasks",
            columns: ["Label", "Descriptor", "Status", "Timestamp", "Kind"],
            rows: recentActivity,
            emptyLabel: auth
              ? "No recent activity yet."
              : "Sign in to load recent operational activity.",
            compact: true,
          })}

          <section class="insight-card">
            <p class="card-kicker">Design structure</p>
            <h3>Why this shell looks different from a generic dashboard</h3>
            <p>
              LIS users live in dense tables, pending lists, and action ribbons. The layout
              deliberately favors that operational density over consumer-style cards.
            </p>
            <div class="inline-actions">
              ${actionLink("orders", "Review orders")}
              ${actionLink("specimens", "Review specimens")}
              ${actionLink("transport", "Review transport")}
            </div>
          </section>
        </div>
      </div>
    `,
  }
}

function renderPatientsPage() {
  const items = filterItems(state.cache.patients, (patient) => [
    patient.mrn,
    patient.family_name,
    patient.given_name,
    patient.sex_code,
  ])
  ensureSelection("patientId", items)
  const selected = selectedFrom(items, "patientId")
  const rows = items.map((patient) => {
    const selectedClass = String(patient.id) === String(state.selected.patientId) ? " class=\"is-selected\"" : ""
    return `
      <tr${selectedClass} data-select-kind="patientId" data-select-value="${escapeHtml(patient.id)}">
        <td><strong>${escapeHtml(patient.mrn)}</strong></td>
        <td>${escapeHtml(`${patient.family_name}, ${patient.given_name}`)}</td>
        <td>${escapeHtml(patient.sex_code || "-")}</td>
        <td>${formatDate(patient.birth_date)}</td>
        <td>${formatDateTime(patient.created_at)}</td>
      </tr>
    `
  })

  return {
    badges: [
      { label: `${items.length} visible patients`, tone: "brand" },
      { label: state.searchQuery ? `Filtered by "${state.searchQuery}"` : "All registry rows", tone: "neutral" },
      { label: state.currentUser ? state.currentUser.role_code : "Guest", tone: "ok" },
    ],
    hero: `
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Patient-centric intake</p>
          <h2>Registry and rapid demographic capture.</h2>
          <p>
            The patient page keeps list and create controls together so accessioning and front-desk
            users can scan existing records and capture new demographics without modal hopping.
          </p>
        </div>
        <div class="metric-grid">
          ${metricCard("Patients", formatNumber(state.cache.patients.length), "Total rows registered in this runtime.")}
          ${metricCard("Visible now", formatNumber(items.length), "Rows left after the current workspace filter.")}
          ${metricCard("FHIR ready", "Patient", "Direct link-out is available for the selected patient record.")}
        </div>
      </div>
    `,
    content: `
      <div class="page-split">
        <div class="card-stack">
          ${tableCard({
            title: "Registry",
            subtitle: "Patient browser",
            columns: ["MRN", "Name", "Sex", "Birth date", "Created"],
            rows,
            emptyLabel: state.authToken
              ? "No patients match the current filter."
              : "Sign in to browse patient records.",
          })}

          <section class="detail-card">
            <div class="detail-card-header">
              <div>
                <p class="table-caption">Selected record</p>
                <h3>${selected ? escapeHtml(`${selected.family_name}, ${selected.given_name}`) : "No patient selected"}</h3>
              </div>
            </div>
            <div class="detail-body">
              ${
                selected
                  ? `
                ${detailGrid([
                  { label: "Patient ID", value: selected.id, mono: true },
                  { label: "MRN", value: selected.mrn },
                  { label: "Given name", value: selected.given_name },
                  { label: "Family name", value: selected.family_name },
                  { label: "Sex", value: selected.sex_code || "Not set" },
                  { label: "Birth date", value: formatDate(selected.birth_date) },
                ])}
                <div class="inline-actions">
                  <a class="button button-ghost" href="/fhir/R4/Patient/${selected.id}" target="_blank" rel="noreferrer">Open FHIR resource</a>
                  <button class="button button-secondary" type="button" data-nav-route="orders">View orders</button>
                </div>
              `
                  : renderDisabledEmptyState("Select a patient row to inspect identity details.")
              }
            </div>
          </section>
        </div>

        <div class="card-stack">
          <section class="panel" id="patient-form">
            <div class="panel-header">
              <div>
                <p class="panel-label">Create patient</p>
                <h2>Registration form</h2>
              </div>
            </div>
            ${
              state.authToken
                ? `
              <form class="form-stack" data-form-handler="createPatient">
                <div class="form-grid">
                  <label>
                    <span>MRN</span>
                    <input name="mrn" type="text" required placeholder="MRN-2026-001">
                  </label>
                  <label>
                    <span>Sex</span>
                    <select name="sex_code">
                      <option value="">Unspecified</option>
                      <option value="F">F</option>
                      <option value="M">M</option>
                      <option value="X">X</option>
                    </select>
                  </label>
                  <label>
                    <span>Given name</span>
                    <input name="given_name" type="text" required placeholder="Anna">
                  </label>
                  <label>
                    <span>Family name</span>
                    <input name="family_name" type="text" required placeholder="Nowak">
                  </label>
                  <label class="span-2">
                    <span>Birth date</span>
                    <input name="birth_date" type="date">
                  </label>
                </div>
                <button class="button button-primary" type="submit">Create patient</button>
              </form>
            `
                : renderDisabledEmptyState("Sign in with an accessioner or admin role to create patient records.")
            }
          </section>

          <section class="insight-card">
            <p class="card-kicker">Launch points</p>
            <h3>How this subpage fits the broader LIS flow</h3>
            <p>
              New patient records feed order entry, FHIR patient search, and downstream specimen
              accession. The page is intentionally compact because intake users repeat this action often.
            </p>
          </section>
        </div>
      </div>
    `,
  }
}

function renderCatalogPage() {
  const items = filterItems(state.cache.catalog, (test) => [
    test.local_code,
    test.display_name,
    test.kind,
    test.loinc_num,
    test.specimen_type_code,
  ])
  const rows = items.map(
    (test) => `
      <tr>
        <td><strong>${escapeHtml(test.local_code)}</strong></td>
        <td>${escapeHtml(test.display_name)}</td>
        <td>${escapeHtml(test.kind)}</td>
        <td>${escapeHtml(test.specimen_type_code || "-")}</td>
        <td>${escapeHtml(test.result_value_type)}</td>
        <td>${escapeHtml(test.default_ucum || "-")}</td>
      </tr>
    `,
  )

  return {
    badges: [
      { label: `${items.length} visible tests`, tone: "brand" },
      { label: `${state.cache.catalog.filter((item) => item.active).length} active`, tone: "ok" },
      { label: "Master data control", tone: "neutral" },
    ],
    hero: `
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Master data</p>
          <h2>Test definitions that power orders, devices, QC, and result typing.</h2>
          <p>
            Catalog rows are kept dense and configurable, because LIS users need code, specimen,
            and result-type data visible together when onboarding new assays.
          </p>
        </div>
        <div class="metric-grid">
          ${metricCard("Catalog rows", formatNumber(state.cache.catalog.length), "All orderables and analytes in the runtime catalog.")}
          ${metricCard("Visible now", formatNumber(items.length), "Catalog rows left after the current filter.")}
          ${metricCard("Result types", new Set(state.cache.catalog.map((item) => item.result_value_type)).size, "Distinct result payload types supported.")}
        </div>
      </div>
    `,
    content: `
      <div class="page-split">
        <div class="card-stack">
          ${tableCard({
            title: "Catalog",
            subtitle: "Configured tests and orderables",
            columns: ["Code", "Display name", "Kind", "Specimen", "Result type", "Unit"],
            rows,
            emptyLabel: state.authToken
              ? "No catalog rows are available yet."
              : "Sign in to browse the test catalog.",
          })}
        </div>

        <div class="card-stack">
          <section class="panel" id="catalog-form">
            <div class="panel-header">
              <div>
                <p class="panel-label">Create test</p>
                <h2>Catalog maintenance</h2>
              </div>
            </div>
            ${
              state.authToken
                ? `
              <form class="form-stack" data-form-handler="createCatalog">
                <label>
                  <span>Local code</span>
                  <input name="local_code" type="text" required placeholder="GLU">
                </label>
                <label>
                  <span>Display name</span>
                  <input name="display_name" type="text" required placeholder="Glucose">
                </label>
                <div class="mini-form-grid">
                  <label>
                    <span>Kind</span>
                    <select name="kind">
                      <option value="orderable">orderable</option>
                      <option value="panel">panel</option>
                      <option value="analyte">analyte</option>
                      <option value="aoe">aoe</option>
                    </select>
                  </label>
                  <label>
                    <span>Result type</span>
                    <select name="result_value_type">
                      <option value="quantity">quantity</option>
                      <option value="text">text</option>
                      <option value="coded">coded</option>
                      <option value="boolean">boolean</option>
                      <option value="range">range</option>
                      <option value="attachment">attachment</option>
                    </select>
                  </label>
                  <label>
                    <span>LOINC</span>
                    <input name="loinc_num" type="text" placeholder="2345-7">
                  </label>
                  <label>
                    <span>Specimen type</span>
                    <input name="specimen_type_code" type="text" placeholder="serum">
                  </label>
                  <label class="span-2">
                    <span>Default unit</span>
                    <input name="default_ucum" type="text" placeholder="mg/dL">
                  </label>
                </div>
                <button class="button button-primary" type="submit">Create catalog item</button>
              </form>
            `
                : renderDisabledEmptyState("Sign in to maintain the test catalog.")
            }
          </section>
        </div>
      </div>
    `,
  }
}

function renderOrdersPage() {
  const items = filterItems(state.cache.orders, (order) => [
    order.requisition_no,
    order.source_system,
    order.priority,
    order.status,
  ])
  ensureSelection("orderId", items)
  const selectedDetail = state.cache.orderDetails[String(state.selected.orderId)] || null

  const rows = items.map((order) => {
    const selectedClass = String(order.id) === String(state.selected.orderId) ? " class=\"is-selected\"" : ""
    return `
      <tr${selectedClass} data-select-kind="orderId" data-select-value="${escapeHtml(order.id)}">
        <td><strong>${escapeHtml(order.requisition_no)}</strong></td>
        <td>${escapeHtml(order.source_system)}</td>
        <td>${statusPill(order.status)}</td>
        <td>${escapeHtml(order.priority)}</td>
        <td>${formatDateTime(order.ordered_at)}</td>
      </tr>
    `
  })

  const orderItemRows = selectedDetail
    ? selectedDetail.items.map(
        (item) => `
          <tr>
            <td><strong>${item.line_no}</strong></td>
            <td class="mono">${escapeHtml(item.id)}</td>
            <td class="mono">${escapeHtml(item.test_catalog_id)}</td>
            <td>${statusPill(item.status)}</td>
            <td>${escapeHtml(item.priority || "-")}</td>
            <td>
              <div class="row-actions">
                <button class="button button-ghost" type="button" data-click-handler="holdOrderItem" data-order-item-id="${escapeHtml(item.id)}">Hold</button>
                <button class="button button-danger" type="button" data-click-handler="cancelOrderItem" data-order-item-id="${escapeHtml(item.id)}">Cancel</button>
              </div>
            </td>
          </tr>
        `,
      )
    : []

  return {
    badges: [
      { label: `${state.cache.orders.length} total orders`, tone: "brand" },
      { label: `${items.length} visible`, tone: "neutral" },
      {
        label: `${state.cache.orders.filter((item) => item.status === "on_hold").length} on hold`,
        tone: "warning",
      },
    ],
    hero: `
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Order browser</p>
          <h2>Requisition-led intake with visible line-item control.</h2>
          <p>
            This page combines the order browser and a selected requisition detail pane, which
            mirrors the way many LIS products let staff review intake and intervene on order lines.
          </p>
        </div>
        <div class="metric-grid">
          ${metricCard("Orders", formatNumber(state.cache.orders.length), "All requisitions stored in this runtime.")}
          ${metricCard("Visible", formatNumber(items.length), "Orders left after the current filter.")}
          ${metricCard("Selected items", selectedDetail ? formatNumber(selectedDetail.items.length) : "0", "Order items on the selected requisition.")}
        </div>
      </div>
    `,
    content: `
      <div class="page-split">
        <div class="card-stack">
          ${tableCard({
            title: "Orders",
            subtitle: "Requisition browser",
            columns: ["Requisition", "Source", "Status", "Priority", "Ordered at"],
            rows,
            emptyLabel: state.authToken
              ? "No orders match the current filter."
              : "Sign in to browse order worklists.",
          })}

          <section class="detail-card">
            <div class="detail-card-header">
              <div>
                <p class="table-caption">Selected requisition</p>
                <h3>${selectedDetail ? escapeHtml(selectedDetail.requisition_no) : "No order selected"}</h3>
              </div>
            </div>
            <div class="detail-body">
              ${
                selectedDetail
                  ? `
                ${detailGrid([
                  { label: "Order ID", value: selectedDetail.id, mono: true },
                  { label: "Patient ID", value: selectedDetail.patient_id, mono: true },
                  { label: "Source", value: selectedDetail.source_system },
                  { label: "Status", value: selectedDetail.status },
                  { label: "Priority", value: selectedDetail.priority },
                  { label: "Ordered", value: formatDateTime(selectedDetail.ordered_at) },
                ])}
                ${tableCard({
                  title: "Selected order",
                  subtitle: "Line items and action controls",
                  columns: ["Line", "Order item ID", "Catalog ID", "Status", "Priority", "Actions"],
                  rows: orderItemRows,
                  emptyLabel: "This order does not have line items yet.",
                  compact: true,
                })}
              `
                  : renderDisabledEmptyState("Select an order row to inspect its items and status.")
              }
            </div>
          </section>
        </div>

        <div class="card-stack">
          <section class="panel" id="order-form">
            <div class="panel-header">
              <div>
                <p class="panel-label">Create order</p>
                <h2>Requisition entry</h2>
              </div>
            </div>
            ${
              state.authToken
                ? `
              <form class="form-stack" data-form-handler="createOrder">
                <label>
                  <span>Patient</span>
                  <select name="patient_id" required>${selectOptions(
                    state.cache.patients,
                    (patient) => `${patient.family_name}, ${patient.given_name} (${patient.mrn})`,
                    "",
                    "Select patient",
                  )}</select>
                </label>
                <label>
                  <span>Primary test item</span>
                  <select name="test_catalog_id" required>${selectOptions(
                    state.cache.catalog,
                    (item) => `${item.local_code} - ${item.display_name}`,
                    "",
                    "Select test",
                  )}</select>
                </label>
                <div class="mini-form-grid">
                  <label>
                    <span>Source system</span>
                    <input name="source_system" type="text" value="portal" required>
                  </label>
                  <label>
                    <span>Priority</span>
                    <select name="priority">
                      <option value="routine">routine</option>
                      <option value="urgent">urgent</option>
                      <option value="asap">asap</option>
                      <option value="stat">stat</option>
                    </select>
                  </label>
                  <label class="span-2">
                    <span>Ordered at</span>
                    <input name="ordered_at" type="datetime-local" value="${nowLocalInputValue()}" required>
                  </label>
                </div>
                <label>
                  <span>Clinical info</span>
                  <textarea name="clinical_info" placeholder="Optional clinical context"></textarea>
                </label>
                <button class="button button-primary" type="submit">Create order</button>
              </form>
            `
                : renderDisabledEmptyState("Sign in as an accessioner or admin to create orders.")
            }
          </section>

          <section class="insight-card">
            <p class="card-kicker">Workflow note</p>
            <h3>Selected order detail behaves like a worklist side pane</h3>
            <p>
              That pattern is common in LIS UIs because staff often browse many requisitions while
              intervening only on the currently highlighted case.
            </p>
          </section>
        </div>
      </div>
    `,
  }
}

function renderSpecimensPage() {
  const items = filterItems(state.cache.specimens, (specimen) => [
    specimen.accession_no,
    specimen.specimen_type_code,
    specimen.status,
    specimen.order_id,
    specimen.patient_id,
  ])
  ensureSelection("specimenId", items)
  const trace = state.cache.specimenTrace
  const selected = trace?.specimen || selectedFrom(items, "specimenId")
  const rows = items.map((specimen) => {
    const selectedClass = String(specimen.id) === String(state.selected.specimenId) ? " class=\"is-selected\"" : ""
    return `
      <tr${selectedClass} data-select-kind="specimenId" data-select-value="${escapeHtml(specimen.id)}">
        <td><strong>${escapeHtml(specimen.accession_no)}</strong></td>
        <td>${escapeHtml(specimen.specimen_type_code)}</td>
        <td>${statusPill(specimen.status)}</td>
        <td class="mono">${escapeHtml(specimen.order_id)}</td>
        <td>${formatDateTime(specimen.received_at || specimen.collected_at || null)}</td>
      </tr>
    `
  })

  const timelineMarkup = trace?.events?.length
    ? trace.events
        .map(
          (event) => `
            <article class="timeline-item">
              <div>
                <div class="meta-row">
                  ${statusPill(event.event_type)}
                  ${event.location_id ? miniTag(`location ${event.location_id}`, "neutral") : ""}
                </div>
                <h4>${escapeHtml(event.event_type)}</h4>
                <p>${escapeHtml(JSON.stringify(event.details || {}))}</p>
              </div>
              <time>${formatDateTime(event.occurred_at)}</time>
            </article>
          `,
        )
        .join("")
    : renderDisabledEmptyState("Select a specimen to view lifecycle events.")

  return {
    badges: [
      { label: `${state.cache.specimens.length} specimens`, tone: "brand" },
      { label: `${items.length} visible`, tone: "neutral" },
      {
        label: `${state.cache.specimens.filter((item) => item.status === "received").length} received`,
        tone: "ok",
      },
    ],
    hero: `
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Barcode-first lifecycle</p>
          <h2>Accession, trace, and receive without leaving one specimen workspace.</h2>
          <p>
            The specimen screen is structured around accession numbers and event history so bench
            staff can scan state, movement, and collection timing without opening separate dialogs.
          </p>
        </div>
        <div class="metric-grid">
          ${metricCard("Specimens", formatNumber(state.cache.specimens.length), "All specimen records available in this runtime.")}
          ${metricCard("Visible", formatNumber(items.length), "Specimens left after filtering this view.")}
          ${metricCard("Selected timeline", trace?.events?.length || 0, "Lifecycle events on the selected specimen.")}
        </div>
      </div>
    `,
    content: `
      <div class="page-split">
        <div class="card-stack">
          ${tableCard({
            title: "Specimen browser",
            subtitle: "Accession and lifecycle overview",
            columns: ["Accession", "Type", "Status", "Order ID", "Latest timestamp"],
            rows,
            emptyLabel: state.authToken
              ? "No specimens match the current filter."
              : "Sign in to browse specimens.",
          })}

          <section class="detail-card">
            <div class="detail-card-header">
              <div>
                <p class="table-caption">Selected specimen</p>
                <h3>${selected ? escapeHtml(selected.accession_no) : "No specimen selected"}</h3>
              </div>
            </div>
            <div class="detail-body">
              ${
                selected
                  ? `
                ${detailGrid([
                  { label: "Specimen ID", value: selected.id, mono: true },
                  { label: "Order ID", value: selected.order_id, mono: true },
                  { label: "Patient ID", value: selected.patient_id, mono: true },
                  { label: "Type", value: selected.specimen_type_code },
                  { label: "Status", value: selected.status },
                  { label: "Collected", value: formatDateTime(selected.collected_at) },
                  { label: "Received", value: formatDateTime(selected.received_at) },
                ])}
                <section class="panel">
                  <div class="panel-header">
                    <div>
                      <p class="panel-label">Trace</p>
                      <h3>Lifecycle events</h3>
                    </div>
                  </div>
                  <div class="timeline">${timelineMarkup}</div>
                </section>
              `
                  : renderDisabledEmptyState("Select a specimen row to inspect its trace.")
              }
            </div>
          </section>
        </div>

        <div class="card-stack">
          <section class="panel" id="specimen-form">
            <div class="panel-header">
              <div>
                <p class="panel-label">Accession specimen</p>
                <h2>New specimen intake</h2>
              </div>
            </div>
            ${
              state.authToken
                ? `
              <form class="form-stack" data-form-handler="accessionSpecimen">
                <label>
                  <span>Order</span>
                  <select name="order_id" required>${selectOptions(
                    state.cache.orders,
                    (order) => `${order.requisition_no} (${order.status})`,
                    selected?.order_id,
                    "Select order",
                  )}</select>
                </label>
                <label>
                  <span>Patient</span>
                  <select name="patient_id" required>${selectOptions(
                    state.cache.patients,
                    (patient) => `${patient.family_name}, ${patient.given_name} (${patient.mrn})`,
                    selected?.patient_id,
                    "Select patient",
                  )}</select>
                </label>
                <label>
                  <span>Specimen type</span>
                  <input name="specimen_type_code" type="text" value="serum" required>
                </label>
                <button class="button button-primary" type="submit">Accession specimen</button>
              </form>
            `
                : renderDisabledEmptyState("Sign in to accession new specimens.")
            }
          </section>

          <section class="panel">
            <div class="panel-header">
              <div>
                <p class="panel-label">Lifecycle actions</p>
                <h2>Selected specimen controls</h2>
              </div>
            </div>
            ${
              state.authToken && selected
                ? `
              <form class="form-stack" data-form-handler="collectSelectedSpecimen">
                <input type="hidden" name="specimen_id" value="${escapeHtml(selected.id)}">
                <label>
                  <span>Collect at</span>
                  <input name="collected_at" type="datetime-local" value="${nowLocalInputValue()}">
                </label>
                <label>
                  <span>Container barcode</span>
                  <input name="container_barcodes" type="text" placeholder="Optional, comma separated">
                </label>
                <button class="button button-secondary" type="submit">Collect specimen</button>
              </form>
              <form class="form-stack" data-form-handler="receiveSelectedSpecimen">
                <input type="hidden" name="specimen_id" value="${escapeHtml(selected.id)}">
                <label>
                  <span>Receive at</span>
                  <input name="received_at" type="datetime-local" value="${nowLocalInputValue()}">
                </label>
                <button class="button button-secondary" type="submit">Receive specimen</button>
              </form>
              <div class="inline-actions">
                <button class="button button-primary" type="button" data-click-handler="acceptSelectedSpecimen">Accept selected</button>
              </div>
              <form class="form-stack" data-form-handler="rejectSelectedSpecimen">
                <input type="hidden" name="specimen_id" value="${escapeHtml(selected.id)}">
                <label>
                  <span>Rejection reason</span>
                  <input name="rejection_reason_code" type="text" placeholder="hemolyzed">
                </label>
                <label>
                  <span>Notes</span>
                  <textarea name="notes" placeholder="Optional rejection notes"></textarea>
                </label>
                <button class="button button-danger" type="submit">Reject selected</button>
              </form>
            `
                : renderDisabledEmptyState("Select a specimen and sign in to use lifecycle actions.")
            }
          </section>
        </div>
      </div>
    `,
  }
}

function renderTasksPage() {
  const items = filterItems(state.cache.tasks, (task) => [
    task.queue_code,
    task.status,
    task.business_status,
    task.focus_type,
    task.focus_id,
  ])
  ensureSelection("taskId", items)
  const selected = selectedFrom(items, "taskId")
  const rows = items.map((task) => {
    const selectedClass = String(task.id) === String(state.selected.taskId) ? " class=\"is-selected\"" : ""
    return `
      <tr${selectedClass} data-select-kind="taskId" data-select-value="${escapeHtml(task.id)}">
        <td><strong>${escapeHtml(task.queue_code)}</strong></td>
        <td>${escapeHtml(task.focus_type)}</td>
        <td>${statusPill(task.status)}</td>
        <td>${escapeHtml(task.business_status || "-")}</td>
        <td>${escapeHtml(task.priority || "-")}</td>
        <td>${formatDateTime(task.authored_on)}</td>
      </tr>
    `
  })

  return {
    badges: [
      { label: `${state.cache.tasks.length} tasks`, tone: "brand" },
      { label: `${items.filter((task) => task.status === "ready").length} ready`, tone: "ok" },
      { label: `${items.filter((task) => task.status === "in_progress").length} in progress`, tone: "warning" },
    ],
    hero: `
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Digital pending lists</p>
          <h2>Queue-centric bench work with direct progression controls.</h2>
          <p>
            Task management is intentionally list-dense because bench users need ownership and
            work state exposed immediately, not hidden behind individual record pages.
          </p>
        </div>
        <div class="metric-grid">
          ${metricCard("Tasks", formatNumber(state.cache.tasks.length), "All tasks visible in the runtime.")}
          ${metricCard("Ready", formatNumber(items.filter((task) => task.status === "ready").length), "Tasks waiting to be claimed or started.")}
          ${metricCard("Selected", selected ? selected.queue_code : "None", "The active task drives quick actions in the side panel.")}
        </div>
      </div>
    `,
    content: `
      <div class="page-split">
        <div class="card-stack">
          ${tableCard({
            title: "Queue browser",
            subtitle: "Pending and completed tasks",
            columns: ["Queue", "Focus", "Status", "Business status", "Priority", "Authored"],
            rows,
            emptyLabel: state.authToken
              ? "No tasks match the current filter."
              : "Sign in to load bench task queues.",
          })}

          <section class="detail-card">
            <div class="detail-card-header">
              <div>
                <p class="table-caption">Selected task</p>
                <h3>${selected ? escapeHtml(selected.queue_code) : "No task selected"}</h3>
              </div>
            </div>
            <div class="detail-body">
              ${
                selected
                  ? `
                ${detailGrid([
                  { label: "Task ID", value: selected.id, mono: true },
                  { label: "Focus type", value: selected.focus_type },
                  { label: "Focus ID", value: selected.focus_id, mono: true },
                  { label: "Queue", value: selected.queue_code },
                  { label: "Status", value: selected.status },
                  { label: "Business status", value: selected.business_status || "Not set" },
                  { label: "Priority", value: selected.priority || "Not set" },
                  { label: "Owner user", value: selected.owner_user_id || "Unassigned", mono: true },
                  { label: "Due at", value: formatDateTime(selected.due_at) },
                ])}
                <div class="inline-actions">
                  <button class="button button-secondary" type="button" data-click-handler="claimSelectedTask">Claim to me</button>
                  <button class="button button-secondary" type="button" data-click-handler="startSelectedTask">Start</button>
                  <button class="button button-primary" type="button" data-click-handler="completeSelectedTask">Complete</button>
                </div>
                <form class="form-stack" data-form-handler="pauseSelectedTask">
                  <label>
                    <span>Pause reason</span>
                    <input name="reason" type="text" placeholder="Awaiting repeat, maintenance, clarification">
                  </label>
                  <button class="button button-ghost" type="submit">Pause selected task</button>
                </form>
                <form class="form-stack" data-form-handler="failSelectedTask">
                  <label>
                    <span>Failure reason</span>
                    <input name="reason" type="text" placeholder="Instrument fault, sample issue">
                  </label>
                  <button class="button button-danger" type="submit">Fail selected task</button>
                </form>
              `
                  : renderDisabledEmptyState("Select a task to use quick progression controls.")
              }
            </div>
          </section>
        </div>

        <div class="card-stack">
          <section class="panel" id="task-form">
            <div class="panel-header">
              <div>
                <p class="panel-label">Create task</p>
                <h2>Bench queue composer</h2>
              </div>
            </div>
            ${
              state.authToken
                ? `
              <form class="form-stack" data-form-handler="createTask">
                <div class="mini-form-grid">
                  <label>
                    <span>Focus type</span>
                    <select name="focus_type">
                      <option value="order-item">order-item</option>
                      <option value="specimen">specimen</option>
                      <option value="observation">observation</option>
                      <option value="report">report</option>
                    </select>
                  </label>
                  <label>
                    <span>Status</span>
                    <select name="status">
                      <option value="ready">ready</option>
                      <option value="in_progress">in_progress</option>
                      <option value="completed">completed</option>
                    </select>
                  </label>
                  <label class="span-2">
                    <span>Focus ID</span>
                    <input name="focus_id" type="text" placeholder="UUID of order item, specimen, observation, or report" required>
                  </label>
                  <label class="span-2">
                    <span>Based on order item ID</span>
                    <input name="based_on_order_item_id" type="text" placeholder="Optional UUID">
                  </label>
                  <label>
                    <span>Queue code</span>
                    <input name="queue_code" type="text" value="chemistry" required>
                  </label>
                  <label>
                    <span>Priority</span>
                    <input name="priority" type="text" placeholder="stat">
                  </label>
                </div>
                <button class="button button-primary" type="submit">Create task</button>
              </form>
            `
                : renderDisabledEmptyState("Sign in to create bench tasks.")
            }
          </section>
        </div>
      </div>
    `,
  }
}

function renderObservationsPage() {
  const items = filterItems(state.cache.observations, (observation) => [
    observation.code_local,
    observation.status,
    observation.abnormal_flag,
    observation.unit_ucum,
    observation.specimen_id,
  ])
  ensureSelection("observationId", items)
  const selected = state.cache.observationDetail || selectedFrom(items, "observationId")
  const gate = state.cache.observationGate
  const rows = items.map((observation) => {
    const selectedClass =
      String(observation.id) === String(state.selected.observationId) ? " class=\"is-selected\"" : ""
    const value =
      observation.value_num ?? observation.value_text ?? observation.value_boolean ?? observation.value_code ?? "-"
    return `
      <tr${selectedClass} data-select-kind="observationId" data-select-value="${escapeHtml(observation.id)}">
        <td><strong>${escapeHtml(observation.code_local)}</strong></td>
        <td>${escapeHtml(String(value))}</td>
        <td>${escapeHtml(observation.unit_ucum || "-")}</td>
        <td>${statusPill(observation.status)}</td>
        <td>${escapeHtml(observation.abnormal_flag || observation.interpretation_code || "-")}</td>
        <td>${formatDateTime(observation.issued_at || observation.effective_at)}</td>
      </tr>
    `
  })

  const previewRuns = state.cache.observationRuns
    .map(
      (run) => `
        <article class="context-item">
          <strong>${escapeHtml(run.decision)}</strong>
          <p>Evaluated ${formatDateTime(run.evaluated_at)}${run.created_task_id ? ` / task ${run.created_task_id}` : ""}</p>
        </article>
      `,
    )
    .join("")

  return {
    badges: [
      { label: `${state.cache.observations.length} observations`, tone: "brand" },
      {
        label: `${items.filter((item) => item.abnormal_flag || item.interpretation_code).length} flagged`,
        tone: "warning",
      },
      {
        label: gate ? `QC gate ${gate.allowed ? "open" : "blocked"}` : "QC gate pending",
        tone: gate ? (gate.allowed ? "ok" : "warning") : "neutral",
      },
    ],
    hero: `
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Analytical review</p>
          <h2>Result review with QC and autoverification context on the same screen.</h2>
          <p>
            Observations are displayed as a dense clinical browser with the selected result detail,
            QC gate, and autoverification history nearby so technical review stays fast.
          </p>
        </div>
        <div class="metric-grid">
          ${metricCard("Observations", formatNumber(state.cache.observations.length), "All available observations in the runtime.")}
          ${metricCard("Flagged", formatNumber(items.filter((item) => item.abnormal_flag || item.interpretation_code).length), "Rows with abnormal or interpretation markers.")}
          ${metricCard("Selected runs", formatNumber(state.cache.observationRuns.length), "Autoverification history rows for the selected observation.")}
        </div>
      </div>
    `,
    content: `
      <div class="page-split">
        <div class="card-stack">
          ${tableCard({
            title: "Observation browser",
            subtitle: "Results, flags, and review state",
            columns: ["Code", "Value", "Unit", "Status", "Flags", "Issued/effective"],
            rows,
            emptyLabel: state.authToken
              ? "No observations match the current filter."
              : "Sign in to review observations.",
          })}

          <section class="detail-card">
            <div class="detail-card-header">
              <div>
                <p class="table-caption">Selected result</p>
                <h3>${selected ? escapeHtml(selected.code_local) : "No observation selected"}</h3>
              </div>
            </div>
            <div class="detail-body">
              ${
                selected
                  ? `
                ${detailGrid([
                  { label: "Observation ID", value: selected.id, mono: true },
                  { label: "Order item ID", value: selected.order_item_id, mono: true },
                  { label: "Specimen ID", value: selected.specimen_id || "Not linked", mono: true },
                  { label: "Status", value: selected.status },
                  { label: "Value type", value: selected.value_type },
                  {
                    label: "Value",
                    value: String(
                      selected.value_num ??
                        selected.value_text ??
                        selected.value_boolean ??
                        selected.value_code ??
                        "-",
                    ),
                  },
                  { label: "Unit", value: selected.unit_ucum || "Not set" },
                  { label: "Interpretation", value: selected.interpretation_code || "Not set" },
                  { label: "Abnormal flag", value: selected.abnormal_flag || "Not set" },
                ])}
                <div class="two-up">
                  <section class="panel">
                    <div class="panel-header">
                      <div>
                        <p class="panel-label">QC gate</p>
                        <h3>${gate ? (gate.allowed ? "Release allowed" : "Release blocked") : "No gate result"}</h3>
                      </div>
                    </div>
                    ${
                      gate
                        ? `
                      <div class="pill-row">
                        ${miniTag(gate.applies ? "QC applies" : "QC not applicable", gate.applies ? "brand" : "neutral")}
                        ${miniTag(gate.latest_decision || "no latest decision", toneForStatus(gate.latest_decision))}
                      </div>
                      <div class="empty-state">${escapeHtml((gate.reasons || []).join("; ") || "No blocking reasons.")}</div>
                    `
                        : renderDisabledEmptyState("No QC gate information available.")
                    }
                  </section>
                  <section class="panel">
                    <div class="panel-header">
                      <div>
                        <p class="panel-label">Autoverification runs</p>
                        <h3>History</h3>
                      </div>
                    </div>
                    ${previewRuns || renderDisabledEmptyState("No autoverification runs recorded yet.")}
                  </section>
                </div>
                <div class="inline-actions">
                  <button class="button button-secondary" type="button" data-click-handler="verifySelectedObservation">Technical verify</button>
                  <button class="button button-secondary" type="button" data-click-handler="evaluateAutoverificationFromRibbon">Evaluate auto</button>
                  <button class="button button-primary" type="button" data-click-handler="applyAutoverificationFromRibbon">Apply auto</button>
                </div>
              `
                  : renderDisabledEmptyState("Select an observation row to inspect result detail.")
              }
            </div>
          </section>
        </div>

        <div class="card-stack">
          <section class="panel" id="observation-form">
            <div class="panel-header">
              <div>
                <p class="panel-label">Manual result entry</p>
                <h2>Create observation</h2>
              </div>
            </div>
            ${
              state.authToken
                ? `
              <form class="form-stack" data-form-handler="createObservation">
                <div class="mini-form-grid">
                  <label class="span-2">
                    <span>Order item ID</span>
                    <input name="order_item_id" type="text" placeholder="UUID from selected order detail" required>
                  </label>
                  <label class="span-2">
                    <span>Specimen ID</span>
                    <input name="specimen_id" type="text" placeholder="Optional UUID">
                  </label>
                  <label>
                    <span>Code local</span>
                    <input name="code_local" type="text" required placeholder="GLU">
                  </label>
                  <label>
                    <span>Value type</span>
                    <select name="value_type">
                      <option value="quantity">quantity</option>
                      <option value="text">text</option>
                      <option value="boolean">boolean</option>
                    </select>
                  </label>
                  <label>
                    <span>Numeric value</span>
                    <input name="value_num" type="number" step="any" placeholder="105.4">
                  </label>
                  <label>
                    <span>Text value</span>
                    <input name="value_text" type="text" placeholder="Negative">
                  </label>
                  <label>
                    <span>Boolean value</span>
                    <select name="value_boolean">
                      <option value="">Unspecified</option>
                      <option value="true">true</option>
                      <option value="false">false</option>
                    </select>
                  </label>
                  <label>
                    <span>Unit</span>
                    <input name="unit_ucum" type="text" placeholder="mg/dL">
                  </label>
                  <label>
                    <span>Status</span>
                    <select name="status">
                      <option value="preliminary">preliminary</option>
                      <option value="final">final</option>
                      <option value="amended">amended</option>
                    </select>
                  </label>
                  <label>
                    <span>Abnormal flag</span>
                    <input name="abnormal_flag" type="text" placeholder="H">
                  </label>
                </div>
                <button class="button button-primary" type="submit">Create observation</button>
              </form>
            `
                : renderDisabledEmptyState("Sign in to enter manual observations.")
            }
          </section>

          <section class="panel">
            <div class="panel-header">
              <div>
                <p class="panel-label">Correction</p>
                <h2>Selected observation amendment</h2>
              </div>
            </div>
            ${
              state.authToken && selected
                ? `
              <form class="form-stack" data-form-handler="correctSelectedObservation">
                <label>
                  <span>Reason</span>
                  <input name="reason" type="text" placeholder="Transcription error, repeat release">
                </label>
                <button class="button button-danger" type="submit">Mark selected result corrected</button>
              </form>
            `
                : renderDisabledEmptyState("Select an observation and sign in to correct it.")
            }
          </section>
        </div>
      </div>
    `,
  }
}

function renderReportsPage() {
  const items = filterItems(state.cache.reports, (report) => [
    report.report_no,
    report.status,
    report.code_local,
    report.patient_id,
  ])
  ensureSelection("reportId", items)
  const selected = state.cache.reportDetail || selectedFrom(items, "reportId")
  const rows = items.map((report) => {
    const selectedClass = String(report.id) === String(state.selected.reportId) ? " class=\"is-selected\"" : ""
    return `
      <tr${selectedClass} data-select-kind="reportId" data-select-value="${escapeHtml(report.id)}">
        <td><strong>${escapeHtml(report.report_no)}</strong></td>
        <td>${statusPill(report.status)}</td>
        <td class="mono">${escapeHtml(report.order_id)}</td>
        <td>${escapeHtml(report.code_local || "-")}</td>
        <td>${formatDateTime(report.issued_at || report.effective_at)}</td>
      </tr>
    `
  })

  const versionRows = selected
    ? selected.versions.map(
        (version) => `
          <tr>
            <td><strong>${version.version_no}</strong></td>
            <td>${statusPill(version.status)}</td>
            <td>${version.amendment_reason ? escapeHtml(version.amendment_reason) : "-"}</td>
            <td>${formatDateTime(version.signed_at || version.created_at)}</td>
            <td>${version.rendered_pdf_uri ? `<a class="data-link" href="${version.rendered_pdf_uri}" target="_blank" rel="noreferrer">Open PDF</a>` : "-"}</td>
          </tr>
        `,
      )
    : []

  return {
    badges: [
      { label: `${state.cache.reports.length} reports`, tone: "brand" },
      { label: `${items.filter((item) => item.status === "final").length} final`, tone: "ok" },
      { label: `${items.filter((item) => item.status === "preliminary").length} preliminary`, tone: "warning" },
    ],
    hero: `
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Clinical sign-out</p>
          <h2>Reporting workspace with versioned release and amend control.</h2>
          <p>
            The reporting page behaves like a case review station, showing selected report detail,
            versions, PDF handoff, and release actions in the same operational frame.
          </p>
        </div>
        <div class="metric-grid">
          ${metricCard("Reports", formatNumber(state.cache.reports.length), "All reports available in the runtime.")}
          ${metricCard("Visible", formatNumber(items.length), "Reports left after the current filter.")}
          ${metricCard("Selected versions", selected ? formatNumber(selected.versions.length) : "0", "Versions available for the selected report.")}
        </div>
      </div>
    `,
    content: `
      <div class="page-split">
        <div class="card-stack">
          ${tableCard({
            title: "Report browser",
            subtitle: "Generated and finalized reports",
            columns: ["Report no", "Status", "Order ID", "Code local", "Issued/effective"],
            rows,
            emptyLabel: state.authToken
              ? "No reports match the current filter."
              : "Sign in to browse reports.",
          })}

          <section class="detail-card">
            <div class="detail-card-header">
              <div>
                <p class="table-caption">Selected report</p>
                <h3>${selected ? escapeHtml(selected.report_no) : "No report selected"}</h3>
              </div>
            </div>
            <div class="detail-body">
              ${
                selected
                  ? `
                ${detailGrid([
                  { label: "Report ID", value: selected.id, mono: true },
                  { label: "Order ID", value: selected.order_id, mono: true },
                  { label: "Patient ID", value: selected.patient_id, mono: true },
                  { label: "Status", value: selected.status },
                  { label: "Code local", value: selected.code_local || "Not set" },
                  { label: "Conclusion", value: selected.conclusion_text || "Not set" },
                ])}
                ${tableCard({
                  title: "Versions",
                  subtitle: "Release history for the selected report",
                  columns: ["Version", "Status", "Amendment reason", "Signed/created", "PDF"],
                  rows: versionRows,
                  emptyLabel: "No versions are available for this report.",
                  compact: true,
                })}
              `
                  : renderDisabledEmptyState("Select a report to inspect sign-out detail.")
              }
            </div>
          </section>
        </div>

        <div class="card-stack">
          <section class="panel" id="report-form">
            <div class="panel-header">
              <div>
                <p class="panel-label">Generate report</p>
                <h2>Draft reporting</h2>
              </div>
            </div>
            ${
              state.authToken
                ? `
              <form class="form-stack" data-form-handler="generateReport">
                <label>
                  <span>Order</span>
                  <select name="order_id" required>${selectOptions(
                    state.cache.orders,
                    (order) => `${order.requisition_no} (${order.status})`,
                    selected?.order_id,
                    "Select order",
                  )}</select>
                </label>
                <label>
                  <span>Code local</span>
                  <input name="code_local" type="text" placeholder="CHEM-PANEL">
                </label>
                <label>
                  <span>Conclusion</span>
                  <textarea name="conclusion_text" placeholder="Optional conclusion or interpretation"></textarea>
                </label>
                <button class="button button-primary" type="submit">Generate report</button>
              </form>
            `
                : renderDisabledEmptyState("Sign in to generate reports.")
            }
          </section>

          <section class="panel">
            <div class="panel-header">
              <div>
                <p class="panel-label">Release controls</p>
                <h2>Selected report actions</h2>
              </div>
            </div>
            ${
              state.authToken && selected && state.currentUser
                ? `
              <div class="inline-actions">
                <button class="button button-primary" type="button" data-click-handler="authorizeSelectedReport">Authorize selected</button>
                <button class="button button-secondary" type="button" data-click-handler="openSelectedReportPdf">Open latest PDF</button>
              </div>
              <form class="form-stack" data-form-handler="amendSelectedReport">
                <label>
                  <span>Amendment reason</span>
                  <input name="reason" type="text" placeholder="Additional interpretation, corrected wording">
                </label>
                <label>
                  <span>Updated conclusion</span>
                  <textarea name="conclusion_text" placeholder="Optional amended conclusion"></textarea>
                </label>
                <button class="button button-danger" type="submit">Amend selected report</button>
              </form>
            `
                : renderDisabledEmptyState("Select a report and sign in as a pathologist or admin to release it.")
            }
          </section>
        </div>
      </div>
    `,
  }
}

function renderQcPage() {
  const runItems = filterItems(state.cache.qcRuns, (run) => [run.status, run.id, run.lot_id, run.device_id])
  ensureSelection("qcRunId", runItems)
  const selectedRun = state.cache.qcRunDetail
  const runRows = runItems.map((run) => {
    const selectedClass = String(run.id) === String(state.selected.qcRunId) ? " class=\"is-selected\"" : ""
    return `
      <tr${selectedClass} data-select-kind="qcRunId" data-select-value="${escapeHtml(run.id)}">
        <td class="mono"><strong>${escapeHtml(run.id)}</strong></td>
        <td class="mono">${escapeHtml(run.lot_id)}</td>
        <td>${statusPill(run.status)}</td>
        <td>${formatDateTime(run.started_at)}</td>
      </tr>
    `
  })

  const qcMiniTable = (title, subtitle, columns, rows, emptyLabel) =>
    tableCard({ title, subtitle, columns, rows, emptyLabel, compact: true })

  return {
    badges: [
      { label: `${state.cache.qcRuns.length} runs`, tone: "brand" },
      { label: `${state.cache.qcRuns.filter((run) => run.status === "failed").length} failed`, tone: "warning" },
      { label: `${state.cache.qcRules.length} rules`, tone: "neutral" },
    ],
    hero: `
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">QC operations</p>
          <h2>Rules, materials, runs, and gates in one continuous quality workspace.</h2>
          <p>
            QC pages in LIS products are dense by necessity. This layout keeps setup entities and
            live runs together so release gating stays operational instead of hidden in admin screens.
          </p>
        </div>
        <div class="metric-grid">
          ${metricCard("Materials", formatNumber(state.cache.qcMaterials.length), "QC materials configured for the runtime.")}
          ${metricCard("Lots", formatNumber(state.cache.qcLots.length), "QC lots that can be attached to runs.")}
          ${metricCard("Runs", formatNumber(state.cache.qcRuns.length), "QC runs available for review and evaluation.")}
        </div>
      </div>
    `,
    content: `
      <div class="page-split">
        <div class="card-stack">
          <div class="qc-grid">
            ${qcMiniTable(
              "QC materials",
              "Reference materials",
              ["Code", "Name", "Manufacturer"],
              state.cache.qcMaterials.map(
                (item) => `
                  <tr>
                    <td><strong>${escapeHtml(item.code)}</strong></td>
                    <td>${escapeHtml(item.name)}</td>
                    <td>${escapeHtml(item.manufacturer || "-")}</td>
                  </tr>
                `,
              ),
              "No QC materials configured yet.",
            )}
            ${qcMiniTable(
              "QC lots",
              "Lot configuration",
              ["Lot no", "Material ID", "Catalog ID"],
              state.cache.qcLots.map(
                (item) => `
                  <tr>
                    <td><strong>${escapeHtml(item.lot_no)}</strong></td>
                    <td class="mono">${escapeHtml(item.material_id)}</td>
                    <td class="mono">${escapeHtml(item.test_catalog_id)}</td>
                  </tr>
                `,
              ),
              "No QC lots configured yet.",
            )}
            ${qcMiniTable(
              "QC rules",
              "Rule library",
              ["Name", "Type", "Priority"],
              state.cache.qcRules.map(
                (item) => `
                  <tr>
                    <td><strong>${escapeHtml(item.name)}</strong></td>
                    <td>${escapeHtml(item.rule_type)}</td>
                    <td>${escapeHtml(item.priority)}</td>
                  </tr>
                `,
              ),
              "No QC rules configured yet.",
            )}
            ${qcMiniTable(
              "QC runs",
              "Run browser",
              ["Run ID", "Lot ID", "Status", "Started"],
              runRows,
              "No QC runs available yet.",
            )}
          </div>

          <section class="detail-card">
            <div class="detail-card-header">
              <div>
                <p class="table-caption">Selected run</p>
                <h3>${selectedRun?.run ? escapeHtml(selectedRun.run.id) : "No run selected"}</h3>
              </div>
            </div>
            <div class="detail-body">
              ${
                selectedRun?.run
                  ? `
                ${detailGrid([
                  { label: "Run ID", value: selectedRun.run.id, mono: true },
                  { label: "Lot ID", value: selectedRun.run.lot_id, mono: true },
                  { label: "Status", value: selectedRun.run.status },
                  { label: "Device ID", value: selectedRun.run.device_id || "Not set", mono: true },
                  { label: "Started at", value: formatDateTime(selectedRun.run.started_at) },
                  { label: "Evaluated at", value: formatDateTime(selectedRun.run.evaluated_at) },
                ])}
                ${tableCard({
                  title: "Selected run",
                  subtitle: "QC results",
                  columns: ["Result ID", "Catalog ID", "Value", "Decision", "Observed"],
                  rows: selectedRun.results.map(
                    (result) => `
                      <tr>
                        <td class="mono"><strong>${escapeHtml(result.id)}</strong></td>
                        <td class="mono">${escapeHtml(result.test_catalog_id)}</td>
                        <td>${escapeHtml(result.value_num)} ${escapeHtml(result.unit_ucum || "")}</td>
                        <td>${statusPill(result.decision || "-")}</td>
                        <td>${formatDateTime(result.observed_at || result.created_at)}</td>
                      </tr>
                    `,
                  ),
                  emptyLabel: "No QC results captured for this run yet.",
                  compact: true,
                })}
              `
                  : renderDisabledEmptyState("Select a QC run to inspect its evaluated results.")
              }
            </div>
          </section>
        </div>

        <div class="card-stack">
          <section class="panel">
            <div class="panel-header">
              <div>
                <p class="panel-label">Create QC entities</p>
                <h2>Setup controls</h2>
              </div>
            </div>
            ${
              state.authToken
                ? `
              <form class="form-stack" data-form-handler="createQcMaterial">
                <h3 id="qc-material-form">New material</h3>
                <div class="mini-form-grid">
                  <label>
                    <span>Code</span>
                    <input name="code" type="text" placeholder="QC-GLU-01" required>
                  </label>
                  <label>
                    <span>Name</span>
                    <input name="name" type="text" placeholder="Glucose level 1" required>
                  </label>
                  <label class="span-2">
                    <span>Manufacturer</span>
                    <input name="manufacturer" type="text" placeholder="Vendor name">
                  </label>
                </div>
                <button class="button button-primary" type="submit">Create material</button>
              </form>
              <div class="divider"></div>
              <form class="form-stack" data-form-handler="createQcLot">
                <h3 id="qc-lot-form">New lot</h3>
                <label>
                  <span>Material</span>
                  <select name="material_id" required>${selectOptions(
                    state.cache.qcMaterials,
                    (item) => `${item.code} - ${item.name}`,
                    "",
                    "Select material",
                  )}</select>
                </label>
                <label>
                  <span>Catalog item</span>
                  <select name="test_catalog_id" required>${selectOptions(
                    state.cache.catalog,
                    (item) => `${item.local_code} - ${item.display_name}`,
                    "",
                    "Select test",
                  )}</select>
                </label>
                <div class="mini-form-grid">
                  <label>
                    <span>Lot number</span>
                    <input name="lot_no" type="text" placeholder="LOT-2026-01" required>
                  </label>
                  <label>
                    <span>Unit</span>
                    <input name="unit_ucum" type="text" placeholder="mg/dL">
                  </label>
                  <label>
                    <span>Minimum</span>
                    <input name="min_value" type="number" step="any">
                  </label>
                  <label>
                    <span>Maximum</span>
                    <input name="max_value" type="number" step="any">
                  </label>
                </div>
                <button class="button button-secondary" type="submit">Create lot</button>
              </form>
              <div class="divider"></div>
              <form class="form-stack" data-form-handler="createQcRule">
                <h3 id="qc-rule-form">New rule</h3>
                <label>
                  <span>Name</span>
                  <input name="name" type="text" placeholder="Westgard 1_2s chemistry" required>
                </label>
                <div class="mini-form-grid">
                  <label>
                    <span>Rule type</span>
                    <select name="rule_type">
                      <option value="range">range</option>
                      <option value="westgard_12s">westgard_12s</option>
                      <option value="westgard_13s">westgard_13s</option>
                      <option value="westgard_22s">westgard_22s</option>
                    </select>
                  </label>
                  <label>
                    <span>Priority</span>
                    <input name="priority" type="number" value="100">
                  </label>
                </div>
                <label>
                  <span>Params JSON</span>
                  <textarea name="params_json" placeholder='{"min": 80, "max": 120}'>{}</textarea>
                </label>
                <button class="button button-secondary" type="submit">Create rule</button>
              </form>
              <div class="divider"></div>
              <form class="form-stack" data-form-handler="createQcRun" id="qc-run-form">
                <h3>New run</h3>
                <label>
                  <span>Lot</span>
                  <select name="lot_id" required>${selectOptions(
                    state.cache.qcLots,
                    (item) => item.lot_no,
                    selectedRun?.run?.lot_id,
                    "Select lot",
                  )}</select>
                </label>
                <button class="button button-primary" type="submit">Create run</button>
              </form>
            `
                : renderDisabledEmptyState("Sign in to configure QC materials, lots, rules, and runs.")
            }
          </section>

          <section class="panel">
            <div class="panel-header">
              <div>
                <p class="panel-label">Selected run controls</p>
                <h2>Result entry and evaluation</h2>
              </div>
            </div>
            ${
              state.authToken && selectedRun?.run
                ? `
              <form class="form-stack" data-form-handler="createQcResult">
                <label>
                  <span>Test catalog</span>
                  <select name="test_catalog_id" required>${selectOptions(
                    state.cache.catalog,
                    (item) => `${item.local_code} - ${item.display_name}`,
                    "",
                    "Select test",
                  )}</select>
                </label>
                <div class="mini-form-grid">
                  <label>
                    <span>Value</span>
                    <input name="value_num" type="number" step="any" required>
                  </label>
                  <label>
                    <span>Unit</span>
                    <input name="unit_ucum" type="text" placeholder="mg/dL">
                  </label>
                </div>
                <button class="button button-secondary" type="submit" data-qc-run-id="${escapeHtml(selectedRun.run.id)}">Add QC result</button>
              </form>
              <div class="inline-actions">
                <button class="button button-primary" type="button" data-click-handler="evaluateSelectedQcRun">Evaluate selected run</button>
              </div>
            `
                : renderDisabledEmptyState("Select a QC run and sign in to add results or evaluate it.")
            }
          </section>
        </div>
      </div>
    `,
  }
}

function renderAutoverificationPage() {
  const rules = filterItems(state.cache.autoverificationRules, (rule) => [
    rule.name,
    rule.rule_type,
    rule.specimen_type_code,
    rule.id,
  ])
  const preview = state.cache.autoverificationPreview
  const rows = rules.map(
    (rule) => `
      <tr>
        <td><strong>${escapeHtml(rule.name)}</strong></td>
        <td>${escapeHtml(rule.rule_type)}</td>
        <td>${escapeHtml(rule.priority)}</td>
        <td>${escapeHtml(rule.specimen_type_code || "-")}</td>
        <td class="mono">${escapeHtml(rule.device_id || "-")}</td>
      </tr>
    `,
  )

  return {
    badges: [
      { label: `${state.cache.autoverificationRules.length} rules`, tone: "brand" },
      { label: preview ? `Preview ${preview.mode}` : "No preview loaded", tone: preview ? "ok" : "neutral" },
      { label: `${state.cache.observations.length} observations available`, tone: "neutral" },
    ],
    hero: `
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Decision support</p>
          <h2>Expose rule logic and auto-release outcomes in a usable operations screen.</h2>
          <p>
            The autoverification page keeps rules, evaluation, and apply outcomes close together
            so analysts can understand why a result was held or auto-finalized.
          </p>
        </div>
        <div class="metric-grid">
          ${metricCard("Rules", formatNumber(state.cache.autoverificationRules.length), "Autoverification rules available in the runtime.")}
          ${metricCard("Observations", formatNumber(state.cache.observations.length), "Recent observations that can be evaluated or applied.")}
          ${metricCard("Preview", preview ? preview.title : "Idle", "The result of the latest evaluate or apply action.")}
        </div>
      </div>
    `,
    content: `
      <div class="page-split">
        <div class="card-stack">
          ${tableCard({
            title: "Rules",
            subtitle: "Autoverification rule library",
            columns: ["Name", "Type", "Priority", "Specimen scope", "Device scope"],
            rows,
            emptyLabel: state.authToken
              ? "No autoverification rules configured yet."
              : "Sign in to browse autoverification rules.",
          })}

          <section class="detail-card">
            <div class="detail-card-header">
              <div>
                <p class="table-caption">Preview</p>
                <h3>${preview ? escapeHtml(preview.title) : "No evaluation preview yet"}</h3>
              </div>
            </div>
            <div class="detail-body">
              ${
                preview
                  ? `
                ${detailGrid(preview.summary)}
                <div class="json-preview">${formatJsonPreview(preview.payload)}</div>
              `
                  : renderDisabledEmptyState("Run an evaluate or apply action to inspect rule output here.")
              }
            </div>
          </section>
        </div>

        <div class="card-stack">
          <section class="panel" id="autoverification-form">
            <div class="panel-header">
              <div>
                <p class="panel-label">Create rule</p>
                <h2>Rule maintenance</h2>
              </div>
            </div>
            ${
              state.authToken
                ? `
              <form class="form-stack" data-form-handler="createAutoverificationRule">
                <label>
                  <span>Name</span>
                  <input name="name" type="text" placeholder="Delta check glucose" required>
                </label>
                <div class="mini-form-grid">
                  <label>
                    <span>Rule type</span>
                    <select name="rule_type">
                      <option value="basic">basic</option>
                      <option value="delta">delta</option>
                    </select>
                  </label>
                  <label>
                    <span>Priority</span>
                    <input name="priority" type="number" value="100">
                  </label>
                  <label>
                    <span>Catalog</span>
                    <select name="test_catalog_id">${selectOptions(
                      state.cache.catalog,
                      (item) => `${item.local_code} - ${item.display_name}`,
                      "",
                      "Any catalog item",
                    )}</select>
                  </label>
                  <label>
                    <span>Device</span>
                    <select name="device_id">${selectOptions(
                      state.cache.devices,
                      (item) => `${item.code} - ${item.name}`,
                      "",
                      "Any device",
                    )}</select>
                  </label>
                  <label class="span-2">
                    <span>Specimen type scope</span>
                    <input name="specimen_type_code" type="text" placeholder="serum">
                  </label>
                </div>
                <label>
                  <span>Condition JSON</span>
                  <textarea name="condition_json" placeholder='{"abnormal_flag_not_in": ["H", "L"]}'>{}</textarea>
                </label>
                <button class="button button-primary" type="submit">Create rule</button>
              </form>
            `
                : renderDisabledEmptyState("Sign in to manage autoverification rules.")
            }
          </section>

          <section class="panel">
            <div class="panel-header">
              <div>
                <p class="panel-label">Observation preview</p>
                <h2>Evaluate or apply</h2>
              </div>
            </div>
            ${
              state.authToken
                ? `
              <form class="form-stack" data-form-handler="previewAutoverification">
                <label>
                  <span>Observation ID</span>
                  <input
                    name="observation_id"
                    type="text"
                    value="${escapeHtml(state.selected.observationId || "")}"
                    placeholder="UUID of observation to evaluate"
                    required
                  >
                </label>
                <div class="button-row">
                  <button class="button button-secondary" type="submit" name="mode" value="evaluate">Evaluate</button>
                  <button class="button button-primary" type="submit" name="mode" value="apply">Apply</button>
                </div>
              </form>
            `
                : renderDisabledEmptyState("Sign in to preview autoverification decisions.")
            }
          </section>
        </div>
      </div>
    `,
  }
}

function renderDevicesPage() {
  const items = filterItems(state.cache.devices, (device) => [
    device.code,
    device.name,
    device.manufacturer,
    device.model,
    device.protocol_code,
  ])
  ensureSelection("deviceId", items)
  const selected = selectedFrom(items, "deviceId")
  const rows = items.map((device) => {
    const selectedClass = String(device.id) === String(state.selected.deviceId) ? " class=\"is-selected\"" : ""
    return `
      <tr${selectedClass} data-select-kind="deviceId" data-select-value="${escapeHtml(device.id)}">
        <td><strong>${escapeHtml(device.code)}</strong></td>
        <td>${escapeHtml(device.name)}</td>
        <td>${escapeHtml(device.protocol_code || "-")}</td>
        <td>${escapeHtml(device.manufacturer || "-")}</td>
        <td>${escapeHtml(device.model || "-")}</td>
      </tr>
    `
  })

  const mappingRows = state.cache.deviceMappings.map(
    (mapping) => `
      <tr>
        <td><strong>${escapeHtml(mapping.incoming_test_code)}</strong></td>
        <td class="mono">${escapeHtml(mapping.test_catalog_id)}</td>
        <td>${escapeHtml(mapping.local_code)}</td>
        <td>${escapeHtml(mapping.default_unit_ucum || "-")}</td>
      </tr>
    `,
  )

  return {
    badges: [
      { label: `${state.cache.devices.length} devices`, tone: "brand" },
      { label: `${state.cache.deviceMappings.length} mappings for selected`, tone: "ok" },
      { label: selected ? selected.protocol_code || "No protocol" : "No device", tone: "neutral" },
    ],
    hero: `
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Instrument registry</p>
          <h2>Device onboarding and test-code mapping in one support console.</h2>
          <p>
            Devices stay in a registry-style browser with mappings alongside the selected analyzer,
            following the support-centric pattern used by most production LIS interface modules.
          </p>
        </div>
        <div class="metric-grid">
          ${metricCard("Devices", formatNumber(state.cache.devices.length), "Configured instruments and gateway endpoints.")}
          ${metricCard("Mappings", formatNumber(state.cache.deviceMappings.length), "Incoming-test mappings on the selected device.")}
          ${metricCard("Protocols", new Set(state.cache.devices.map((item) => item.protocol_code || "none")).size, "Distinct protocol families in the registry.")}
        </div>
      </div>
    `,
    content: `
      <div class="page-split">
        <div class="card-stack">
          ${tableCard({
            title: "Device registry",
            subtitle: "Configured instruments",
            columns: ["Code", "Name", "Protocol", "Manufacturer", "Model"],
            rows,
            emptyLabel: state.authToken
              ? "No devices are configured yet."
              : "Sign in to browse the device registry.",
          })}

          <section class="detail-card">
            <div class="detail-card-header">
              <div>
                <p class="table-caption">Selected device</p>
                <h3>${selected ? escapeHtml(selected.name) : "No device selected"}</h3>
              </div>
            </div>
            <div class="detail-body">
              ${
                selected
                  ? `
                ${detailGrid([
                  { label: "Device ID", value: selected.id, mono: true },
                  { label: "Code", value: selected.code },
                  { label: "Protocol", value: selected.protocol_code || "Not set" },
                  { label: "Manufacturer", value: selected.manufacturer || "Not set" },
                  { label: "Model", value: selected.model || "Not set" },
                  { label: "Serial", value: selected.serial_no || "Not set" },
                ])}
                ${tableCard({
                  title: "Mappings",
                  subtitle: "Incoming test codes for the selected device",
                  columns: ["Incoming code", "Catalog ID", "Catalog code", "Default unit"],
                  rows: mappingRows,
                  emptyLabel: "No mappings exist for the selected device.",
                  compact: true,
                })}
              `
                  : renderDisabledEmptyState("Select a device to inspect instrument mappings.")
              }
            </div>
          </section>
        </div>

        <div class="card-stack">
          <section class="panel" id="device-form">
            <div class="panel-header">
              <div>
                <p class="panel-label">Create device</p>
                <h2>Instrument onboarding</h2>
              </div>
            </div>
            ${
              state.authToken
                ? `
              <form class="form-stack" data-form-handler="createDevice">
                <div class="mini-form-grid">
                  <label>
                    <span>Code</span>
                    <input name="code" type="text" placeholder="CHEM-01" required>
                  </label>
                  <label>
                    <span>Name</span>
                    <input name="name" type="text" placeholder="Chemistry Analyzer 01" required>
                  </label>
                  <label>
                    <span>Manufacturer</span>
                    <input name="manufacturer" type="text" placeholder="Vendor">
                  </label>
                  <label>
                    <span>Model</span>
                    <input name="model" type="text" placeholder="Model">
                  </label>
                  <label>
                    <span>Serial number</span>
                    <input name="serial_no" type="text">
                  </label>
                  <label>
                    <span>Protocol</span>
                    <input name="protocol_code" type="text" placeholder="astm">
                  </label>
                </div>
                <button class="button button-primary" type="submit">Create device</button>
              </form>
            `
                : renderDisabledEmptyState("Sign in to register new devices.")
            }
          </section>

          <section class="panel" id="mapping-form">
            <div class="panel-header">
              <div>
                <p class="panel-label">Selected device mapping</p>
                <h2>Add incoming code mapping</h2>
              </div>
            </div>
            ${
              state.authToken && selected
                ? `
              <form class="form-stack" data-form-handler="createDeviceMapping">
                <input type="hidden" name="device_id" value="${escapeHtml(selected.id)}">
                <label>
                  <span>Incoming test code</span>
                  <input name="incoming_test_code" type="text" placeholder="GLU" required>
                </label>
                <label>
                  <span>Catalog item</span>
                  <select name="test_catalog_id" required>${selectOptions(
                    state.cache.catalog,
                    (item) => `${item.local_code} - ${item.display_name}`,
                    "",
                    "Select catalog item",
                  )}</select>
                </label>
                <label>
                  <span>Default unit</span>
                  <input name="default_unit_ucum" type="text" placeholder="mg/dL">
                </label>
                <button class="button button-secondary" type="submit">Add mapping</button>
              </form>
            `
                : renderDisabledEmptyState("Select a device and sign in to create a mapping.")
            }
          </section>
        </div>
      </div>
    `,
  }
}

function renderIntegrationsPage() {
  const interfaceRows = filterItems(state.cache.interfaceMessages, (message) => [
    message.protocol,
    message.message_type,
    message.control_id,
    message.related_entity_type,
  ]).map(
    (message) => `
      <tr>
        <td><strong>${escapeHtml(message.protocol)}</strong></td>
        <td>${escapeHtml(message.message_type)}</td>
        <td>${statusPill(message.processed_ok ? "processed" : "error")}</td>
        <td>${escapeHtml(message.control_id || "-")}</td>
        <td>${escapeHtml(message.related_entity_type || "-")}</td>
        <td>${formatDateTime(message.created_at)}</td>
      </tr>
    `,
  )

  const rawRows = filterItems(state.cache.rawMessages, (message) => [
    message.protocol,
    message.message_type,
    message.accession_no,
    message.specimen_barcode,
  ]).map(
    (message) => `
      <tr>
        <td><strong>${escapeHtml(message.protocol)}</strong></td>
        <td>${escapeHtml(message.message_type || "-")}</td>
        <td>${escapeHtml(message.accession_no || message.specimen_barcode || "-")}</td>
        <td>${statusPill(message.parsed_ok ? "parsed" : "parse_error")}</td>
        <td>${escapeHtml(message.created_observation_count)}</td>
        <td>${formatDateTime(message.created_at)}</td>
      </tr>
    `,
  )

  return {
    badges: [
      { label: `${state.cache.interfaceMessages.length} interface logs`, tone: "brand" },
      { label: `${state.cache.rawMessages.length} raw payloads`, tone: "neutral" },
      {
        label: `${state.cache.rawMessages.filter((item) => !item.parsed_ok).length} parse issues`,
        tone: "warning",
      },
    ],
    hero: `
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Messaging workspace</p>
          <h2>HL7, ASTM, and device ingress with trace logs close to import actions.</h2>
          <p>
            Integration pages combine payload-facing controls and operational message logs so staff
            can see what was sent, what parsed, and what business records were created.
          </p>
        </div>
        <div class="metric-grid">
          ${metricCard("Interface logs", formatNumber(state.cache.interfaceMessages.length), "HL7 and related interface events captured by the runtime.")}
          ${metricCard("Raw messages", formatNumber(state.cache.rawMessages.length), "Device and ASTM raw payloads captured for traceability.")}
          ${metricCard("Parse issues", formatNumber(state.cache.rawMessages.filter((item) => !item.parsed_ok).length), "Messages that did not parse cleanly.")}
        </div>
      </div>
    `,
    content: `
      <div class="card-stack">
        <div class="two-up">
          ${tableCard({
            title: "Interface log",
            subtitle: "Processed HL7 and export events",
            columns: ["Protocol", "Message type", "Status", "Control ID", "Related entity", "Created"],
            rows: interfaceRows,
            emptyLabel: state.authToken
              ? "No interface messages are recorded yet."
              : "Sign in to view interface logs.",
            compact: true,
          })}
          ${tableCard({
            title: "Device gateway",
            subtitle: "Raw analyzer payloads",
            columns: ["Protocol", "Message type", "Accession / barcode", "Parse", "Observations", "Created"],
            rows: rawRows,
            emptyLabel: state.authToken
              ? "No device or ASTM payloads are recorded yet."
              : "Sign in to view gateway payloads.",
            compact: true,
          })}
        </div>

        <div class="three-up">
          <section class="panel" id="hl7-oml-form">
            <div class="panel-header">
              <div>
                <p class="panel-label">HL7 order import</p>
                <h2>OML^O33</h2>
              </div>
            </div>
            ${
              state.authToken
                ? `
              <form class="form-stack" data-form-handler="importHl7Oml">
                <label>
                  <span>Message</span>
                  <textarea name="message" placeholder="Paste inbound OML^O33 payload"></textarea>
                </label>
                <button class="button button-primary" type="submit">Import order message</button>
              </form>
            `
                : renderDisabledEmptyState("Sign in to import HL7 order messages.")
            }
          </section>

          <section class="panel">
            <div class="panel-header">
              <div>
                <p class="panel-label">HL7 result import</p>
                <h2>ORU^R01</h2>
              </div>
            </div>
            ${
              state.authToken
                ? `
              <form class="form-stack" data-form-handler="importHl7Oru">
                <label>
                  <span>Message</span>
                  <textarea name="message" placeholder="Paste inbound ORU^R01 payload"></textarea>
                </label>
                <button class="button button-secondary" type="submit">Import result message</button>
              </form>
            `
                : renderDisabledEmptyState("Sign in to import HL7 result messages.")
            }
          </section>

          <section class="panel" id="astm-form">
            <div class="panel-header">
              <div>
                <p class="panel-label">ASTM import</p>
                <h2>Analyzer results</h2>
              </div>
            </div>
            ${
              state.authToken
                ? `
              <form class="form-stack" data-form-handler="importAstm">
                <label>
                  <span>Device</span>
                  <select name="device_id">${selectOptions(
                    state.cache.devices,
                    (item) => `${item.code} - ${item.name}`,
                    "",
                    "Select device",
                  )}</select>
                </label>
                <label>
                  <span>Message</span>
                  <textarea name="message" placeholder="Paste ASTM payload"></textarea>
                </label>
                <label>
                  <span><input name="auto_verify" type="checkbox"> Auto-apply autoverification</span>
                </label>
                <button class="button button-secondary" type="submit">Import ASTM results</button>
              </form>
            `
                : renderDisabledEmptyState("Sign in to import ASTM results.")
            }
          </section>
        </div>

        <section class="panel" id="gateway-form">
          <div class="panel-header">
            <div>
              <p class="panel-label">Device gateway ingest</p>
              <h2>Structured manual gateway payload</h2>
            </div>
          </div>
          ${
            state.authToken
              ? `
            <form class="form-stack" data-form-handler="ingestDeviceGateway">
              <div class="form-grid">
                <label>
                  <span>Device</span>
                  <select name="device_id">${selectOptions(
                    state.cache.devices,
                    (item) => `${item.code} - ${item.name}`,
                    "",
                    "Select device",
                  )}</select>
                </label>
                <label>
                  <span>Accession no</span>
                  <input name="accession_no" type="text" placeholder="ACC-20260426-0001">
                </label>
              </div>
              <label>
                <span>Results JSON</span>
                <textarea name="results_json" placeholder='[{"incoming_test_code":"GLU","value_type":"quantity","value_num":105.4,"unit_ucum":"mg/dL"}]'>[]</textarea>
              </label>
              <button class="button button-primary" type="submit">Ingest device results</button>
            </form>
          `
              : renderDisabledEmptyState("Sign in to ingest structured device results.")
          }
        </section>
      </div>
    `,
  }
}

function renderTransportPage() {
  const profiles = filterItems(state.cache.transportProfiles, (item) => [
    item.connection_mode,
    item.device_id,
    item.protocol,
  ])
  const sessions = filterItems(state.cache.transportSessions, (item) => [
    item.session_status,
    item.device_id,
    item.profile_id,
  ])
  ensureSelection("transportSessionId", sessions)
  const selectedSession = selectedFrom(sessions, "transportSessionId")
  const overview = state.cache.transportOverview
  const metrics = state.cache.transportMetrics

  return {
    badges: [
      { label: `${profiles.length} profiles`, tone: "brand" },
      { label: `${sessions.length} sessions`, tone: "neutral" },
      { label: `${metrics?.quarantined_message_count || 0} quarantined`, tone: "warning" },
    ],
    hero: `
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Operations console</p>
          <h2>Transport sessions, retries, queues, and runtime events in one screen.</h2>
          <p>
            Analyzer transport is treated like an operational console, with profiles, sessions,
            awaiting ACK states, reconnects, and events visible without leaving the workbench.
          </p>
        </div>
        <div class="metric-grid">
          ${metricCard("Profiles", formatNumber(overview?.profile_count || profiles.length), "Transport profiles configured for analyzers.")}
          ${metricCard("Sessions", formatNumber(overview?.session_count || sessions.length), "Runtime sessions currently known to the transport layer.")}
          ${metricCard("Awaiting ACK", formatNumber(metrics?.awaiting_ack_count || 0), "Outbound messages waiting on acknowledgment.")}
        </div>
      </div>
    `,
    content: `
      <div class="card-stack">
        <div class="three-up">
          ${tableCard({
            title: "Profiles",
            subtitle: "Transport profile definitions",
            columns: ["Device ID", "Connection", "Protocol", "Retries"],
            rows: profiles.map(
              (profile) => `
                <tr>
                  <td class="mono"><strong>${escapeHtml(profile.device_id)}</strong></td>
                  <td>${escapeHtml(profile.connection_mode)}</td>
                  <td>${escapeHtml(profile.protocol)}</td>
                  <td>${escapeHtml(profile.max_retries)}</td>
                </tr>
              `,
            ),
            emptyLabel: state.authToken
              ? "No transport profiles are configured yet."
              : "Sign in to inspect transport profiles.",
            compact: true,
          })}
          ${tableCard({
            title: "Sessions",
            subtitle: "Runtime session browser",
            columns: ["Session ID", "Status", "Device", "Last activity"],
            rows: sessions.map((session) => {
              const selectedClass =
                String(session.id) === String(state.selected.transportSessionId) ? " class=\"is-selected\"" : ""
              return `
                <tr${selectedClass} data-select-kind="transportSessionId" data-select-value="${escapeHtml(session.id)}">
                  <td class="mono"><strong>${escapeHtml(session.id)}</strong></td>
                  <td>${statusPill(session.session_status)}</td>
                  <td class="mono">${escapeHtml(session.device_id)}</td>
                  <td>${formatDateTime(session.last_activity_at)}</td>
                </tr>
              `
            }),
            emptyLabel: state.authToken
              ? "No transport sessions exist yet."
              : "Sign in to inspect transport sessions.",
            compact: true,
          })}
          ${tableCard({
            title: "Runtime events",
            subtitle: "Latest analyzer transport audit events",
            columns: ["Action", "Status", "Entity", "Event at"],
            rows: (state.cache.transportEvents || []).slice(0, 8).map(
              (event) => `
                <tr>
                  <td><strong>${escapeHtml(event.action)}</strong></td>
                  <td>${statusPill(event.status)}</td>
                  <td>${escapeHtml(event.entity_type)}</td>
                  <td>${formatDateTime(event.event_at)}</td>
                </tr>
              `,
            ),
            emptyLabel: state.authToken
              ? "No runtime events are available yet."
              : "Sign in to inspect runtime events.",
            compact: true,
          })}
        </div>

        <div class="page-split">
          <div class="card-stack">
            <section class="detail-card">
              <div class="detail-card-header">
                <div>
                  <p class="table-caption">Selected session</p>
                  <h3>${selectedSession ? escapeHtml(selectedSession.id) : "No transport session selected"}</h3>
                </div>
              </div>
              <div class="detail-body">
                ${
                  selectedSession
                    ? `
                  ${detailGrid([
                    { label: "Status", value: selectedSession.session_status },
                    { label: "Device ID", value: selectedSession.device_id, mono: true },
                    { label: "Profile ID", value: selectedSession.profile_id, mono: true },
                    { label: "Lease owner", value: selectedSession.lease_owner || "Not set" },
                    { label: "Reconnect count", value: selectedSession.reconnect_count },
                    { label: "Last error", value: selectedSession.last_error || "No error" },
                  ])}
                  ${tableCard({
                    title: "Messages",
                    subtitle: "Outbound and inbound session messages",
                    columns: ["Type", "Direction", "Status", "Retries", "Created"],
                    rows: state.cache.transportMessages.map(
                      (message) => `
                        <tr>
                          <td><strong>${escapeHtml(message.message_type)}</strong></td>
                          <td>${escapeHtml(message.direction)}</td>
                          <td>${statusPill(message.transport_status)}</td>
                          <td>${escapeHtml(message.retry_count)}</td>
                          <td>${formatDateTime(message.created_at)}</td>
                        </tr>
                      `,
                    ),
                    emptyLabel: "No messages recorded for the selected session.",
                    compact: true,
                  })}
                `
                    : renderDisabledEmptyState("Select a transport session to inspect its state and messages.")
                }
              </div>
            </section>
          </div>

          <div class="card-stack">
            <section class="panel" id="transport-profile-form">
              <div class="panel-header">
                <div>
                  <p class="panel-label">Create profile</p>
                  <h2>Transport profile</h2>
                </div>
              </div>
              ${
                state.authToken
                  ? `
                <form class="form-stack" data-form-handler="createTransportProfile">
                  <label>
                    <span>Device</span>
                    <select name="device_id">${selectOptions(
                      state.cache.devices,
                      (item) => `${item.code} - ${item.name}`,
                      "",
                      "Select device",
                    )}</select>
                  </label>
                  <div class="mini-form-grid">
                    <label>
                      <span>Connection mode</span>
                      <select name="connection_mode">
                        <option value="mock">mock</option>
                        <option value="tcp-client">tcp-client</option>
                        <option value="serial">serial</option>
                      </select>
                    </label>
                    <label>
                      <span>Max retries</span>
                      <input name="max_retries" type="number" value="3">
                    </label>
                    <label>
                      <span>TCP host</span>
                      <input name="tcp_host" type="text" placeholder="127.0.0.1">
                    </label>
                    <label>
                      <span>TCP port</span>
                      <input name="tcp_port" type="number" placeholder="5000">
                    </label>
                  </div>
                  <div class="button-row">
                    <button class="button button-primary" type="submit">Create profile</button>
                  </div>
                </form>
              `
                  : renderDisabledEmptyState("Sign in to create transport profiles.")
              }
            </section>

            <section class="panel" id="transport-session-form">
              <div class="panel-header">
                <div>
                  <p class="panel-label">Create session</p>
                  <h2>Runtime session</h2>
                </div>
              </div>
              ${
                state.authToken
                  ? `
                <form class="form-stack" data-form-handler="createTransportSession">
                  <label>
                    <span>Device</span>
                    <select name="device_id">${selectOptions(
                      state.cache.devices,
                      (item) => `${item.code} - ${item.name}`,
                      "",
                      "Select device",
                    )}</select>
                  </label>
                  <label>
                    <span>Profile</span>
                    <select name="profile_id">${selectOptions(
                      state.cache.transportProfiles,
                      (item) => `${item.connection_mode} / ${item.device_id}`,
                      "",
                      "Select profile",
                    )}</select>
                  </label>
                  <button class="button button-secondary" type="submit">Create session</button>
                </form>
              `
                  : renderDisabledEmptyState("Sign in to create transport sessions.")
              }
            </section>

            <section class="panel" id="transport-queue-form">
              <div class="panel-header">
                <div>
                  <p class="panel-label">Queue outbound</p>
                  <h2>Message composer</h2>
                </div>
              </div>
              ${
                state.authToken
                  ? `
                <form class="form-stack" data-form-handler="queueTransportMessage">
                  <label>
                    <span>Session</span>
                    <select name="session_id">${selectOptions(
                      state.cache.transportSessions,
                      (item) => `${item.session_status} / ${item.device_id}`,
                      selectedSession?.id,
                      "Select session",
                    )}</select>
                  </label>
                  <label>
                    <span>Message type</span>
                    <input name="message_type" type="text" value="ASTM-WORKLIST">
                  </label>
                  <label>
                    <span>Logical payload</span>
                    <textarea name="logical_payload" placeholder="Paste ASTM logical payload"></textarea>
                  </label>
                  <button class="button button-primary" type="submit">Queue outbound message</button>
                </form>
              `
                  : renderDisabledEmptyState("Sign in to queue outbound transport messages.")
              }
            </section>
          </div>
        </div>
      </div>
    `,
  }
}

function renderAuditPage() {
  const auditRows = filterItems(state.cache.audit, (item) => [
    item.entity_type,
    item.action,
    item.status,
    item.entity_id,
  ]).map(
    (item) => `
      <tr>
        <td><strong>${escapeHtml(item.entity_type)}</strong></td>
        <td>${escapeHtml(item.action)}</td>
        <td>${statusPill(item.status)}</td>
        <td class="mono">${escapeHtml(item.entity_id)}</td>
        <td>${formatDateTime(item.event_at)}</td>
      </tr>
    `,
  )

  const provenanceRows = filterItems(state.cache.provenance, (item) => [
    item.target_resource_type,
    item.activity_code,
    item.target_resource_id,
  ]).map(
    (item) => `
      <tr>
        <td><strong>${escapeHtml(item.target_resource_type)}</strong></td>
        <td>${escapeHtml(item.activity_code)}</td>
        <td class="mono">${escapeHtml(item.target_resource_id)}</td>
        <td>${formatDateTime(item.recorded_at)}</td>
      </tr>
    `,
  )

  return {
    badges: [
      { label: `${state.cache.audit.length} audit events`, tone: "brand" },
      { label: `${state.cache.provenance.length} provenance rows`, tone: "neutral" },
      { label: "Append-only traceability", tone: "ok" },
    ],
    hero: `
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Traceability</p>
          <h2>Operational audit and provenance rendered as readable evidence tables.</h2>
          <p>
            Audit and provenance stay in the same workbench because operational troubleshooting and
            compliance review often happen together in laboratory systems.
          </p>
        </div>
        <div class="metric-grid">
          ${metricCard("Audit events", formatNumber(state.cache.audit.length), "Audit rows across clinical and transport workflows.")}
          ${metricCard("Provenance rows", formatNumber(state.cache.provenance.length), "Provenance records linked to target resources.")}
          ${metricCard("Visible evidence", formatNumber(auditRows.length + provenanceRows.length), "Rows left after applying the current workspace filter.")}
        </div>
      </div>
    `,
    content: `
      <div class="two-up">
        ${tableCard({
          title: "Audit log",
          subtitle: "Entity actions and statuses",
          columns: ["Entity type", "Action", "Status", "Entity ID", "Event at"],
          rows: auditRows,
          emptyLabel: state.authToken
            ? "No audit events match the current filter."
            : "Sign in to inspect audit events.",
        })}
        ${tableCard({
          title: "Provenance",
          subtitle: "Activity and target resource trace",
          columns: ["Resource type", "Activity", "Resource ID", "Recorded at"],
          rows: provenanceRows,
          emptyLabel: state.authToken
            ? "No provenance rows match the current filter."
            : "Sign in to inspect provenance records.",
        })}
      </div>
    `,
  }
}

function renderFhirPage() {
  const resources = state.cache.fhirMetadata?.rest?.[0]?.resource || []
  return {
    badges: [
      { label: `${resources.length} FHIR resources`, tone: "brand" },
      { label: "R4 facade", tone: "ok" },
      { label: "Read and search coverage", tone: "neutral" },
    ],
    hero: `
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Interoperability launchpad</p>
          <h2>FHIR capability, resource coverage, and direct links into the facade.</h2>
          <p>
            This page surfaces the current FHIR R4 capability statement and exposes resource-level
            launch points so interface teams can verify scope without leaving the LIS workbench.
          </p>
        </div>
        <div class="metric-grid">
          ${metricCard("Resources", formatNumber(resources.length), "Resource types advertised by the current capability statement.")}
          ${metricCard("Mode", "R4", "FHIR version currently exposed by the facade.")}
          ${metricCard("Launch points", "Direct links", "Open resource search endpoints straight from the workbench.")}
        </div>
      </div>
    `,
    content: `
      <div class="page-split">
        <div class="card-stack">
          <section class="panel">
            <div class="panel-header">
              <div>
                <p class="panel-label">Resource matrix</p>
                <h2>Capability statement coverage</h2>
              </div>
            </div>
            <div class="resource-grid">
              ${resources
                .map(
                  (resource) => `
                    <article class="resource-card">
                      <h4>${escapeHtml(resource.type)}</h4>
                      <p>${escapeHtml((resource.interaction || []).map((item) => item.code).join(", ") || "No interactions listed")}</p>
                      <div class="inline-actions">
                        <a class="data-link" href="/fhir/R4/${resource.type}" target="_blank" rel="noreferrer">Open endpoint</a>
                      </div>
                    </article>
                  `,
                )
                .join("")}
            </div>
          </section>
        </div>

        <div class="card-stack">
          <section class="insight-card">
            <p class="card-kicker">Capability JSON</p>
            <h3>Direct preview</h3>
            <div class="json-preview">${formatJsonPreview(state.cache.fhirMetadata || {})}</div>
          </section>
        </div>
      </div>
    `,
  }
}

const pageRenderers = {
  dashboard: renderDashboardPage,
  patients: renderPatientsPage,
  catalog: renderCatalogPage,
  orders: renderOrdersPage,
  specimens: renderSpecimensPage,
  tasks: renderTasksPage,
  observations: renderObservationsPage,
  reports: renderReportsPage,
  qc: renderQcPage,
  autoverification: renderAutoverificationPage,
  devices: renderDevicesPage,
  integrations: renderIntegrationsPage,
  transport: renderTransportPage,
  audit: renderAuditPage,
  fhir: renderFhirPage,
}

function renderCurrentRoute() {
  renderSidebar()
  renderPageNotice()
  const page = currentPage()
  const renderer = pageRenderers[state.route] || pageRenderers.dashboard
  const view = renderer()
  renderTopbar({
    section: page.section,
    title: page.title,
    subtitle: page.subtitle,
    badges: view.badges,
  })
  renderRibbon(page.ribbon)
  renderContext(page.context)
  elements.pageHero.innerHTML = view.hero
  elements.pageContent.innerHTML = view.content
  elements.ribbonStatus.textContent = "View-aware shortcuts"
}

async function reloadCurrentRoute(force = true) {
  await loadCurrentRoute(force)
  renderCurrentRoute()
}

async function goToRoute(route, force = false) {
  state.route = pageBlueprints[route] ? route : "dashboard"
  if (window.location.hash !== `#/${state.route}`) {
    window.location.hash = `#/${state.route}`
  }
  clearPageNotice()
  await loadCurrentRoute(force)
  renderCurrentRoute()
}

function getSelectedTask() {
  return selectedFrom(state.cache.tasks, "taskId")
}

async function withAction(task, successMessage, reload = true) {
  try {
    await task()
    if (successMessage) {
      setPageNotice(successMessage, "ok")
    }
    if (reload) {
      await reloadCurrentRoute(true)
    } else {
      renderCurrentRoute()
    }
  } catch (error) {
    setPageNotice(error.message, "error")
  }
}

const formHandlers = {
  async createPatient(form) {
    await withAction(async () => {
      await apiFetch("/api/v1/patients", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mrn: readText(form, "mrn"),
          given_name: readText(form, "given_name"),
          family_name: readText(form, "family_name"),
          sex_code: readOptionalText(form, "sex_code"),
          birth_date: readDate(form, "birth_date"),
        }),
      })
      form.reset()
    }, "Patient created.")
  },
  async createCatalog(form) {
    await withAction(async () => {
      await apiFetch("/api/v1/test-catalog", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          local_code: readText(form, "local_code"),
          display_name: readText(form, "display_name"),
          kind: readText(form, "kind"),
          loinc_num: readOptionalText(form, "loinc_num"),
          specimen_type_code: readOptionalText(form, "specimen_type_code"),
          default_ucum: readOptionalText(form, "default_ucum"),
          result_value_type: readText(form, "result_value_type"),
        }),
      })
      form.reset()
    }, "Catalog item created.")
  },
  async createOrder(form) {
    await withAction(async () => {
      await apiFetch("/api/v1/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_id: readText(form, "patient_id"),
          source_system: readText(form, "source_system"),
          priority: readText(form, "priority"),
          clinical_info: readOptionalText(form, "clinical_info"),
          ordered_at: readDateTime(form, "ordered_at"),
          items: [{ test_catalog_id: readText(form, "test_catalog_id") }],
        }),
      })
      form.reset()
    }, "Order created.")
  },
  async accessionSpecimen(form) {
    await withAction(async () => {
      await apiFetch("/api/v1/specimens/accession", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          order_id: readText(form, "order_id"),
          patient_id: readText(form, "patient_id"),
          specimen_type_code: readText(form, "specimen_type_code"),
        }),
      })
    }, "Specimen accessioned.")
  },
  async collectSelectedSpecimen(form) {
    const specimenId = readText(form, "specimen_id") || state.selected.specimenId
    await withAction(async () => {
      const rawBarcodes = readText(form, "container_barcodes")
      const barcodes = rawBarcodes
        ? rawBarcodes
            .split(",")
            .map((value) => value.trim())
            .filter(Boolean)
        : []
      await apiFetch(`/api/v1/specimens/${specimenId}/collect`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          collected_at: readDateTime(form, "collected_at"),
          container_barcodes: barcodes,
        }),
      })
    }, "Specimen collected.")
  },
  async receiveSelectedSpecimen(form) {
    const specimenId = readText(form, "specimen_id") || state.selected.specimenId
    await withAction(async () => {
      await apiFetch(`/api/v1/specimens/${specimenId}/receive`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          received_at: readDateTime(form, "received_at"),
        }),
      })
    }, "Specimen received.")
  },
  async rejectSelectedSpecimen(form) {
    const specimenId = readText(form, "specimen_id") || state.selected.specimenId
    await withAction(async () => {
      await apiFetch(`/api/v1/specimens/${specimenId}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rejection_reason_code: readText(form, "rejection_reason_code"),
          notes: readOptionalText(form, "notes"),
        }),
      })
    }, "Specimen rejected.")
  },
  async createTask(form) {
    await withAction(async () => {
      const payload = {
        focus_type: readText(form, "focus_type"),
        focus_id: readText(form, "focus_id"),
        based_on_order_item_id: readOptionalText(form, "based_on_order_item_id"),
        queue_code: readText(form, "queue_code"),
        status: readText(form, "status"),
        priority: readOptionalText(form, "priority"),
        inputs: {},
      }
      await apiFetch("/api/v1/tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      form.reset()
    }, "Task created.")
  },
  async pauseSelectedTask(form) {
    const task = getSelectedTask()
    if (!task) {
      setPageNotice("Select a task first.", "error")
      return
    }
    await withAction(async () => {
      await apiFetch(`/api/v1/tasks/${task.id}/pause`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reason: readText(form, "reason"),
          comment: readOptionalText(form, "reason"),
        }),
      })
    }, "Task paused.")
  },
  async failSelectedTask(form) {
    const task = getSelectedTask()
    if (!task) {
      setPageNotice("Select a task first.", "error")
      return
    }
    await withAction(async () => {
      await apiFetch(`/api/v1/tasks/${task.id}/fail`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reason: readText(form, "reason"),
          comment: readOptionalText(form, "reason"),
        }),
      })
    }, "Task failed.")
  },
  async createObservation(form) {
    await withAction(async () => {
      const valueType = readText(form, "value_type")
      const payload = {
        order_item_id: readText(form, "order_item_id"),
        specimen_id: readOptionalText(form, "specimen_id"),
        code_local: readText(form, "code_local"),
        status: readText(form, "status"),
        value_type: valueType,
        value_num: valueType === "quantity" ? readNumber(form, "value_num") : null,
        value_text: valueType === "text" ? readOptionalText(form, "value_text") : null,
        value_boolean:
          valueType === "boolean"
            ? readOptionalText(form, "value_boolean") === "true"
            : null,
        unit_ucum: readOptionalText(form, "unit_ucum"),
        abnormal_flag: readOptionalText(form, "abnormal_flag"),
      }
      await apiFetch("/api/v1/observations/manual", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      form.reset()
    }, "Observation created.")
  },
  async correctSelectedObservation(form) {
    const observationId = state.selected.observationId
    if (!observationId) {
      setPageNotice("Select an observation first.", "error")
      return
    }
    await withAction(async () => {
      await apiFetch(`/api/v1/observations/${observationId}/correct`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reason: readText(form, "reason"),
        }),
      })
    }, "Observation marked as corrected.")
  },
  async generateReport(form) {
    await withAction(async () => {
      await apiFetch("/api/v1/reports/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          order_id: readText(form, "order_id"),
          code_local: readOptionalText(form, "code_local"),
          conclusion_text: readOptionalText(form, "conclusion_text"),
        }),
      })
      form.reset()
    }, "Report generated.")
  },
  async amendSelectedReport(form) {
    const reportId = state.selected.reportId
    if (!reportId || !state.currentUser) {
      setPageNotice("Select a report and sign in first.", "error")
      return
    }
    await withAction(async () => {
      await apiFetch(`/api/v1/reports/${reportId}/amend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          signed_by_user_id: state.currentUser.id,
          reason: readText(form, "reason"),
          conclusion_text: readOptionalText(form, "conclusion_text"),
        }),
      })
    }, "Report amended.")
  },
  async createQcMaterial(form) {
    await withAction(async () => {
      await apiFetch("/api/v1/qc/materials", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: readText(form, "code"),
          name: readText(form, "name"),
          manufacturer: readOptionalText(form, "manufacturer"),
        }),
      })
      form.reset()
    }, "QC material created.")
  },
  async createQcLot(form) {
    await withAction(async () => {
      await apiFetch("/api/v1/qc/lots", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          material_id: readText(form, "material_id"),
          lot_no: readText(form, "lot_no"),
          test_catalog_id: readText(form, "test_catalog_id"),
          unit_ucum: readOptionalText(form, "unit_ucum"),
          min_value: readNumber(form, "min_value"),
          max_value: readNumber(form, "max_value"),
        }),
      })
    }, "QC lot created.")
  },
  async createQcRule(form) {
    await withAction(async () => {
      await apiFetch("/api/v1/qc/rules", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: readText(form, "name"),
          priority: readNumber(form, "priority") || 100,
          rule_type: readText(form, "rule_type"),
          params: readJson(form, "params_json", {}),
        }),
      })
    }, "QC rule created.")
  },
  async createQcRun(form) {
    await withAction(async () => {
      await apiFetch("/api/v1/qc/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lot_id: readText(form, "lot_id"),
        }),
      })
    }, "QC run created.")
  },
  async createQcResult(form) {
    const runId = state.selected.qcRunId
    if (!runId) {
      setPageNotice("Select a QC run first.", "error")
      return
    }
    await withAction(async () => {
      await apiFetch(`/api/v1/qc/runs/${runId}/results`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          test_catalog_id: readText(form, "test_catalog_id"),
          value_num: readNumber(form, "value_num"),
          unit_ucum: readOptionalText(form, "unit_ucum"),
        }),
      })
    }, "QC result added.")
  },
  async createAutoverificationRule(form) {
    await withAction(async () => {
      await apiFetch("/api/v1/autoverification/rules", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: readText(form, "name"),
          priority: readNumber(form, "priority") || 100,
          test_catalog_id: readOptionalText(form, "test_catalog_id"),
          device_id: readOptionalText(form, "device_id"),
          specimen_type_code: readOptionalText(form, "specimen_type_code"),
          rule_type: readText(form, "rule_type"),
          condition: readJson(form, "condition_json", {}),
        }),
      })
      form.reset()
    }, "Autoverification rule created.")
  },
  async previewAutoverification(form, submitter) {
    const mode = submitter?.value || "evaluate"
    const observationId = readText(form, "observation_id")
    if (!observationId) {
      setPageNotice("Observation ID is required.", "error")
      return
    }
    await withAction(async () => {
      const endpoint =
        mode === "apply"
          ? `/api/v1/autoverification/observations/${observationId}/apply`
          : `/api/v1/autoverification/observations/${observationId}/evaluate`
      const payload = await apiFetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      })
      state.cache.autoverificationPreview = {
        mode,
        title: mode === "apply" ? "Apply outcome" : "Evaluation outcome",
        payload,
        summary:
          mode === "apply"
            ? [
                { label: "Observation", value: payload.observation_id, mono: true },
                { label: "Decision", value: payload.decision },
                { label: "Matched rules", value: payload.matched_rule_count },
                { label: "Created task", value: payload.created_task_id || "None", mono: true },
              ]
            : [
                { label: "Observation", value: payload.observation_id, mono: true },
                { label: "Overall", value: payload.overall_decision },
                { label: "Matched rules", value: payload.matched_rule_count },
                { label: "Previous final", value: payload.previous_final_observation_id || "None", mono: true },
              ],
      }
    }, `Autoverification ${mode} completed.`, false)
  },
  async createDevice(form) {
    await withAction(async () => {
      await apiFetch("/api/v1/devices", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: readText(form, "code"),
          name: readText(form, "name"),
          manufacturer: readOptionalText(form, "manufacturer"),
          model: readOptionalText(form, "model"),
          serial_no: readOptionalText(form, "serial_no"),
          protocol_code: readOptionalText(form, "protocol_code"),
        }),
      })
      form.reset()
    }, "Device created.")
  },
  async createDeviceMapping(form) {
    const deviceId = readText(form, "device_id")
    await withAction(async () => {
      await apiFetch(`/api/v1/devices/${deviceId}/mappings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          incoming_test_code: readText(form, "incoming_test_code"),
          test_catalog_id: readText(form, "test_catalog_id"),
          default_unit_ucum: readOptionalText(form, "default_unit_ucum"),
        }),
      })
    }, "Device mapping created.")
  },
  async importHl7Oml(form) {
    await withAction(async () => {
      const payload = await apiFetch("/api/v1/integrations/hl7v2/import/oml-o33", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: readText(form, "message"),
          create_missing_patient: true,
        }),
      })
      setPageNotice(`HL7 order imported for requisition ${payload.order.requisition_no}.`, "ok")
    }, "", true)
  },
  async importHl7Oru(form) {
    await withAction(async () => {
      const payload = await apiFetch("/api/v1/integrations/hl7v2/import/oru-r01", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: readText(form, "message"),
          create_missing_patient: true,
        }),
      })
      setPageNotice(`HL7 result imported for order ${payload.order_id}.`, "ok")
    }, "", true)
  },
  async importAstm(form) {
    await withAction(async () => {
      const payload = await apiFetch("/api/v1/integrations/astm/import/results", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_id: readText(form, "device_id"),
          message: readText(form, "message"),
          auto_verify: readBoolean(form, "auto_verify"),
        }),
      })
      setPageNotice(`ASTM payload imported with ${payload.created_observations.length} observations.`, "ok")
    }, "", true)
  },
  async ingestDeviceGateway(form) {
    await withAction(async () => {
      const payload = await apiFetch("/api/v1/integrations/device-gateway/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_id: readText(form, "device_id"),
          accession_no: readOptionalText(form, "accession_no"),
          results: readJson(form, "results_json", []),
          auto_verify: false,
        }),
      })
      setPageNotice(`Gateway ingest created ${payload.created_observations.length} observations.`, "ok")
    }, "", true)
  },
  async createTransportProfile(form) {
    await withAction(async () => {
      await apiFetch("/api/v1/analyzer-transport/profiles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_id: readText(form, "device_id"),
          connection_mode: readText(form, "connection_mode"),
          tcp_host: readOptionalText(form, "tcp_host"),
          tcp_port: readNumber(form, "tcp_port"),
          max_retries: readNumber(form, "max_retries") || 3,
        }),
      })
    }, "Transport profile created.")
  },
  async createTransportSession(form) {
    await withAction(async () => {
      await apiFetch("/api/v1/analyzer-transport/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          device_id: readText(form, "device_id"),
          profile_id: readOptionalText(form, "profile_id"),
        }),
      })
    }, "Transport session created.")
  },
  async queueTransportMessage(form) {
    const sessionId = readText(form, "session_id")
    await withAction(async () => {
      await apiFetch(`/api/v1/analyzer-transport/sessions/${sessionId}/queue-outbound`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message_type: readText(form, "message_type"),
          logical_payload: readText(form, "logical_payload"),
        }),
      })
    }, "Transport message queued.")
  },
}

const clickHandlers = {
  async reloadCurrentRoute() {
    await reloadCurrentRoute(true)
  },
  scrollToAnchor(button) {
    const anchor = button.dataset.anchor
    document.getElementById(anchor)?.scrollIntoView({ behavior: "smooth", block: "start" })
  },
  async acceptSelectedSpecimen() {
    if (!state.selected.specimenId) {
      setPageNotice("Select a specimen first.", "error")
      return
    }
    await withAction(async () => {
      await apiFetch(`/api/v1/specimens/${state.selected.specimenId}/accept`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
    }, "Specimen accepted.")
  },
  async quickReceiveSelectedSpecimen() {
    if (!state.selected.specimenId) {
      setPageNotice("Select a specimen first.", "error")
      return
    }
    await withAction(async () => {
      await apiFetch(`/api/v1/specimens/${state.selected.specimenId}/receive`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ received_at: new Date().toISOString() }),
      })
    }, "Specimen received.")
  },
  async quickAcceptSelectedSpecimen() {
    await clickHandlers.acceptSelectedSpecimen()
  },
  async holdOrderItem(button) {
    const orderItemId = button.dataset.orderItemId
    await withAction(async () => {
      await apiFetch(`/api/v1/order-items/${orderItemId}/hold`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "Held from workbench UI" }),
      })
    }, "Order item placed on hold.")
  },
  async cancelOrderItem(button) {
    const orderItemId = button.dataset.orderItemId
    await withAction(async () => {
      await apiFetch(`/api/v1/order-items/${orderItemId}/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "Cancelled from workbench UI" }),
      })
    }, "Order item cancelled.")
  },
  async claimSelectedTask() {
    const task = getSelectedTask()
    if (!task || !state.currentUser) {
      setPageNotice("Select a task and sign in first.", "error")
      return
    }
    await withAction(async () => {
      await apiFetch(`/api/v1/tasks/${task.id}/claim`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ owner_user_id: state.currentUser.id }),
      })
    }, "Task claimed.")
  },
  async startSelectedTask() {
    const task = getSelectedTask()
    if (!task) {
      setPageNotice("Select a task first.", "error")
      return
    }
    await withAction(async () => {
      await apiFetch(`/api/v1/tasks/${task.id}/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      })
    }, "Task started.")
  },
  async completeSelectedTask() {
    const task = getSelectedTask()
    if (!task) {
      setPageNotice("Select a task first.", "error")
      return
    }
    await withAction(async () => {
      await apiFetch(`/api/v1/tasks/${task.id}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      })
    }, "Task completed.")
  },
  async verifySelectedObservation() {
    const observationId = state.selected.observationId
    if (!observationId) {
      setPageNotice("Select an observation first.", "error")
      return
    }
    await withAction(async () => {
      await apiFetch(`/api/v1/observations/${observationId}/technical-verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      })
    }, "Observation technically verified.")
  },
  async evaluateAutoverificationFromRibbon() {
    if (!state.selected.observationId) {
      setPageNotice("Select an observation first.", "error")
      return
    }
    await withAction(async () => {
      const payload = await apiFetch(
        `/api/v1/autoverification/observations/${state.selected.observationId}/evaluate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        },
      )
      state.cache.autoverificationPreview = {
        mode: "evaluate",
        title: "Evaluation outcome",
        payload,
        summary: [
          { label: "Observation", value: payload.observation_id, mono: true },
          { label: "Overall", value: payload.overall_decision },
          { label: "Matched rules", value: payload.matched_rule_count },
          { label: "Previous final", value: payload.previous_final_observation_id || "None", mono: true },
        ],
      }
      window.location.hash = "#/autoverification"
      state.route = "autoverification"
    }, "Autoverification evaluate completed.")
  },
  async applyAutoverificationFromRibbon() {
    if (!state.selected.observationId) {
      setPageNotice("Select an observation first.", "error")
      return
    }
    await withAction(async () => {
      const payload = await apiFetch(
        `/api/v1/autoverification/observations/${state.selected.observationId}/apply`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        },
      )
      state.cache.autoverificationPreview = {
        mode: "apply",
        title: "Apply outcome",
        payload,
        summary: [
          { label: "Observation", value: payload.observation_id, mono: true },
          { label: "Decision", value: payload.decision },
          { label: "Matched rules", value: payload.matched_rule_count },
          { label: "Created task", value: payload.created_task_id || "None", mono: true },
        ],
      }
      window.location.hash = "#/autoverification"
      state.route = "autoverification"
    }, "Autoverification apply completed.")
  },
  async authorizeSelectedReport() {
    if (!state.selected.reportId || !state.currentUser) {
      setPageNotice("Select a report and sign in first.", "error")
      return
    }
    await withAction(async () => {
      await apiFetch(`/api/v1/reports/${state.selected.reportId}/authorize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          signed_by_user_id: state.currentUser.id,
        }),
      })
    }, "Report authorized.")
  },
  openSelectedReportPdf() {
    const report = state.cache.reportDetail
    const latestVersion = report?.versions?.[report.versions.length - 1]
    if (!latestVersion?.rendered_pdf_uri) {
      setPageNotice("Selected report does not expose a PDF URI yet.", "error")
      return
    }
    window.open(latestVersion.rendered_pdf_uri, "_blank", "noopener")
  },
  async evaluateSelectedQcRun() {
    if (!state.selected.qcRunId) {
      setPageNotice("Select a QC run first.", "error")
      return
    }
    await withAction(async () => {
      await apiFetch(`/api/v1/qc/runs/${state.selected.qcRunId}/evaluate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      })
    }, "QC run evaluated.")
  },
}

async function updateSelection(kind, value) {
  state.selected[kind] = value
  try {
    if (kind === "orderId") {
      await loadOrderDetail(value, true)
    }
    if (kind === "specimenId") {
      await loadSpecimenTrace(value, true)
    }
    if (kind === "observationId") {
      await loadObservationDetail(value, true)
    }
    if (kind === "reportId") {
      await loadReportDetail(value, true)
    }
    if (kind === "deviceId") {
      await loadDeviceMappings(value, true)
    }
    if (kind === "qcRunId") {
      await loadQcRunDetail(value, true)
    }
    if (kind === "transportSessionId") {
      await loadTransportArtifacts(value, true)
    }
  } catch (error) {
    setPageNotice(error.message, "error")
  }
  renderCurrentRoute()
}

async function handleLogin(event) {
  event.preventDefault()
  setMessage(elements.authMessage, "Signing in...")
  try {
    const payload = await apiFetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: elements.usernameInput.value,
        password: elements.passwordInput.value,
      }),
    })
    state.authToken = payload.access_token
    localStorage.setItem(storageKey, state.authToken)
    await loadCurrentUser()
    await loadCurrentRoute(true)
    setMessage(elements.authMessage, "Session established.", "ok")
    renderCurrentRoute()
  } catch (error) {
    setMessage(elements.authMessage, error.message, "error")
  }
}

async function handleBootstrap(event) {
  event.preventDefault()
  setMessage(elements.bootstrapMessage, "Creating bootstrap admin...")
  try {
    const payload = await apiFetch("/api/v1/auth/bootstrap-admin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        display_name: readText(elements.bootstrapForm, "display_name"),
        username: readText(elements.bootstrapForm, "username"),
        password: readText(elements.bootstrapForm, "password"),
      }),
    })
    state.authToken = payload.access_token
    localStorage.setItem(storageKey, state.authToken)
    await loadCurrentUser()
    await loadCurrentRoute(true)
    setMessage(elements.bootstrapMessage, "Bootstrap admin created.", "ok")
    renderCurrentRoute()
  } catch (error) {
    setMessage(elements.bootstrapMessage, error.message, "error")
  }
}

async function handleLogout() {
  state.authToken = ""
  state.currentUser = null
  localStorage.removeItem(storageKey)
  setMessage(elements.authMessage, "Signed out.", "neutral")
  setSessionBadge("neutral", "Guest")
  elements.sessionInfo.textContent =
    "Sign in to unlock live worklists, result review, QC controls, and connectivity pages."
  state.cache.overview = null
  clearPageNotice()
  await loadCurrentRoute(true)
  renderCurrentRoute()
}

function bindStaticEvents() {
  elements.loginForm.addEventListener("submit", handleLogin)
  elements.bootstrapForm.addEventListener("submit", handleBootstrap)
  elements.logoutButton.addEventListener("click", handleLogout)

  elements.globalSearch.addEventListener("input", () => {
    state.searchQuery = elements.globalSearch.value.trim().toLowerCase()
    renderCurrentRoute()
  })

  window.addEventListener("hashchange", async () => {
    state.route = resolveRoute()
    clearPageNotice()
    await loadCurrentRoute(false)
    renderCurrentRoute()
  })

  document.addEventListener("click", async (event) => {
    const routeTarget = event.target.closest("[data-nav-route]")
    if (routeTarget) {
      event.preventDefault()
      await goToRoute(routeTarget.dataset.navRoute, false)
      return
    }

    const selectTarget = event.target.closest("[data-select-kind]")
    if (selectTarget && !event.target.closest("button, a")) {
      await updateSelection(selectTarget.dataset.selectKind, selectTarget.dataset.selectValue)
      return
    }

    const actionTarget = event.target.closest("[data-click-handler]")
    if (actionTarget) {
      const handler = clickHandlers[actionTarget.dataset.clickHandler]
      if (handler) {
        event.preventDefault()
        await handler(actionTarget)
      }
    }
  })

  document.addEventListener("submit", async (event) => {
    const form = event.target.closest("form[data-form-handler]")
    if (!form) {
      return
    }
    event.preventDefault()
    const handler = formHandlers[form.dataset.formHandler]
    if (!handler) {
      return
    }
    const submitter = event.submitter || null
    await handler(form, submitter)
  })
}

async function init() {
  state.route = resolveRoute()
  renderQuickLinks()
  renderSidebar()
  renderPageNotice()
  bindStaticEvents()
  await loadHealth()
  if (state.authToken) {
    try {
      await loadCurrentUser()
    } catch (error) {
      state.authToken = ""
      localStorage.removeItem(storageKey)
      setMessage(elements.authMessage, error.message, "error")
    }
  } else {
    setSessionBadge("neutral", "Guest")
  }
  await loadCurrentRoute(false)
  renderCurrentRoute()
}

init()
