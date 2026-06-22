/**
 * lockscreen.ts — F.R.I.D.A.Y. Biometric Authentication UI
 *
 * Phase 1: Face scan (webcam → backend OpenCV)
 * Phase 2: Voice passphrase (Web Speech API → backend comparison)
 * Phase 3: Unlock animation → main F.R.I.D.A.Y. UI
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface FaceAuthResult {
  matched: boolean;
  confidence: number;
  face_detected?: boolean;
  name?: string;
  error?: string;
}

interface VoiceAuthResult {
  matched: boolean;
  similarity?: number;
  error?: string;
}

interface AuthStatus {
  face_auth_enabled: boolean;
  model_exists: boolean;
  voice_passphrase_set: boolean;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const FACE_SCAN_INTERVAL_MS = 600;   // how often to send frame to backend
const FACE_TIMEOUT_MS       = 12000; // time for face phase before giving up
const VOICE_TIMEOUT_MS      = 9000;  // time for voice phase

// ---------------------------------------------------------------------------
// Main export
// ---------------------------------------------------------------------------

export async function runLockScreen(onUnlocked: () => void): Promise<void> {
  // Check if face auth is enabled on the backend, retrying if the server is still booting
  let status: AuthStatus | null = null;
  const maxRetries = 15; // 15 attempts * 500ms = 7.5 seconds total
  const retryDelay = 500;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const resp = await fetch("/api/auth/status");
      if (resp.ok) {
        status = await resp.json();
        break;
      }
    } catch (err) {
      console.log(`[lockscreen] status fetch attempt ${attempt} failed, retrying...`);
    }
    if (attempt < maxRetries) {
      await sleep(retryDelay);
    }
  }

  if (!status) {
    // Backend still not reachable or auth not configured — skip lockscreen
    console.warn("[lockscreen] backend unreachable after retries, failing open");
    onUnlocked();
    return;
  }

  if (!status.face_auth_enabled || !status.model_exists) {
    onUnlocked();
    return;
  }

  // Show lock screen
  const lockEl = document.getElementById("lock-screen")!;
  lockEl.classList.add("visible");

  try {
    const unlocked = await runFacePhase(lockEl, status);
    if (unlocked) {
      await playUnlockAnimation(lockEl);
      onUnlocked();
      return;
    }

    // Face failed — try voice if passphrase is set
    if (status.voice_passphrase_set) {
      const voiceOk = await runVoicePhase(lockEl);
      if (voiceOk) {
        await playUnlockAnimation(lockEl);
        onUnlocked();
        return;
      }
    }

    // Both failed — show denied
    showDenied(lockEl);
  } catch (err) {
    console.error("[lockscreen] error:", err);
    onUnlocked(); // fail open on unexpected errors
  }
}

// ---------------------------------------------------------------------------
// Phase 1: Face scan
// ---------------------------------------------------------------------------

async function runFacePhase(lockEl: HTMLElement, status: AuthStatus): Promise<boolean> {
  setPhase(lockEl, "face");
  setStatus(lockEl, "SCANNING BIOMETRICS");

  let stream: MediaStream | null = null;
  const videoEl = lockEl.querySelector<HTMLVideoElement>(".lock-video")!;
  const canvas   = document.createElement("canvas");
  canvas.width   = 320;
  canvas.height  = 240;
  const ctx      = canvas.getContext("2d")!;

  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 } });
    videoEl.srcObject = stream;
    await videoEl.play();
  } catch {
    setStatus(lockEl, "CAMERA UNAVAILABLE");
    await sleep(1200);
    stopStream(stream);
    return false;
  }

  return new Promise<boolean>((resolve) => {
    let resolved = false;
    let attempts = 0;

    const timer = setTimeout(() => {
      if (!resolved) {
        resolved = true;
        stopStream(stream);
        resolve(false);
      }
    }, FACE_TIMEOUT_MS);

    const interval = setInterval(async () => {
      if (resolved) { clearInterval(interval); return; }

      ctx.drawImage(videoEl, 0, 0, 320, 240);
      const frameB64 = canvas.toDataURL("image/jpeg", 0.7).split(",")[1];

      try {
        const resp = await fetch("/api/auth/face", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ frame: frameB64 }),
        });
        const result: FaceAuthResult = await resp.json();

        if (result.face_detected === false) {
          setStatus(lockEl, "POSITION FACE IN VIEW");
        } else if (result.matched) {
          clearInterval(interval);
          clearTimeout(timer);
          resolved = true;
          stopStream(stream);
          setStatus(lockEl, `IDENTITY CONFIRMED — ${result.name || "SIR"}`);
          lockEl.querySelector(".lock-ring-wrap")?.classList.add("matched");
          await sleep(900);
          resolve(true);
        } else {
          attempts++;
          const confidence = Math.round(result.confidence ?? 999);
          setStatus(lockEl, `SCANNING... ATTEMPT ${attempts}`);
          lockEl.querySelector(".lock-ring-wrap")?.classList.remove("matched");
        }
      } catch {
        // network hiccup — keep trying
      }
    }, FACE_SCAN_INTERVAL_MS);
  });
}

// ---------------------------------------------------------------------------
// Phase 2: Voice passphrase
// ---------------------------------------------------------------------------

async function runVoicePhase(lockEl: HTMLElement): Promise<boolean> {
  setPhase(lockEl, "voice");
  setStatus(lockEl, "SAY YOUR PASSPHRASE");

  return new Promise<boolean>((resolve) => {
    const SpeechRec =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRec) {
      setStatus(lockEl, "SPEECH API UNAVAILABLE");
      setTimeout(() => resolve(false), 1500);
      return;
    }

    const rec = new SpeechRec();
    rec.lang = "en-US";
    rec.continuous = false;
    rec.interimResults = false;
    rec.maxAlternatives = 3;

    let resolved = false;

    const timeout = setTimeout(() => {
      if (!resolved) {
        resolved = true;
        rec.stop();
        setStatus(lockEl, "NO VOICE DETECTED");
        setTimeout(() => resolve(false), 1000);
      }
    }, VOICE_TIMEOUT_MS);

    rec.onstart = () => {
      lockEl.querySelector(".lock-mic-ring")?.classList.add("active");
      setStatus(lockEl, "LISTENING...");
    };

    rec.onresult = async (event: any) => {
      if (resolved) return;
      const spoken = event.results[0][0].transcript.toLowerCase().trim();
      setStatus(lockEl, `HEARD: "${spoken.toUpperCase()}"`);

      try {
        const resp = await fetch("/api/auth/voice", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: spoken }),
        });
        const result: VoiceAuthResult = await resp.json();

        clearTimeout(timeout);
        resolved = true;
        rec.stop();

        if (result.matched) {
          lockEl.querySelector(".lock-mic-ring")?.classList.add("matched");
          setStatus(lockEl, "PASSPHRASE ACCEPTED");
          await sleep(700);
          resolve(true);
        } else {
          setStatus(lockEl, "PASSPHRASE INCORRECT");
          await sleep(1000);
          resolve(false);
        }
      } catch {
        clearTimeout(timeout);
        resolved = true;
        resolve(false);
      }
    };

    rec.onerror = (event: any) => {
      if (resolved) return;
      clearTimeout(timeout);
      resolved = true;
      const msg = event.error === "no-speech" ? "NO VOICE DETECTED" : "MIC ERROR";
      setStatus(lockEl, msg);
      setTimeout(() => resolve(false), 1000);
    };

    rec.onend = () => {
      lockEl.querySelector(".lock-mic-ring")?.classList.remove("active");
    };

    rec.start();
  });
}

// ---------------------------------------------------------------------------
// Unlock animation
// ---------------------------------------------------------------------------

async function playUnlockAnimation(lockEl: HTMLElement): Promise<void> {
  lockEl.classList.add("unlocking");
  setStatus(lockEl, "SYSTEMS ONLINE");
  await sleep(1200);
  lockEl.classList.add("hidden");
  await sleep(600);
  lockEl.style.display = "none";
}

// ---------------------------------------------------------------------------
// Denied screen
// ---------------------------------------------------------------------------

function showDenied(lockEl: HTMLElement): void {
  setPhase(lockEl, "denied");
  setStatus(lockEl, "ACCESS DENIED");
  lockEl.querySelector(".lock-ring-wrap")?.classList.add("denied");
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function setPhase(lockEl: HTMLElement, phase: "face" | "voice" | "denied"): void {
  lockEl.setAttribute("data-phase", phase);
}

function setStatus(lockEl: HTMLElement, text: string): void {
  const el = lockEl.querySelector<HTMLElement>(".lock-status-text");
  if (el) el.textContent = text;
}

function stopStream(stream: MediaStream | null): void {
  stream?.getTracks().forEach((t) => t.stop());
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}
