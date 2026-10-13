<div align="center">

# 🖥️ GestiVox

### A Smart Hands-Free Interaction System

Control your Windows desktop through hand tracking and the Proton voice assistant.

![Python 3.10](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)
![Windows](https://img.shields.io/badge/Platform-Windows-0078D4)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.9-0097A7)
![OpenCV](https://img.shields.io/badge/OpenCV-4.6-5C3EE8?logo=opencv&logoColor=white)
[![MIT License](https://img.shields.io/badge/License-MIT-22C55E)](LICENSE)
![Status](https://img.shields.io/badge/Status-Prototype-F59E0B)

[Get started](#installation) · [Gesture guide](#gestures) · [Voice commands](#proton) · [Troubleshooting](#troubleshooting)

</div>

---

GestiVox brings two interaction modes into one Windows desktop project:
**webcam gestures** for pointer and system control, and **Proton** for voice
commands, spoken responses, and a local browser chat interface. Run the
gesture controller independently or launch it from the assistant.

## ✨ What you can do

| | Capability | How it works |
| --- | --- | --- |
| 🖱️ | Pointer control | Move, click, double-click, right-click, and drag with hand poses |
| ↕️ | Scrolling | Use four fingers for vertical or Shift + wheel horizontal scrolling |
| 🔊 | Volume | Change the distance between your thumb and index finger |
| ☀️ | Brightness | Change the distance between your thumb and pinky on supported displays |
| 🎙️ | Voice commands | Search, open Maps, get the date/time, copy/paste, and navigate files |
| 🔗 | Integrated control | Ask Proton to start or stop gesture recognition |
| 📷 | Visual feedback | View hand landmarks and the detected gesture in the camera preview |

## 🧭 Contents

- [System requirements](#requirements)
- [Installation](#installation)
- [Gesture control](#gestures)
- [Proton assistant](#proton)
- [How it works](#architecture)
- [Repository layout](#layout)
- [Troubleshooting](#troubleshooting)
- [Development and status](#development)
- [License](#license)

<a id="requirements"></a>

## 🧰 System requirements

| Component | Requirement |
| --- | --- |
| Operating system | Windows; audio control, SAPI5 speech, and file opening use Windows APIs |
| Python | Python 3.10, matching the verified local environment |
| Camera | Available webcam; the gesture controller selects camera index `0` |
| Audio | Microphone and an available speaker device for Proton |
| Browser | Google Chrome for the Eel chat window |
| Network | Package installation, Google speech recognition, web search, and Maps |

Hand tracking runs locally. Proton sends captured speech to Google's speech
recognition service. Display brightness support depends on the monitor and
driver. The project has not been validated on macOS or Linux.

<a id="installation"></a>

## 🚀 Installation

### 1. Open the project

Clone your GitHub repository or download it, then open PowerShell in its root
folder.

### 2. Create a Python 3.10 environment

```powershell
py -3.10 -m venv venv
```

### 3. Install dependencies

```powershell
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

The commands below call the environment's interpreter directly, so activation
is optional. Virtual environments contain location-specific paths: recreate
one after moving or renaming the project instead of copying it between machines.

`requirements.txt` pins the packages recorded from the existing environment.
That environment passed `pip check` and core library import checks. A clean
installation of every pinned package has not yet been verified.

> [!IMPORTANT]
> Use `venv\Scripts\python.exe` to run this project. Plain `python` may select
> a different installation. This code uses MediaPipe's legacy Solutions API;
> the verified environment has **MediaPipe 0.10.9**. MediaPipe **0.10.35** in
> the system environment does not provide the required `mediapipe.python`
> module.

<a id="gestures"></a>

## 🖐️ Gesture control

### Start the controller

```powershell
.\venv\Scripts\python.exe .\Gesture_Controller.py
```

Allow camera access and keep one hand visible in good lighting. The preview
shows the current gesture. Press **Esc** while the preview is focused to quit.
An open palm pauses gesture actions.

### Gesture reference

| Hand pose | Action |
| --- | --- |
| Index and middle fingers extended | Move pointer; arm the next click |
| Index finger extended | Left-click after the move pose |
| Middle finger extended | Double-click after the move pose |
| Pinky extended | Right-click after the move pose |
| Fist | Hold left mouse button and move to drag; change pose to release |
| Four fingers extended, thumb folded | Scroll; sideways motion sends Shift + wheel |
| Thumb and index extended in an L | Adjust volume by changing fingertip distance |
| Thumb and pinky extended in a shaka | Adjust brightness by changing fingertip distance |
| Open palm | Pause actions and clear the click-ready state |

Horizontal scrolling depends on the target application's handling of Shift +
wheel. Pose recognition uses finger positions and a short stability delay,
so camera angle and hand orientation affect detection.

> [!CAUTION]
> The current controller disables PyAutoGUI's corner failsafe. Keep the
> keyboard accessible and press **Esc** with the preview focused to exit.
> Losing hand tracking during a drag does not currently guarantee immediate
> mouse release.

<a id="proton"></a>

## 🎙️ Proton assistant

### Start the assistant

```powershell
.\venv\Scripts\python.exe .\Proton.py
```

Proton opens a Chrome chat window served locally on port `27005`. Say commands
with the word **proton**. Use that prefix for typed commands as well, since the
current command loop applies its wake-word check after reading the chat queue.

### Command reference

| Example command | Result |
| --- | --- |
| `proton hello` | Greeting |
| `proton date` / `proton time` | Current session date / current time |
| `proton search computer vision` | Open Google search |
| `proton location` | Ask for a place through the microphone, then open Maps |
| `proton launch gesture recognition` | Start the main gesture controller |
| `proton stop gesture recognition` | Stop the running gesture process |
| `proton copy` / `proton paste` | Send Ctrl+C / Ctrl+V to the focused application |
| `proton list` | List files and directories on C: |
| `proton open 1` / `proton back` | Navigate the numbered file list |
| `proton bye` / `proton wake up` | Put the assistant to sleep / wake it |
| `proton exit` | Exit and stop its gesture subprocess |

Start Proton from the project root. Its gesture subprocess resolves the script
relative to `Proton.py`, so the project name is not hardcoded.

<a id="architecture"></a>

## ⚙️ How it works

| Mode | Processing flow |
| --- | --- |
| 🖐️ Gestures | Webcam → OpenCV frames → MediaPipe hand landmarks → pose recognition → mouse, volume, or brightness action |
| 🎙️ Speech | Microphone → Google speech recognition → Proton command dispatcher → desktop action and spoken reply |
| 💬 Chat | Browser input → Eel bridge → Proton command dispatcher → chat response |

The main controller tracks one hand, smooths pointer movement, and waits for
a pose to remain stable across frames before changing the recognized gesture.
Proton starts gesture control in a separate process using the same Python
interpreter as the assistant.

<a id="layout"></a>

## 📁 Repository layout

```text
GestiVox/
|-- Gesture_Controller.py       # Main MediaPipe gesture controller
|-- Proton.py                   # Voice assistant and command dispatcher
|-- app.py                      # Eel bridge and chat window lifecycle
|-- web/                        # Chat HTML, JavaScript, CSS, and images
|-- experimental/
|   |-- Gesture_Controller_Gloved.py
|   |-- calib_images/           # Existing checkerboards and calibration data
|   `-- README.md
|-- requirements.txt            # Pinned environment dependencies
|-- CONTRIBUTING.md
|-- LICENSE
|-- .editorconfig
|-- .gitattributes
`-- .gitignore
```

`venv/`, Python caches, and `.local/` are local-only and ignored by Git.

The [experimental glove controller](experimental/README.md) is preserved
separately with its calibration assets. It uses ArUco markers and legacy
OpenCV APIs, and has no executable entry point.

<a id="troubleshooting"></a>

## 🛠️ Troubleshooting

| Symptom | Check |
| --- | --- |
| `No module named 'mediapipe.python'` | Run with `.\venv\Scripts\python.exe .\Gesture_Controller.py`; use the pinned MediaPipe version from `requirements.txt` |
| Python cannot start after a folder move | Recreate `venv` using Python 3.10; do not reuse activation paths from the old folder |
| Missing module | Install `requirements.txt` using the same interpreter used to launch the script |
| Camera unavailable | Close other camera applications and check Windows camera permissions |
| Voice commands fail | Check the default microphone, microphone permissions, and network access |
| Brightness does not change | Check whether your display supports software brightness control |
| Assistant chat does not open | Confirm Chrome is installed and port `27005` is available; the current startup loop can wait indefinitely if the UI fails |
| ArUco errors in the glove prototype | Check the recorded OpenCV version and the experimental README |

<details>
<summary>🔍 Check the Python interpreter and MediaPipe version</summary>

Run these commands from the repository root:

```powershell
.\venv\Scripts\python.exe -c "import sys, mediapipe; print(sys.executable); print(mediapipe.__version__)"
.\venv\Scripts\python.exe -m pip check
```

The interpreter path should point inside this project's `venv`, and the
recorded MediaPipe version is `0.10.9`.

</details>

<a id="development"></a>

## 🤝 Development and status

This is a desktop prototype with hardware-dependent behavior. The main gesture
script has been started successfully in the existing Windows environment.
The assistant and glove prototype have not undergone an end-to-end hardware
test during repository preparation. There is no automated hardware test suite.

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and verification steps.

### Verification commands

```powershell
.\venv\Scripts\python.exe -m compileall -q Gesture_Controller.py Proton.py app.py experimental
.\venv\Scripts\python.exe -m pip check
```

These checks validate syntax and dependency consistency. Gesture recognition,
audio, brightness, and browser behavior require manual testing on hardware.

### Preparing a GitHub commit

Commit the source, web assets, documentation, and `requirements.txt`.
The included `.gitignore` excludes `venv/`, caches, editor settings, and local
scratch files. Each contributor should create their own environment after
cloning the repository.

<a id="license"></a>

## 📄 License

GestiVox is provided under the [MIT License](LICENSE). Dependency packages
retain their own licenses. Preserve any applicable upstream notices for reused
code or assets; the project license does not replace third-party obligations.
