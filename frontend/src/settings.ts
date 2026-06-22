/**
 * F.R.I.D.A.Y. — Settings Panel
 *
 * Overlay panel for API keys, connection status, preferences, and system info.
 * Slides in from the right with glass-morphism styling.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface StatusResponse {
  claude_code_installed: boolean;
  calendar_accessible: boolean;
  mail_accessible: boolean;
  notes_accessible: boolean;
  memory_count: number;
  task_count: number;
  server_port: number;
  uptime_seconds: number;
  env_keys_set: {
    groq: boolean;
    tts_edge: boolean;
    tts_kokoro: boolean;
    user_name: string;
    openweathermap?: boolean;
  };
}

interface PreferencesResponse {
  user_name: string;
  honorific: string;
  calendar_accounts: string;
}

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let panelEl: HTMLElement | null = null;
let isOpen = false;
let isFirstTimeSetup = false;
let setupStep = 0; // 0=groq, 1=name, 2=done

// ---------------------------------------------------------------------------
// API helpers
// ---------------------------------------------------------------------------

async function apiGet<T>(url: string): Promise<T> {
  const res = await fetch(url);
  return res.json();
}

async function apiPost<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

// ---------------------------------------------------------------------------
// Panel HTML
// ---------------------------------------------------------------------------

function buildPanelHTML(): string {
  return `
    <div class="settings-backdrop" id="settings-backdrop"></div>
    <div class="settings-panel" id="settings-panel-inner">
      <div class="settings-header">
        <h2>Settings</h2>
        <button class="settings-close" id="settings-close">&times;</button>
      </div>

      <div class="settings-welcome" id="settings-welcome" style="display:none">
        <p>Welcome to F.R.I.D.A.Y. Let's get you set up.</p>
      </div>

      <div class="settings-body">

        <!-- API Keys -->
        <section class="settings-section" id="section-api-keys">
          <h3>API Keys</h3>

          <div class="settings-field">
            <label>Groq API Key</label>
            <div class="settings-input-row">
              <input type="password" id="input-groq-key" placeholder="gsk-..." />
              <button class="settings-btn" id="btn-test-groq">Test</button>
              <span class="status-dot" id="status-groq"></span>
            </div>
          </div>

          <div class="settings-field">
            <label>OpenWeatherMap API Key</label>
            <div class="settings-input-row">
              <input type="password" id="input-openweathermap-key" placeholder="9cdc..." />
              <button class="settings-btn" id="btn-test-openweathermap">Test</button>
              <span class="status-dot" id="status-openweathermap"></span>
            </div>
          </div>

          <!-- TTS Status (Edge + Kokoro) -->
          <div class="settings-field">
            <label>Voice Synthesis (Edge TTS + Kokoro)</label>
            <div class="settings-input-row" style="align-items: center; gap: 8px; display: flex;">
              <span class="status-dot" id="status-tts"></span>
              <span id="label-tts-status" style="font-size: 0.95em; color: #888; margin-left: 8px;">Checking voice engine...</span>
              <button class="settings-btn" id="btn-test-tts" style="margin-left: auto;">Test</button>
            </div>
          </div>

          <div class="settings-actions">
            <button class="settings-btn primary" id="btn-save-keys">Save Keys</button>
          </div>
        </section>

        <!-- Connection Status -->
        <section class="settings-section" id="section-status">
          <h3>Connection Status</h3>
          <div class="status-grid">
            <div class="status-row"><span class="status-dot" id="status-claude-cli"></span><span>Claude Code CLI</span></div>
            <div class="status-row"><span class="status-dot" id="status-calendar"></span><span>Google Calendar</span></div>
            <div class="status-row"><span class="status-dot" id="status-mail"></span><span>Gmail</span></div>
            <div class="status-row"><span class="status-dot" id="status-notes"></span><span>Local Notes</span></div>
            <div class="status-row"><span class="status-dot" id="status-server"></span><span>Server</span><span class="status-detail" id="status-server-detail"></span></div>
          </div>
        </section>

        <!-- User Preferences -->
        <section class="settings-section" id="section-preferences">
          <h3>User Preferences</h3>

          <div class="settings-field">
            <label>Your Name</label>
            <input type="text" id="input-user-name" placeholder="Your name" />
          </div>

          <div class="settings-field">
            <label>Honorific</label>
            <select id="input-honorific">
              <option value="sir">Sir</option>
              <option value="ma'am">Ma'am</option>
              <option value="none">None</option>
            </select>
          </div>

          <div class="settings-field">
            <label>Calendar Accounts</label>
            <textarea id="input-calendar-accounts" rows="2" placeholder="auto (or comma-separated emails)"></textarea>
          </div>

          <div class="settings-actions">
            <button class="settings-btn primary" id="btn-save-prefs">Save Preferences</button>
          </div>
        </section>

        <!-- System Info -->
        <section class="settings-section" id="section-sysinfo">
          <h3>System Info</h3>
          <div class="sysinfo-grid">
            <div class="sysinfo-row"><span class="sysinfo-label">Memory entries</span><span id="sysinfo-memory">--</span></div>
            <div class="sysinfo-row"><span class="sysinfo-label">Tasks</span><span id="sysinfo-tasks">--</span></div>
            <div class="sysinfo-row"><span class="sysinfo-label">Server port</span><span id="sysinfo-port">--</span></div>
            <div class="sysinfo-row"><span class="sysinfo-label">Uptime</span><span id="sysinfo-uptime">--</span></div>
          </div>
        </section>

        <!-- Setup Navigation (first-time only) -->
        <div class="setup-nav" id="setup-nav" style="display:none">
          <button class="settings-btn primary" id="btn-setup-next">Next</button>
        </div>

      </div>
    </div>
  `;
}

// ---------------------------------------------------------------------------
// Panel lifecycle
// ---------------------------------------------------------------------------

function createPanel(): HTMLElement {
  const container = document.createElement("div");
  container.id = "settings-container";
  container.innerHTML = buildPanelHTML();
  document.body.appendChild(container);
  return container;
}

function setDotStatus(id: string, status: "green" | "red" | "yellow" | "off") {
  const dot = document.getElementById(id);
  if (!dot) return;
  dot.className = "status-dot";
  if (status !== "off") dot.classList.add(`status-${status}`);
}

function formatUptime(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
}

async function loadStatus() {
  try {
    const status = await apiGet<StatusResponse>("/api/settings/status");

    setDotStatus("status-claude-cli", status.claude_code_installed ? "green" : "red");
    setDotStatus("status-calendar", status.calendar_accessible ? "green" : "red");
    setDotStatus("status-mail", status.mail_accessible ? "green" : "red");
    setDotStatus("status-notes", status.notes_accessible ? "green" : "red");
    setDotStatus("status-server", "green");

    const serverDetail = document.getElementById("status-server-detail");
    if (serverDetail) serverDetail.textContent = `port ${status.server_port} | up ${formatUptime(status.uptime_seconds)}`;

    // TTS status dots
    setDotStatus("status-groq", status.env_keys_set.groq ? "green" : "red");
    setDotStatus("status-openweathermap", status.env_keys_set.openweathermap ? "green" : "red");
    const edgeReady = status.env_keys_set.tts_edge;
    const kokoroReady = status.env_keys_set.tts_kokoro;
    setDotStatus("status-tts", edgeReady ? "green" : kokoroReady ? "yellow" : "red");
    const ttsLabel = document.getElementById("label-tts-status");
    if (ttsLabel) {
      if (edgeReady) { ttsLabel.textContent = "Edge TTS online"; ttsLabel.style.color = "#00ffcc"; }
      else if (kokoroReady) { ttsLabel.textContent = "Kokoro offline active (no internet)"; ttsLabel.style.color = "#f59e0b"; }
      else { ttsLabel.textContent = "No voice engine available"; ttsLabel.style.color = "#ff3366"; }
    }

    // System info
    const memEl = document.getElementById("sysinfo-memory");
    if (memEl) memEl.textContent = String(status.memory_count);
    const taskEl = document.getElementById("sysinfo-tasks");
    if (taskEl) taskEl.textContent = String(status.task_count);
    const portEl = document.getElementById("sysinfo-port");
    if (portEl) portEl.textContent = String(status.server_port);
    const upEl = document.getElementById("sysinfo-uptime");
    if (upEl) upEl.textContent = formatUptime(status.uptime_seconds);

    return status;
  } catch (e) {
    console.error("[settings] failed to load status:", e);
    setDotStatus("status-server", "red");
    return null;
  }
}

async function loadPreferences() {
  try {
    const prefs = await apiGet<PreferencesResponse>("/api/settings/preferences");
    const nameEl = document.getElementById("input-user-name") as HTMLInputElement;
    const honEl = document.getElementById("input-honorific") as HTMLSelectElement;
    const calEl = document.getElementById("input-calendar-accounts") as HTMLTextAreaElement;
    if (nameEl) nameEl.value = prefs.user_name || "";
    if (honEl) honEl.value = prefs.honorific || "sir";
    if (calEl) calEl.value = prefs.calendar_accounts || "auto";
  } catch (e) {
    console.error("[settings] failed to load preferences:", e);
  }
}

function wireEvents() {
  // Close
  document.getElementById("settings-close")?.addEventListener("click", closeSettings);
  document.getElementById("settings-backdrop")?.addEventListener("click", closeSettings);

  // Save keys
  document.getElementById("btn-save-keys")?.addEventListener("click", async () => {
    const groqKey = (document.getElementById("input-groq-key") as HTMLInputElement).value.trim();
    const openweathermapKey = (document.getElementById("input-openweathermap-key") as HTMLInputElement).value.trim();

    if (groqKey) {
      await apiPost("/api/settings/keys", { key_name: "GROQ_API_KEY", key_value: groqKey });
    }
    if (openweathermapKey) {
      await apiPost("/api/settings/keys", { key_name: "OPENWEATHERMAP_API_KEY", key_value: openweathermapKey });
    }
    await loadStatus();
  });

  // Test Groq
  document.getElementById("btn-test-groq")?.addEventListener("click", async () => {
    setDotStatus("status-groq", "yellow");
    const key = (document.getElementById("input-groq-key") as HTMLInputElement).value.trim();
    try {
      const result = await apiPost<{ valid: boolean; error?: string }>("/api/settings/test-groq", { key_value: key || undefined });
      setDotStatus("status-groq", result.valid ? "green" : "red");
    } catch {
      setDotStatus("status-groq", "red");
    }
  });

  // Test TTS (Edge TTS + Kokoro)
  document.getElementById("btn-test-tts")?.addEventListener("click", async () => {
    setDotStatus("status-tts", "yellow");
    try {
      const result = await apiPost<{ valid: boolean; engine?: string; error?: string }>("/api/settings/test-tts", {});
      setDotStatus("status-tts", result.valid ? "green" : "red");
      const ttsLabel = document.getElementById("label-tts-status");
      if (ttsLabel && result.valid) {
        ttsLabel.textContent = result.engine === "edge_tts" ? "Edge TTS online" : "Kokoro offline active";
        ttsLabel.style.color = result.engine === "edge_tts" ? "#00ffcc" : "#f59e0b";
      }
    } catch {
      setDotStatus("status-tts", "red");
    }
  });

  // Test OpenWeatherMap
  document.getElementById("btn-test-openweathermap")?.addEventListener("click", async () => {
    setDotStatus("status-openweathermap", "yellow");
    const key = (document.getElementById("input-openweathermap-key") as HTMLInputElement).value.trim();
    try {
      const result = await apiPost<{ valid: boolean; error?: string }>("/api/settings/test-openweathermap", { key_value: key || undefined });
      setDotStatus("status-openweathermap", result.valid ? "green" : "red");
    } catch {
      setDotStatus("status-openweathermap", "red");
    }
  });

  // Save preferences
  document.getElementById("btn-save-prefs")?.addEventListener("click", async () => {
    const user_name = (document.getElementById("input-user-name") as HTMLInputElement).value.trim();
    const honorific = (document.getElementById("input-honorific") as HTMLSelectElement).value;
    const calendar_accounts = (document.getElementById("input-calendar-accounts") as HTMLTextAreaElement).value.trim();
    await apiPost("/api/settings/preferences", { user_name, honorific, calendar_accounts });
    await loadStatus();
  });

  // Setup next button
  document.getElementById("btn-setup-next")?.addEventListener("click", advanceSetup);
}

// ---------------------------------------------------------------------------
// First-time setup wizard
// ---------------------------------------------------------------------------

function enterSetupMode() {
  isFirstTimeSetup = true;
  setupStep = 0;

  const welcome = document.getElementById("settings-welcome");
  if (welcome) welcome.style.display = "block";

  const nav = document.getElementById("setup-nav");
  if (nav) nav.style.display = "flex";

  // Hide sections except API keys
  showSetupStep(0);
}

function showSetupStep(step: number) {
  const sections = ["section-api-keys", "section-status", "section-preferences", "section-sysinfo"];
  sections.forEach((id, i) => {
    const el = document.getElementById(id);
    if (!el) return;
    if (step === 0 && i === 0) el.style.display = "";
    else if (step === 1 && i === 0) el.style.display = "";
    else if (step === 2 && i === 2) el.style.display = "";
    else if (step === 3) el.style.display = "";
    else el.style.display = "none";
  });

  const nextBtn = document.getElementById("btn-setup-next");
  if (nextBtn) {
    if (step === 0) nextBtn.textContent = "Next: Test Keys";
    else if (step === 1) nextBtn.textContent = "Next: Set Your Name";
    else if (step === 2) nextBtn.textContent = "Finish Setup";
    else nextBtn.style.display = "none";
  }
}

async function advanceSetup() {
  setupStep++;
  if (setupStep >= 3) {
    // Done — save everything and close
    isFirstTimeSetup = false;
    const welcome = document.getElementById("settings-welcome");
    if (welcome) welcome.style.display = "none";
    const nav = document.getElementById("setup-nav");
    if (nav) nav.style.display = "none";

    // Show all sections
    ["section-api-keys", "section-status", "section-preferences", "section-sysinfo"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.style.display = "";
    });

    closeSettings();
    return;
  }
  showSetupStep(setupStep);
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export async function openSettings() {
  if (isOpen) return;
  isOpen = true;

  if (!panelEl) {
    panelEl = createPanel();
    wireEvents();
  }

  panelEl.style.display = "block";

  // Trigger animation
  requestAnimationFrame(() => {
    panelEl!.classList.add("open");
  });

  // Load data
  const status = await loadStatus();
  await loadPreferences();

  // Check for first-time setup
  if (status && !status.env_keys_set.groq) {
    enterSetupMode();
  }
}

export function closeSettings() {
  if (!panelEl || !isOpen) return;
  isOpen = false;
  panelEl.classList.remove("open");
  setTimeout(() => {
    if (panelEl) panelEl.style.display = "none";
  }, 300);
}

export function isSettingsOpen(): boolean {
  return isOpen;
}

/**
 * Check if first-time setup is needed and auto-open.
 */
export async function checkFirstTimeSetup(): Promise<boolean> {
  try {
    const status = await apiGet<StatusResponse>("/api/settings/status");
    if (!status.env_keys_set.groq) {
      openSettings();
      return true;
    }
  } catch {
    // Server not ready yet, skip
  }
  return false;
}
