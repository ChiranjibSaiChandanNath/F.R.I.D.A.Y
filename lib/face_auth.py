"""
face_auth.py — F.R.I.D.A.Y. Face Authentication

Two-layer identity verification at F.R.I.D.A.Y. startup:
  Layer 1 — Face scan  (OpenCV LBPH, webcam required)
  Layer 2 — Voice passphrase fallback (SpeechRecognition + Google STT)

If face passes  → full access
If face fails   → voice passphrase prompt
If voice passes → full access
If voice fails  → restricted mode (sensitive commands blocked)

Usage:
    python face_auth.py --train         # One-time face training
    python face_auth.py --verify        # Test face + voice check
    python face_auth.py --reset         # Delete saved face model

Enable via .env:
    FACE_AUTH=true
    VOICE_PASSPHRASE=your secret phrase here
"""

import os
import sys
import time
import logging
import pickle
from pathlib import Path

log = logging.getLogger("friday.face_auth")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_BASE_DIR  = Path(__file__).parent.parent
_DATA_DIR  = _BASE_DIR / "data" / "face_auth"
_MODEL_PATH = _DATA_DIR / "face_model.yml"
_LABELS_PATH = _DATA_DIR / "face_labels.pkl"
_CASCADE_PATH = None  # auto-detected from OpenCV install

_FACE_AUTH_ENABLED = os.getenv("FACE_AUTH", "false").lower() in ("1", "true", "yes")

# Voice passphrase fallback (used when face auth fails)
_VOICE_PASSPHRASE = os.getenv("VOICE_PASSPHRASE", "").strip()

# Recognition thresholds
_CONFIDENCE_THRESHOLD = 80   # lower = stricter. LBPH: <80 is good match
_SAMPLES_NEEDED       = 60   # frames captured during training
_SCAN_TIMEOUT_SECS    = 10   # how long to wait for a face during verify
_MAX_RETRIES          = 2    # how many verify attempts before giving up
_VOICE_TIMEOUT_SECS   = 8    # seconds to wait for spoken passphrase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_cascade():
    """Return the Haar cascade classifier path, installing OpenCV if needed."""
    global _CASCADE_PATH
    if _CASCADE_PATH:
        return _CASCADE_PATH

    try:
        import cv2
    except ImportError:
        log.error("opencv-python not installed. Run: pip install opencv-python")
        return None

    path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"  # type: ignore[attr-defined]
    if not Path(path).exists():
        log.error("Haar cascade XML not found at: %s", path)
        return None

    _CASCADE_PATH = path
    return path


def _ensure_data_dir():
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def _model_exists() -> bool:
    return _MODEL_PATH.exists() and _LABELS_PATH.exists()


def _draw_ui(frame, text: str, color=(0, 255, 120)):
    """Draw a semi-transparent overlay + status text on frame."""
    import cv2
    import numpy as np

    h, w = frame.shape[:2]
    overlay = frame.copy()

    # Bottom bar
    cv2.rectangle(overlay, (0, h - 60), (w, h), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    # Status text
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_size = cv2.getTextSize(text, font, 0.65, 2)[0]
    text_x = (w - text_size[0]) // 2
    cv2.putText(frame, text, (text_x, h - 18), font, 0.65, color, 2, cv2.LINE_AA)

    # Top bar — F.R.I.D.A.Y. label
    cv2.rectangle(frame, (0, 0), (w, 36), (10, 10, 10), -1)
    cv2.putText(frame, "F.R.I.D.A.Y.  FACE AUTHENTICATION", (10, 24),
                font, 0.55, (100, 200, 255), 1, cv2.LINE_AA)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_face(user_name: str = "owner") -> bool:
    """
    Open the webcam, capture _SAMPLES_NEEDED frames of the user's face,
    train an LBPH recognizer, and save the model.

    Returns True on success, False on failure.
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("[FAIL] opencv-python not installed. Run:\n    pip install opencv-python")
        return False

    cascade_path = _get_cascade()
    if not cascade_path:
        return False

    _ensure_data_dir()
    detector = cv2.CascadeClassifier(cascade_path)
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("  [FAIL] Could not open webcam. Make sure it is connected and not in use.")
        return False

    print()
    print("  +---------------------------------------------+")
    print("  |   F.R.I.D.A.Y. Face Training Mode           |")
    print("  |                                             |")
    print("  |   * Look directly at the camera            |")
    print("  |   * Keep your face well-lit                |")
    print(f"  |   * Will capture {_SAMPLES_NEEDED} frames automatically     |")
    print("  |   * Press  Q  to cancel at any time        |")
    print("  +---------------------------------------------+")
    print()

    faces_data   = []
    sample_count = 0
    label_id     = 0
    labels       = {label_id: user_name}

    cv2.namedWindow("F.R.I.D.A.Y. — Face Training", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("F.R.I.D.A.Y. — Face Training", 640, 480)

    while sample_count < _SAMPLES_NEEDED:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detected = detector.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))

        status = f"Scanning... {sample_count}/{_SAMPLES_NEEDED}"
        _draw_ui(frame, status)

        for (x, y, w, h) in detected:
            # Draw face box
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 120), 2)

            # Sample every other frame to get variety
            if sample_count < _SAMPLES_NEEDED:
                face_roi = gray[y:y + h, x:x + w]
                face_roi = cv2.resize(face_roi, (200, 200))
                faces_data.append(face_roi)
                sample_count += 1

                # Progress indicator inside box
                prog = int((sample_count / _SAMPLES_NEEDED) * w)
                cv2.rectangle(frame, (x, y + h + 4), (x + prog, y + h + 12), (0, 255, 120), -1)

        cv2.imshow("F.R.I.D.A.Y. — Face Training", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            cap.release()
            cv2.destroyAllWindows()
            print("  Training cancelled.")
            return False

    cap.release()
    cv2.destroyAllWindows()

    if len(faces_data) < _SAMPLES_NEEDED // 2:
        print(f"  [FAIL] Not enough face samples captured ({len(faces_data)}). Try again with better lighting.")
        return False

    print(f"  [OK] Captured {len(faces_data)} samples. Training model...")

    # Train LBPH recognizer
    recognizer = cv2.face.LBPHFaceRecognizer_create()  # type: ignore[attr-defined]
    ids        = [label_id] * len(faces_data)
    recognizer.train(faces_data, np.array(ids))

    # Save model + labels
    recognizer.save(str(_MODEL_PATH))
    with open(_LABELS_PATH, "wb") as f:
        pickle.dump(labels, f)

    print(f"  [OK] Face model saved to: {_MODEL_PATH}")
    print()
    print("  F.R.I.D.A.Y. will now recognize you on startup.")
    print("  Run  python server.py  to launch normally.")
    print()
    return True


# ---------------------------------------------------------------------------
# Voice Passphrase Fallback
# ---------------------------------------------------------------------------

def voice_passphrase_check() -> bool | None:
    """
    Ask the user to speak the secret passphrase.
    Returns:
        True   -> passphrase matched
        False  -> wrong passphrase or no speech
        None   -> SpeechRecognition not installed or VOICE_PASSPHRASE not set
    """
    if not _VOICE_PASSPHRASE:
        log.info("No VOICE_PASSPHRASE set in .env — voice fallback unavailable.")
        return None

    try:
        import speech_recognition as sr
    except ImportError:
        log.warning("SpeechRecognition not installed. Run: pip install SpeechRecognition pyaudio")
        return None

    recognizer = sr.Recognizer()

    print()
    print("  [MIC] Face not recognized. Voice passphrase required.")
    print("  [MIC] Say your secret passphrase now...")
    print()

    try:
        with sr.Microphone() as source:
            # Calibrate for ambient noise quickly
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            recognizer.energy_threshold = max(recognizer.energy_threshold, 300)
            print("  [MIC] Listening... speak clearly.")
            audio = recognizer.listen(source, timeout=_VOICE_TIMEOUT_SECS, phrase_time_limit=6)

        spoken = recognizer.recognize_google(audio).lower().strip()
        print(f"  [MIC] Heard: \"{spoken}\"")

        expected = _VOICE_PASSPHRASE.lower().strip()

        # Exact match first
        if spoken == expected:
            print("  [OK] Voice passphrase accepted. Welcome back, sir.")
            return True

        # Fuzzy match — allow 1 word difference for speech recognition errors
        spoken_words   = set(spoken.split())
        expected_words = set(expected.split())
        common         = spoken_words & expected_words
        similarity     = len(common) / max(len(expected_words), 1)

        if similarity >= 0.75:  # 75%+ words match (allows 1 mishear in 4-word phrase)
            print(f"  [OK] Voice passphrase accepted (fuzzy match: {int(similarity*100)}%).")
            return True

        print("  [FAIL] Passphrase did not match.")
        return False

    except sr.WaitTimeoutError:
        print("  [FAIL] No voice detected. Timed out.")
        return False
    except sr.UnknownValueError:
        print("  [FAIL] Could not understand audio. Try speaking more clearly.")
        return False
    except sr.RequestError as e:
        log.warning("Google STT unavailable (no internet?): %s", e)
        print("  [SKIP] Voice auth unavailable (no internet connection).")
        return None
    except Exception as e:
        log.error("Voice auth error: %s", e)
        return None


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_face(timeout: int = _SCAN_TIMEOUT_SECS, retries: int = _MAX_RETRIES) -> bool | None:
    """
    Verify the user's face against the saved model.

    Returns:
        True   → face matched (access granted)
        False  → face did NOT match after all retries (restricted mode)
        None   → face auth is disabled, no model exists, or webcam unavailable
    """
    if not _FACE_AUTH_ENABLED:
        return None

    if not _model_exists():
        log.warning("Face auth enabled but no model found. Run: python face_auth.py --train")
        return None

    try:
        import cv2
    except ImportError:
        log.error("opencv-python not installed — face auth skipped.")
        return None

    cascade_path = _get_cascade()
    if not cascade_path:
        return None

    detector   = cv2.CascadeClassifier(cascade_path)
    recognizer = cv2.face.LBPHFaceRecognizer_create()  # type: ignore[attr-defined]
    recognizer.read(str(_MODEL_PATH))

    with open(_LABELS_PATH, "rb") as f:
        labels = pickle.load(f)

    for attempt in range(1, retries + 1):
        result = _run_verify_attempt(detector, recognizer, labels, timeout, attempt, retries)
        if result is True:
            return True
        if result is None:
            return None  # webcam issue

    # ---------------------------------------------------------------
    # Face failed — try voice passphrase fallback
    # ---------------------------------------------------------------
    log.warning("Face verification failed after %d attempts. Trying voice fallback.", retries)
    voice_result = voice_passphrase_check()
    if voice_result is True:
        return True   # voice passed — grant full access
    if voice_result is None:
        # Voice unavailable (not configured / no internet) — go restricted
        log.warning("Voice fallback unavailable. Entering restricted mode.")
        return False

    # Both face and voice failed
    log.warning("Both face and voice auth failed. Entering restricted mode.")
    return False


def _run_verify_attempt(detector, recognizer, labels: dict, timeout: int,
                         attempt: int, total_attempts: int):
    """Single verification pass. Returns True/False/None."""
    import cv2

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        log.warning("Webcam unavailable — skipping face auth.")
        return None

    log.info("Face verification attempt %d/%d (timeout: %ds)", attempt, total_attempts, timeout)

    start_time   = time.time()
    match_frames = 0
    no_face_warn = False

    cv2.namedWindow("F.R.I.D.A.Y. — Identity Verification", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("F.R.I.D.A.Y. — Identity Verification", 640, 480)

    result = False

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            log.warning("Face verification timed out.")
            break

        ret, frame = cap.read()
        if not ret:
            break

        gray     = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detected = detector.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))

        remaining = int(timeout - elapsed)

        if len(detected) == 0:
            status = f"No face detected — {remaining}s remaining"
            _draw_ui(frame, status, color=(180, 180, 180))
        else:
            for (x, y, w, h) in detected:
                face_roi    = gray[y:y + h, x:x + w]
                face_roi    = cv2.resize(face_roi, (200, 200))
                label_id, confidence = recognizer.predict(face_roi)

                is_match = confidence < _CONFIDENCE_THRESHOLD
                color    = (0, 255, 120) if is_match else (0, 80, 255)
                name     = labels.get(label_id, "Unknown") if is_match else "Unknown"

                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, f"{name}  ({confidence:.0f})", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

                if is_match:
                    match_frames += 1
                    status = f"Identity confirmed — Welcome, {name}!"
                    _draw_ui(frame, status, color=(0, 255, 120))
                    # Require 5 consecutive match frames for reliability
                    if match_frames >= 5:
                        cv2.imshow("F.R.I.D.A.Y. — Identity Verification", frame)
                        cv2.waitKey(800)
                        result = True
                        break
                else:
                    match_frames = 0
                    status = f"Face not recognized — {remaining}s remaining"
                    _draw_ui(frame, status, color=(0, 80, 255))

            if result:
                break

        cv2.imshow("F.R.I.D.A.Y. — Identity Verification", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == 27:
            log.info("Face verification cancelled by user.")
            result = None
            break

    cap.release()
    cv2.destroyAllWindows()
    return result


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def reset_face_model():
    """Delete the saved face model so training can be redone."""
    deleted = []
    for p in (_MODEL_PATH, _LABELS_PATH):
        if p.exists():
            p.unlink()
            deleted.append(p.name)

    if deleted:
        print(f"  [DEL] Deleted: {', '.join(deleted)}")
        print("  Face model cleared. Run  python face_auth.py --train  to retrain.")
    else:
        print("  No face model found -- nothing to delete.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    # Load .env for FACE_AUTH flag
    _env_path = Path(__file__).parent.parent / ".env"
    if _env_path.exists():
        for _line in _env_path.read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

    # Re-evaluate after loading env
    _FACE_AUTH_ENABLED = os.getenv("FACE_AUTH", "false").lower() in ("1", "true", "yes")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")

    parser = argparse.ArgumentParser(
        description="F.R.I.D.A.Y. Face Authentication",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--train",  action="store_true",
        help="Capture and train your face model (run once)"
    )
    parser.add_argument(
        "--verify", action="store_true",
        help="Test face verification manually"
    )
    parser.add_argument(
        "--reset",  action="store_true",
        help="Delete the saved face model"
    )
    parser.add_argument(
        "--name",   default="owner",
        help="Your name, used during training (default: owner)"
    )
    args = parser.parse_args()

    if args.reset:
        reset_face_model()

    if args.train:
        success = train_face(user_name=args.name)
        if success:
            print()
            print("  NOTE: Don't forget to add  FACE_AUTH=true  to your .env")
            print("        to enable face auth on every F.R.I.D.A.Y. startup.")

    elif args.verify:
        if not _FACE_AUTH_ENABLED:
            print("  [INFO] FACE_AUTH is not enabled in .env — running verification anyway for testing.")
            # Override for this test session
            _FACE_AUTH_ENABLED = True  # noqa: F841 — module-level var used below

        if not _model_exists():
            print("  [FAIL] No face model found. Run:  python face_auth.py --train  first.")
            sys.exit(1)

        print("  Starting face verification test...")
        result = verify_face()

        if result is True:
            print("  [OK] GRANTED -- Face recognized.")
        elif result is False:
            print("  [FAIL] DENIED -- Face not recognized. Restricted mode would activate.")
        else:
            print("  [SKIP] SKIPPED -- Auth disabled or webcam unavailable.")

    else:
        parser.print_help()
