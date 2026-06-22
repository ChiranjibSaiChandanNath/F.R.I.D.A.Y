/**
 * F.R.I.D.A.Y. — Main entry point.
 *
 * Wires together the orb visualization, WebSocket communication,
 * speech recognition, and audio playback into a single experience.
 */

import { createOrb, type OrbState } from "./orb";
import { createVoiceInput, createAudioPlayer } from "./voice";
import { createSocket } from "./ws";
import { openSettings, checkFirstTimeSetup } from "./settings";
import { runLockScreen } from "./lockscreen";
import "./style.css";

// ---------------------------------------------------------------------------
// State machine
// ---------------------------------------------------------------------------

type State = "idle" | "listening" | "thinking" | "speaking" | "sleeping";
let currentState: State = "sleeping";
let isMuted = false;

const statusEl = document.getElementById("status-text")!;
const errorEl = document.getElementById("error-text")!;

function showError(msg: string) {
  errorEl.textContent = msg;
  errorEl.style.opacity = "1";
  setTimeout(() => {
    errorEl.style.opacity = "0";
  }, 5000);
}

function updateStatus(state: State) {
  const labels: Record<State, string> = {
    sleeping: "inactive",
    idle: "",
    listening: "listening...",
    thinking: "thinking...",
    speaking: "",
  };
  statusEl.textContent = labels[state];
}

// ---------------------------------------------------------------------------
// Wake chime — a short, soft two-tone generated via Web Audio
// ---------------------------------------------------------------------------

function playWakeChime() {
  try {
    const ctx = new AudioContext();
    const now = ctx.currentTime;
    // Two soft ascending tones
    const freqs = [880, 1320];
    freqs.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = freq;
      gain.gain.setValueAtTime(0, now + idx * 0.12);
      gain.gain.linearRampToValueAtTime(0.18, now + idx * 0.12 + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.12 + 0.35);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + idx * 0.12);
      osc.stop(now + idx * 0.12 + 0.4);
    });
    // Close the AudioContext after the chime finishes
    setTimeout(() => ctx.close(), 1000);
  } catch {
    // AudioContext might not be available yet — silently skip
  }
}

// ---------------------------------------------------------------------------
// Init components
// ---------------------------------------------------------------------------

const canvas = document.getElementById("orb-canvas") as HTMLCanvasElement;
const orb = createOrb(canvas);

// ---------------------------------------------------------------------------
// Boot — run lockscreen first, then init F.R.I.D.A.Y.
// ---------------------------------------------------------------------------

runLockScreen(() => {
  // Auth passed (or disabled) — now connect and start
  initFriday();
});

function initFriday() {

const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
const WS_URL = `${wsProto}//${window.location.host}/ws/voice`;
const socket = createSocket(WS_URL);

const audioPlayer = createAudioPlayer();
orb.setAnalyser(audioPlayer.getAnalyser());

function transition(newState: State) {
  if (newState === currentState) return;
  currentState = newState;
  orb.setState(newState as OrbState);
  updateStatus(newState);

  switch (newState) {
    case "sleeping":
      // Keep mic running so we can hear the wake word, but
      // voice.ts itself filters everything — no need to pause.
      if (!isMuted) voiceInput.resume();
      voiceInput.setSleeping(false);
      break;
    case "idle":
      // After a response, return immediately to listening
      transition("listening");
      return;
    case "listening":
      if (!isMuted) voiceInput.resume();
      voiceInput.setSleeping(false);
      break;
    case "thinking":
      voiceInput.pause();
      break;
    case "speaking":
      voiceInput.pause();
      break;
  }
}

// ---------------------------------------------------------------------------
// Voice input
// ---------------------------------------------------------------------------

const voiceInput = createVoiceInput(
  (text: string) => {
    // Cancel any current F.R.I.D.A.Y. response before sending new input
    audioPlayer.stop();
    // User spoke — send transcript
    socket.send({ type: "transcript", text, isFinal: true });
    transition("thinking");
  },
  (msg: string) => {
    showError(msg);
  },
  // onWake — fired when wake word is detected
  () => {
    if (isMuted) return;
    playWakeChime();
    transition("listening");
  }
);

// ---------------------------------------------------------------------------
// Audio playback finished
// ---------------------------------------------------------------------------

audioPlayer.onFinished(() => {
  // After F.R.I.D.A.Y. finishes speaking, go back to listening
  transition("listening");
});

// ---------------------------------------------------------------------------
// WebSocket messages
// ---------------------------------------------------------------------------

socket.onMessage((msg) => {
  const type = msg.type as string;

  if (type === "audio") {
    const audioData = msg.data as string;
    console.log("[audio] received", audioData ? `${audioData.length} chars` : "EMPTY", "state:", currentState);
    if (audioData) {
      if (currentState !== "speaking") {
        transition("speaking");
      }
      audioPlayer.enqueue(audioData);
    } else {
      // TTS failed — no audio but still need to return to idle
      console.warn("[audio] no data received, returning to idle");
      transition("idle");
    }
    // Log text for debugging
    if (msg.text) console.log("[F.R.I.D.A.Y.]", msg.text);
  } else if (type === "status") {
    const state = msg.state as string;
    if (state === "thinking" && currentState !== "thinking") {
      transition("thinking");
    } else if (state === "working") {
      // Task spawned — show thinking with a different label
      transition("thinking");
      statusEl.textContent = "working...";
    } else if (state === "idle") {
      transition("idle");
    }
  } else if (type === "text") {
    // Text fallback when TTS fails
    console.log("[F.R.I.D.A.Y.]", msg.text);
  } else if (type === "task_spawned") {
    console.log("[task]", "spawned:", msg.task_id, msg.prompt);
  } else if (type === "task_complete") {
    console.log("[task]", "complete:", msg.task_id, msg.status, msg.summary);
  }
});

// ---------------------------------------------------------------------------
// Kick off
// ---------------------------------------------------------------------------

// Start in listening state — ready for commands
setTimeout(() => {
  voiceInput.start();
  transition("listening");
}, 1000);

// Resume AudioContext on ANY user interaction (browser autoplay policy)
function ensureAudioContext() {
  const ctx = audioPlayer.getAnalyser().context as AudioContext;
  if (ctx.state === "suspended") {
    ctx.resume().then(() => console.log("[audio] context resumed"));
  }
}
document.addEventListener("click", ensureAudioContext);
document.addEventListener("touchstart", ensureAudioContext);
document.addEventListener("keydown", ensureAudioContext, { once: true });

// Try to resume audio context on load
ensureAudioContext();

// ---------------------------------------------------------------------------
// UI Controls
// ---------------------------------------------------------------------------

const btnMute = document.getElementById("btn-mute")!;
const btnMenu = document.getElementById("btn-menu")!;
const menuDropdown = document.getElementById("menu-dropdown")!;
const btnRestart = document.getElementById("btn-restart")!;
const btnFixSelf = document.getElementById("btn-fix-self")!;

btnMute.addEventListener("click", (e) => {
  e.stopPropagation();
  isMuted = !isMuted;
  btnMute.classList.toggle("muted", isMuted);
  if (isMuted) {
    voiceInput.pause();
    transition("sleeping");
    statusEl.textContent = "muted";
  } else {
    voiceInput.resume();
    transition("listening");
  }
});

btnMenu.addEventListener("click", (e) => {
  e.stopPropagation();
  menuDropdown.style.display = menuDropdown.style.display === "none" ? "block" : "none";
});

document.addEventListener("click", () => {
  menuDropdown.style.display = "none";
});

btnRestart.addEventListener("click", async (e) => {
  e.stopPropagation();
  menuDropdown.style.display = "none";
  statusEl.textContent = "restarting...";
  try {
    await fetch("/api/restart", { method: "POST" });
    // Wait a few seconds then reload
    setTimeout(() => window.location.reload(), 4000);
  } catch {
    statusEl.textContent = "restart failed";
  }
});

btnFixSelf.addEventListener("click", (e) => {
  e.stopPropagation();
  menuDropdown.style.display = "none";
  // Activate work mode on the WebSocket session (F.R.I.D.A.Y. becomes Claude Code's voice)
  socket.send({ type: "fix_self" });
  statusEl.textContent = "entering work mode...";
});

// Settings button
const btnSettings = document.getElementById("btn-settings")!;
btnSettings.addEventListener("click", (e) => {
  e.stopPropagation();
  menuDropdown.style.display = "none";
  openSettings();
});

// First-time setup detection — check after a short delay for server readiness
setTimeout(() => {
  checkFirstTimeSetup();
}, 2000);

  // ── Dashboard Animations ──
  
  // 1. Connection Graph
  const connCanvas = document.getElementById("canvas-connection-chart") as HTMLCanvasElement;
  if (connCanvas) {
    const ctx = connCanvas.getContext("2d")!;
    let points = [15, 12, 18, 14, 22, 19, 15, 17, 25, 20];
    function drawConnChart() {
      requestAnimationFrame(drawConnChart);
      if (Date.now() % 5 !== 0) return;
      points.shift();
      const last = points[points.length - 1];
      const next = Math.max(5, Math.min(30, last + (Math.random() - 0.5) * 6));
      points.push(next);
      
      ctx.clearRect(0, 0, connCanvas.width, connCanvas.height);
      ctx.strokeStyle = "rgba(184, 90, 240, 0.7)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      const step = connCanvas.width / (points.length - 1);
      for (let i = 0; i < points.length; i++) {
        const x = i * step;
        const y = connCanvas.height - points[i];
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
      
      const grad = ctx.createLinearGradient(0, 0, 0, connCanvas.height);
      grad.addColorStop(0, "rgba(184, 90, 240, 0.2)");
      grad.addColorStop(1, "rgba(184, 90, 240, 0)");
      ctx.fillStyle = grad;
      ctx.lineTo(connCanvas.width, connCanvas.height);
      ctx.lineTo(0, connCanvas.height);
      ctx.closePath();
      ctx.fill();
    }
    drawConnChart();
  }

  // 2. Temperature Bars
  const tempBars = document.querySelectorAll("#dash-temp-chart .bar");
  if (tempBars.length > 0) {
    function animateTemp() {
      requestAnimationFrame(animateTemp);
      if (Date.now() % 8 !== 0) return;
      tempBars.forEach((bar, idx) => {
        const el = bar as HTMLElement;
        const base = Math.sin(idx * 0.4 + Date.now() * 0.002) * 35 + 45;
        const noise = (Math.random() - 0.5) * 10;
        el.style.height = `${Math.max(5, Math.min(95, base + noise))}%`;
      });
    }
    animateTemp();
  }

  // 3. Audio Waveform Visualizer (overlaid twin-waves Siri style)
  const waveformCanvas = document.getElementById("canvas-waveform") as HTMLCanvasElement;
  if (waveformCanvas) {
    const ctx = waveformCanvas.getContext("2d")!;
    const analyser = audioPlayer.getAnalyser();
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    function drawWaveform() {
      requestAnimationFrame(drawWaveform);
      analyser.getByteTimeDomainData(dataArray);
      
      if (waveformCanvas.width !== waveformCanvas.parentElement!.clientWidth) {
        waveformCanvas.width = waveformCanvas.parentElement!.clientWidth;
        waveformCanvas.height = 60;
      }
      
      const width = waveformCanvas.width;
      const height = waveformCanvas.height;
      ctx.clearRect(0, 0, width, height);
      ctx.lineWidth = 1.5;
      
      // Purple Wave
      ctx.strokeStyle = "rgba(184, 90, 240, 0.75)";
      ctx.beginPath();
      let sliceWidth = width / bufferLength;
      let x = 0;
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * height) / 2;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        x += sliceWidth;
      }
      ctx.stroke();

      // Pink Wave (Offset)
      ctx.strokeStyle = "rgba(232, 76, 156, 0.4)";
      ctx.beginPath();
      x = 0;
      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * height) / 2 + Math.sin(i * 0.06 + Date.now() * 0.008) * 2;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        x += sliceWidth;
      }
      ctx.stroke();
    }
    drawWaveform();
  }

  // 4. Wire dashboard specific buttons
  document.getElementById("btn-settings-dash")?.addEventListener("click", (e) => {
    e.stopPropagation();
    openSettings();
  });
  document.getElementById("btn-menu-dash")?.addEventListener("click", (e) => {
    e.stopPropagation();
    menuDropdown.style.display = menuDropdown.style.display === "none" ? "block" : "none";
  });

} // end initFriday
