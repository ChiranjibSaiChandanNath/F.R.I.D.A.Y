# FRIDAY

<div align="center">

<!-- Animated multi-line typing title -->
<img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=900&size=30&duration=2800&pause=900&color=4FC3F7&center=true&vCenter=true&multiline=false&width=720&lines=F.R.I.D.A.Y..+%E2%80%94+Voice+Assistant;Local+Kokoro+TTS+%7C+Groq+Llama+3.3" alt="F.R.I.D.A.Y.." />

<br/>

<!-- Enhanced animated SVG — glowing cap with pulse rings + orbiting dots -->
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200">
  <defs>
    <radialGradient id="pulseGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#4FC3F7" stop-opacity="0.22"/>
      <stop offset="70%" stop-color="#7C4DFF" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#4FC3F7" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="#4FC3F7" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <!-- Soft background glow -->
  <circle cx="100" cy="100" r="90" fill="url(#pulseGlow)">
    <animate attributeName="r" values="80;92;80" dur="4s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.6;1;0.6" dur="4s" repeatCount="indefinite"/>
  </circle>

  <!-- Static reference rings -->
  <circle cx="100" cy="100" r="88" fill="none" stroke="#4FC3F7" stroke-width="0.5" stroke-opacity="0.12"/>
  <circle cx="100" cy="100" r="70" fill="none" stroke="#4FC3F7" stroke-width="0.5" stroke-opacity="0.12"/>
  <circle cx="100" cy="100" r="50" fill="none" stroke="#7C4DFF" stroke-width="0.5" stroke-opacity="0.12"/>

  <!-- Crosshair guides -->
  <line x1="100" y1="12" x2="100" y2="188" stroke="#4FC3F7" stroke-width="0.4" stroke-opacity="0.15"/>
  <line x1="12" y1="100" x2="188" y2="100" stroke="#4FC3F7" stroke-width="0.4" stroke-opacity="0.15"/>

  <!-- Outer spinning dashed ring -->
  <circle cx="100" cy="100" r="88" fill="none" stroke="#4FC3F7" stroke-width="1.4"
    stroke-dasharray="18 9" stroke-linecap="round" stroke-opacity="0.65">
    <animateTransform attributeName="transform" type="rotate"
      from="0 100 100" to="360 100 100" dur="10s" repeatCount="indefinite"/>
  </circle>

  <!-- Middle counter-rotating dashed ring -->
  <circle cx="100" cy="100" r="72" fill="none" stroke="#7C4DFF" stroke-width="0.9"
    stroke-dasharray="7 6" stroke-opacity="0.5">
    <animateTransform attributeName="transform" type="rotate"
      from="360 100 100" to="0 100 100" dur="7s" repeatCount="indefinite"/>
  </circle>

  <!-- Inner pulse ring -->
  <circle cx="100" cy="100" r="50" fill="none" stroke="#00e676" stroke-width="0.7"
    stroke-dasharray="4 8" stroke-opacity="0.4">
    <animateTransform attributeName="transform" type="rotate"
      from="0 100 100" to="360 100 100" dur="4s" repeatCount="indefinite"/>
    <animate attributeName="stroke-opacity" values="0.2;0.6;0.2" dur="3s" repeatCount="indefinite"/>
  </circle>

  <!-- Orbiting dot 1 (cyan, outer ring) -->
  <circle r="4" fill="#4FC3F7" opacity="0.9">
    <animateMotion dur="10s" repeatCount="indefinite">
      <mpath href="#orbit1"/>
    </animateMotion>
    <animate attributeName="opacity" values="0.6;1;0.6" dur="2s" repeatCount="indefinite"/>
  </circle>
  <path id="orbit1" d="M 100,12 A 88,88 0 1 1 99.9,12" fill="none"/>

  <!-- Orbiting dot 2 (purple, middle ring, opposite phase) -->
  <circle r="3" fill="#7C4DFF" opacity="0.8">
    <animateMotion dur="7s" repeatCount="indefinite" keyPoints="0.5;1;0.5" keyTimes="0;0.5;1" calcMode="linear">
      <mpath href="#orbit2"/>
    </animateMotion>
  </circle>
  <path id="orbit2" d="M 100,28 A 72,72 0 1 1 99.9,28" fill="none"/>

  <!-- Orbiting dot 3 (green, inner ring) -->
  <circle r="2.5" fill="#00e676" opacity="0.7">
    <animateMotion dur="4s" repeatCount="indefinite" keyPoints="0.25;1;0.25" keyTimes="0;0.5;1" calcMode="linear">
      <mpath href="#orbit3"/>
    </animateMotion>
  </circle>
  <path id="orbit3" d="M 100,50 A 50,50 0 1 1 99.9,50" fill="none"/>

  <!-- Arc Reactor Outer Ring -->
  <circle cx="100" cy="100" r="28" fill="none" stroke="#4FC3F7" stroke-width="1.8" stroke-opacity="0.8">
    <animate attributeName="stroke-opacity" values="0.5;1;0.5" dur="2s" repeatCount="indefinite"/>
  </circle>
  <!-- Arc Reactor Inner Core -->
  <circle cx="100" cy="100" r="14" fill="rgba(79,195,247,0.18)" stroke="#4FC3F7" stroke-width="2.5">
    <animate attributeName="r" values="12;15;12" dur="2s" repeatCount="indefinite"/>
  </circle>
  <!-- Arc Reactor Segments (Triangular / Lines radiating) -->
  <g stroke="#4FC3F7" stroke-width="1.5" stroke-opacity="0.7">
    <line x1="100" y1="68" x2="100" y2="76" />
    <line x1="100" y1="124" x2="100" y2="132" />
    <line x1="68" y1="100" x2="76" y2="100" />
    <line x1="124" y1="100" x2="132" y2="100" />
    <line x1="77" y1="77" x2="83" y2="83" />
    <line x1="123" y1="123" x2="117" y2="117" />
    <line x1="77" y1="123" x2="83" y2="117" />
    <line x1="123" y1="77" x2="117" y2="83" />
  </g>

  <!-- Core centre glow -->
  <circle cx="100" cy="100" r="16" fill="url(#coreGlow)">
    <animate attributeName="r" values="14;18;14" dur="2.5s" repeatCount="indefinite"/>
    <animate attributeName="opacity" values="0.5;1;0.5" dur="2.5s" repeatCount="indefinite"/>
  </circle>

  <!-- Corner blinking status dots -->
  <circle cx="28" cy="38" r="2.5" fill="#4FC3F7">
    <animate attributeName="opacity" values="0;1;0" dur="2.2s" begin="0.1s" repeatCount="indefinite"/>
  </circle>
  <circle cx="172" cy="140" r="2.5" fill="#7C4DFF">
    <animate attributeName="opacity" values="0;1;0" dur="2.7s" begin="0.7s" repeatCount="indefinite"/>
  </circle>
  <circle cx="164" cy="34" r="2" fill="#00e676">
    <animate attributeName="opacity" values="0;1;0" dur="2s" begin="1.2s" repeatCount="indefinite"/>
  </circle>
  <circle cx="34" cy="152" r="2" fill="#ff6d00">
    <animate attributeName="opacity" values="0;1;0" dur="2.4s" begin="0.4s" repeatCount="indefinite"/>
  </circle>
  <circle cx="100" cy="16" r="1.8" fill="#4FC3F7" opacity="0.5">
    <animate attributeName="opacity" values="0.2;0.9;0.2" dur="1.8s" begin="0.9s" repeatCount="indefinite"/>
  </circle>
</svg>

<br/>

<!-- Badge row 1: Core stack -->
![Python](https://img.shields.io/badge/Python-3.11+-4FC3F7?style=for-the-badge&logo=python&logoColor=black&labelColor=0a0f1e)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-7C4DFF?style=for-the-badge&logo=fastapi&logoColor=white&labelColor=0a0f1e)
![TypeScript](https://img.shields.io/badge/TypeScript-Vite-ff6d00?style=for-the-badge&logo=typescript&logoColor=white&labelColor=0a0f1e)
![Three.js](https://img.shields.io/badge/Three.js-Orb-00e676?style=for-the-badge&logo=three.js&logoColor=white&labelColor=0a0f1e)

<br/>

<!-- Badge row 2: Tools & status -->
![Groq](https://img.shields.io/badge/Groq-API-4FC3F7?style=for-the-badge&labelColor=0a0f1e)
![Llama 3.3](https://img.shields.io/badge/Llama_3.3-LLM-7C4DFF?style=for-the-badge&labelColor=0a0f1e)
![Kokoro TTS](https://img.shields.io/badge/Kokoro_TTS-ONNX-00e676?style=for-the-badge&labelColor=0a0f1e)
![SQLite](https://img.shields.io/badge/SQLite-Memory-ff6d00?style=for-the-badge&logo=sqlite&logoColor=white&labelColor=0a0f1e)
![Status](https://img.shields.io/badge/Status-Active-00e676?style=for-the-badge&labelColor=0a0f1e)


<br/>

> **A Voice-First AI Assistant with Local Speech Synthesis, and Groq Llama 3.3 Reasoning**

> [!NOTE]
> **F.R.I.D.A.Y.** is designed for advanced usage, offering full device control and deep system integration. If you prefer a simpler, more basic AI assistant experience without the complex system integrations, please check out my other project: [Jarvis](https://github.com/ChiranjibSaiChandanNath/Jarvis.git).

<br/>

<!-- GitHub repo stats -->
[![Stars](https://img.shields.io/github/stars/ChiranjibSaiChandanNath/F.R.I.D.A.Y.?style=social)](https://github.com/ChiranjibSaiChandanNath/F.R.I.D.A.Y./stargazers)
[![Forks](https://img.shields.io/github/forks/ChiranjibSaiChandanNath/F.R.I.D.A.Y.?style=social)](https://github.com/ChiranjibSaiChandanNath/F.R.I.D.A.Y./network/members)
[![Issues](https://img.shields.io/github/issues/ChiranjibSaiChandanNath/F.R.I.D.A.Y.?color=ff6d00&style=flat-square)](https://github.com/ChiranjibSaiChandanNath/F.R.I.D.A.Y./issues)
[![Last Commit](https://img.shields.io/github/last-commit/ChiranjibSaiChandanNath/F.R.I.D.A.Y.?color=00e676&style=flat-square)](https://github.com/ChiranjibSaiChandanNath/F.R.I.D.A.Y./commits)

<br/>

> If you find this project useful, please consider giving it a **⭐ Star** — it really helps! 👆

</div>

<!-- Animated wave divider -->
<div align="center">
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="60" viewBox="0 0 900 60" preserveAspectRatio="none">
  <defs>
    <linearGradient id="waveGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="#4FC3F7" stop-opacity="0"/>
      <stop offset="20%"  stop-color="#4FC3F7" stop-opacity="0.6"/>
      <stop offset="50%"  stop-color="#7C4DFF" stop-opacity="0.6"/>
      <stop offset="80%"  stop-color="#00e676" stop-opacity="0.6"/>
      <stop offset="100%" stop-color="#00e676" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <path d="M0,30 C150,55 300,5 450,30 C600,55 750,5 900,30" fill="none" stroke="url(#waveGrad)" stroke-width="2">
    <animate attributeName="d"
      values="M0,30 C150,55 300,5 450,30 C600,55 750,5 900,30;
              M0,30 C150,5 300,55 450,30 C600,5 750,55 900,30;
              M0,30 C150,55 300,5 450,30 C600,55 750,5 900,30"
      dur="5s" repeatCount="indefinite"/>
  </path>
  <path d="M0,38 C150,62 300,14 450,38 C600,62 750,14 900,38" fill="none" stroke="url(#waveGrad)" stroke-width="1" opacity="0.4">
    <animate attributeName="d"
      values="M0,38 C150,62 300,14 450,38 C600,62 750,14 900,38;
              M0,38 C150,14 300,62 450,38 C600,14 750,62 900,38;
              M0,38 C150,62 300,14 450,38 C600,62 750,14 900,38"
      dur="5s" begin="0.8s" repeatCount="indefinite"/>
  </path>
</svg>
</div>

> [!IMPORTANT]
> **Always use Google Chrome for the best result.** The voice transcription engine (Web Speech API) is most stable and natively supported in Google Chrome. Other browsers (like Edge, Firefox, or Brave) may fail to capture voice input or raise network connection errors.

---

## Features

- **Biometric Lockscreen UI** — Secure browser startup with webcam face scanning and voice passphrase fallback (`"wake up to reality"`)
- **🎙️ Continuous Listening** — Speak directly to FRIDAY — no wake-word activation required. The microphone remains active and processes your commands instantly.
- **Real-time Battery Status** — *"What's my battery percentage?"* gives the actual live %, charging state, and time remaining — no guessing
- **PC System Controls** — Toggle WiFi, Bluetooth, and switch between Dark / Light mode entirely by voice
- **YouTube Autoplay** — *"Open YouTube and play Kesariya"* searches YouTube and auto-clicks the first result to start playing
- **Voice Browser Interaction** — Click buttons, open results, type text and press keys in any browser window — all by voice
- **Voice Browser Tab Control** — Scroll, switch/open/close tabs, zoom, and focus search bars on any open browser using pyautogui
- **Gmail API Integration** — Read your recent emails and send outbound messages natively (cross-platform)
- **Voice conversation** — speak naturally, FRIDAY listens and replies with a local British voice
- **Groq LLM** — powered by `llama-3.3-70b-versatile` for reasoning and `llama-4-scout` for vision
- **Local Kokoro TTS** — British male voice (`bm_george`) runs fully on CPU via ONNX, no cost
- **Real-time Weather** — *"What's the weather?"* or *"Weather in Tokyo?"* via OpenWeatherMap
- **Smart Web Browsing** — *"Search for black holes"*, *"Open github.com"*, *"Search YouTube for lofi"*
- **Task & Notes** — *"Remind me to call the client"*, *"Save that as a note"*
- **Memory** — remembers your facts, project context, and preferences across sessions
- **Screen Vision** — *"What's on my screen?"* triggers a screenshot and AI description
- **Smart App Launcher** — *"Open Notepad"*, *"Open Spotify"*, *"Launch VS Code"*, *"Open VLC"* — uses 4-layer discovery. If the app isn't installed, F.R.I.D.A.Y. asks whether to open the **official download page in Chrome** or go directly to the **Microsoft Store app page**
- **Write to Notepad** — *"Write a shopping list in Notepad"* creates and opens it instantly
- **Refined personality** — Uses *"sir"* only for greetings and important moments, not after every sentence
- **Audio-reactive Orb** — Three.js particle orb that pulses with your voice; dims to a dark inactive state when muted

---

## 🎙️ Voice Interaction & Orb States

FRIDAY listens to your speech continuously when unmuted. You can speak your commands directly without needing a wake word.

### Orb States

| Orb Appearance | State | Meaning |
|---|---|---|
| 🔵 Bright, active pulse | **Listening** | Active and capturing your command |
| 💡 Fast swirl + electrons | **Thinking** | Processing your request |
| 🔊 Audio-reactive pulse | **Speaking** | FRIDAY is responding |
| 🌑 Dark, dim, slow drift | **Inactive (Sleeping)** | Dims to this state when muted or booting |

### Behaviour
- **Always Listening** — Speak your query or command directly at any time.
- **Auto-Clean** — If you say "Hey Friday" out of habit, the system automatically strips the prefix before processing.
- **Mute Button** — Muting pauses the microphone and turns the orb to an inactive/sleeping state. Unmuting instantly resumes continuous listening.
- **No extra libraries** — Runs entirely in the browser using the Web Speech API; no Python changes needed.

---

## 🖥️ PC System Controls

Control your Windows PC entirely by voice — no clicking, no settings menus.

### 🔋 Battery
| Say | Action |
|-----|--------|
| *"What's my battery percentage?"* | Reports exact %, charging status & time remaining |
| *"How much battery do I have?"* | Same |

### 📶 WiFi
| Say | Action |
|-----|--------|
| *"Turn on WiFi"* / *"Enable WiFi"* | Enables the wireless adapter |
| *"Turn off WiFi"* / *"Disable WiFi"* | Disables the wireless adapter |
| *"WiFi on"* / *"WiFi off"* | Short-form toggle |

### 🦷 Bluetooth
| Say | Action |
|-----|--------|
| *"Turn on Bluetooth"* / *"Enable Bluetooth"* | Enables Bluetooth via Device Manager |
| *"Turn off Bluetooth"* / *"Disable Bluetooth"* | Disables Bluetooth |
| *"Bluetooth on"* / *"Bluetooth off"* | Short-form toggle |

### 🌙 Dark / Light Mode
| Say | Action |
|-----|--------|
| *"Dark mode"* / *"Night mode"* / *"Go dark"* | Switches Windows to dark theme instantly |
| *"Light mode"* / *"White mode"* / *"Bright mode"* | Switches Windows to light theme instantly |
| *"Switch to dark"* / *"Switch to light"* | Also works |

> Dark/Light mode switches the Windows registry instantly — no admin rights required. WiFi/Bluetooth may show a UAC prompt depending on your system config.

### 🎵 System Media Controls (New)
| Say | Action |
|-----|--------|
| *"play music"* / *"resume music"* / *"play"* / *"play/pause"* | Simulates the hardware Play/Pause key to toggle active media |
| *"pause music"* / *"pause the track"* / *"pause"* | Pauses active media playback |
| *"next song"* / *"skip track"* / *"skip"* / *"next"* | Skips to the next track |
| *"previous song"* / *"go back a track"* / *"previous"* / *"prev"* | Goes back to the previous track or restarts current track |
| *"stop music"* / *"stop"* | Stops active media playback |

> Media controls use hardware simulation via PyAutoGUI, meaning they globally control whichever media player has background focus (Spotify, Chrome, YouTube, VLC, etc.).

---

## ▶️ YouTube Autoplay (New)

Say a song or playlist name with "play" and FRIDAY opens YouTube search and **automatically clicks the first result** — no need to click yourself.

| Say | What Happens |
|-----|--------------|
| *"Open YouTube and play Kesariya"* | Opens YouTube search → auto-clicks 1st video |
| *"Play Tum Hi Ho on YouTube"* | Same |
| *"YouTube play Arijit Singh"* | Searches & autoplays |
| *"Play hindi songs on YouTube"* | Plays first matching result |
| *"Play Raataan Lambiyan on YT"* | Short-form also works |
| *"Open YouTube"* (no song) | Opens YouTube homepage as normal |

> The auto-click fires **3.5 seconds** after the page opens to allow YouTube to render. If your connection is slow, just say *"click first"* manually.

---

## 🖱️ Voice Browser Interaction

FRIDAY can control your open browser window by voice — click buttons, open search results, type text, and press keys, all hands-free.

### Clicking elements by text
| Say | Action |
|-----|--------|
| *"click Sign In"* | Clicks the element labelled **Sign In** |
| *"click on the search button"* | Clicks the **search button** |
| *"press Submit"* | Clicks the **Submit** button |
| *"tap the Download button"* | Clicks **Download** |

### Opening results by position (YouTube, Google, etc.)
| Say | Action |
|-----|--------|
| *"click first song"* | Opens the **1st** result on the page |
| *"open first result"* | Same as above |
| *"play first video"* | Opens the **1st** result |
| *"click second video"* | Opens the **2nd** result |
| *"open the third result"* | Opens the **3rd** result |
| *"click 2nd"* | Opens the **2nd** result |

### Typing & keyboard
| Say | Action |
|-----|--------|
| *"type python tutorials"* | Types text into the focused field |
| *"press enter"* | Presses the **Enter** key |
| *"press escape"* | Presses the **Escape** key |
| *"press tab"* | Presses the **Tab** key |

> **How it works:** Uses Windows `.NET UIAutomation` (via PowerShell) to find elements in the live browser accessibility tree — no OCR, no image templates needed. Falls back to Tab+Enter keyboard navigation if UIA fails.

---

## 🌐 Voice Browser Tab Commands

| Say | Action |
|-----|--------|
| *"scroll down"* / *"scroll up"* | Scroll the page |
| *"next tab"* / *"previous tab"* | Switch browser tabs |
| *"new tab"* / *"close tab"* | Open or close a tab |
| *"go back"* / *"go forward"* | Browser navigation |
| *"refresh"* / *"reload"* | Reload the page |
| *"zoom in"* / *"zoom out"* | Zoom level |
| *"open incognito"* | New private window |
| *"address bar"* | Focus the URL bar |

---

## 📦 Smart App Launcher

F.R.I.D.A.Y. uses a **4-layer auto-discovery system** to open any installed app — no need to know the exact executable name.

### Discovery Order

| Layer | Method | Example |
|---|---|---|
| 1 | Hardcoded alias mapping | `"teams"` → `msteams:`, `"vs code"` → `code` |
| 2 | Windows App Paths registry | Finds Steam, Photoshop, any registered app |
| 3 | Start Menu shortcut scan | Games, custom installs with `.lnk` shortcuts |
| 4 | Raw name as executable | CLI tools in PATH |

### If the App Isn't Installed

When all 4 layers fail, F.R.I.D.A.Y. asks where to find it:

```
You: "Open VLC"
        ↓
F.R.I.D.A.Y.: "I couldn't find VLC on your system.
               Should I search for it on the Microsoft Store or Chrome?"
        ↓
  "Chrome"  →  Opens official download page: videolan.org/vlc/download-windows
  "Store"   →  Opens Microsoft Store app page directly (no search needed)
```

For **unknown apps**, it falls back to a Google search or Store search automatically.

### Supported Direct Links

| App | Chrome → Official Site | Microsoft Store |
|---|---|---|
| VLC | videolan.org | ✅ Direct page |
| Spotify | spotify.com/download | ✅ Direct page |
| WhatsApp | whatsapp.com/download | ✅ Direct page |
| Microsoft Teams | microsoft.com/teams | ✅ Direct page |
| Telegram | desktop.telegram.org | ✅ Direct page |
| Zoom | zoom.us/download | ✅ Direct page |
| Discord | discord.com/download | ✅ Direct page |
| VS Code | code.visualstudio.com | — |
| Firefox | mozilla.org | — |
| Slack | slack.com/downloads | — |
| Notion | notion.so/desktop | — |
| Steam, Epic, 7-Zip… | Official site | — |
| **Any other app** | Google search | Store search |

> **Keywords:** Say `"chrome"` / `"google"` / `"browser"` for the web path, or `"store"` / `"microsoft store"` for the Store path.

---

## Step-by-Step Windows Setup Guide

Follow this guide to get FRIDAY running from scratch on Windows.

### 1. Prerequisites
Ensure you have the following installed on Windows:
- **Python 3.10+** (Ensure "Add Python to PATH" is checked during installation)
- **Node.js 18+** (Ensure "Add to PATH" is checked during installation; includes `npm`. If you don't have it, run `winget install OpenJS.NodeJS.LTS` in a new Command Prompt and restart your terminal)
- **Google Chrome** (required for Web Speech API transcription)
- **Groq API key** — Powers the LLM brain for free ([Get one here](https://console.groq.com/))
- **OpenWeatherMap API key** (Optional) — Powers real-time weather details ([Get one here](https://openweathermap.org/api))
- **Google OAuth Credentials (`credentials.json`)** (Optional) — Required if you want FRIDAY to read/write emails and access your calendar. (Download a Desktop app credentials JSON from the Google Cloud Console and place it in the `data/` folder).


### 2. Setup Files & Dependencies

1. Clone the repository and navigate to the project folder:
   ```cmd
   git clone https://github.com/ChiranjibSaiChandanNath/F.R.I.D.A.Y.git
   cd F.R.I.D.A.Y.
   ```

2. Install Python dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

3. Install additional packages needed for local voice synthesis:
   ```cmd
   pip install kokoro-onnx soundfile
   ```

4. Install frontend Node dependencies:
   ```cmd
   cd frontend
   npm install
   cd ..
   ```

### 3. Download Local Kokoro TTS Models
We use local Kokoro voice generation. Run the download script once to fetch the ONNX model files:
```cmd
python lib/download_kokoro.py
```
This downloads `kokoro-v1.0.onnx` and the `voices-v1.0.bin` files to your project folder (~340MB total).

---

## Running FRIDAY

### ⚡ Option A — One Command (Recommended)

Double-click **`start.bat`** or run in CMD from the `F.R.I.D.A.Y.` folder:
```cmd
start.bat
```

> **First time only:**
> 1. If no `.env` file exists, `start.bat` automatically copies `.env.example` to `.env` and opens Notepad so you can fill in your API keys (e.g. `GROQ_API_KEY`).
> 2. It asks if you want to enable Face and Voice Unlock. If accepted, it runs a camera training session and prompts you to set a backup passphrase.
> 3. It asks if you want to integrate Gmail & Google Calendar. If accepted:
>    * It checks if `credentials.json` is in the `data/` folder.
>    * If missing, it opens the Google Cloud Console in your browser so you can obtain it.
>    * **Important:** This step cannot be automated. You must manually download the Desktop App credentials JSON file, rename it to `credentials.json`, place it in the `Friday/data/` folder, and then return to the prompt to confirm.
> 4. It prompts you to enter your name (e.g. John, Tony, Alex) and how FRIDAY should address you (sir, ma'am, boss, chief, etc.) and updates your configuration.
>
> **Every time after that:** FRIDAY starts directly, automatically prompting you for a biometric face scan or voice passphrase to unlock if enabled.

`start.bat` does everything automatically:

| Step | What happens |
|---|---|
| 1 | Opens **FRIDAY Backend** window → `py server.py` |
| 2 | Opens **FRIDAY Frontend** window → `cd frontend && npm run dev` |
| 3 | Waits 3 seconds for Vite to spin up |
| 4 | Opens **Google Chrome** at `http://localhost:5173` automatically |

---

### 🖥️ Option B — Manual (Two Terminals)

If you prefer to run each part yourself:

**Terminal 1 — Backend:**
```cmd
py server.py
```
*Expected output:*
```
[friday] Initializing Kokoro TTS model...
[friday] Kokoro TTS initialized successfully.
Uvicorn running on http://0.0.0.0:8340
```

**Terminal 2 — Frontend:**
```cmd
cd frontend
npm run dev
```

> **Note:** If using Option B for the first time, manually copy `.env.example` to `.env` and fill in your keys:
> ```cmd
> copy .env.example .env
> notepad .env
> ```

---

### Open the Application
- **Local Access**: Open Google Chrome and navigate to **`http://localhost:5173`**
- **Mobile / Local Network**: Connect your phone to the same Wi-Fi, then open Chrome and go to the **Network** IP shown in your frontend terminal (e.g. **`http://192.168.1.15:5173`**)

Click anywhere on the orb page once to activate the audio system. FRIDAY will greet you: *"Good morning, sir."*



## Troubleshooting Voice / Microphone Issues on Windows

If FRIDAY greets you but does not respond when you speak:

### 1. "recognition error: network"
If you see this error in Edge/Brave, it means the browser's speech-to-text service is blocked.
- **Fix:** Use **Google Chrome** instead.
- **Brave Fix:** Go to `brave://settings/privacy`, turn ON **"Use Google services for push messaging and speech recognition"**, and restart.

### 2. Silence (No logs appearing when speaking)
If it says `listening...` but doesn't capture your voice:
1. **Chrome Settings:** Paste `chrome://settings/content/microphone` in a new Chrome tab and hit Enter. Make sure your active microphone hardware (e.g. *Microphone (Realtek Audio)*) is selected in the dropdown rather than a virtual driver.
2. **Windows Settings:** Open **Settings** > **Privacy & security** > **Microphone**. Verify:
   - *Microphone access* is **ON**.
   - *Let desktop apps access your microphone* is **ON** (and Google Chrome is allowed).
3. **Sound Control:** In Windows Sound settings, verify that your input volume slider is at `100` and the test meter bounces when you talk.
