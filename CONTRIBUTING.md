# Contributing to GestiVox

Thank you for helping improve GestiVox. Changes should make gesture and voice
interaction easier to understand, more reliable, or easier to set up.

## Development setup

Follow the Windows and Python 3.10 setup in [README.md](README.md). Use a local
virtual environment; do not commit it. Keep temporary experiments in `.local/`.

## Proposing a change

1. Describe the issue, your Windows/Python versions, and steps to reproduce it.
2. Make a focused change on a separate branch.
3. Update documentation when commands, gestures, paths, or dependencies change.
4. Check Python syntax and dependency consistency:

   ```powershell
   .\venv\Scripts\python.exe -m compileall -q Gesture_Controller.py Proton.py app.py experimental
   .\venv\Scripts\python.exe -m pip check
   ```

5. For hardware-related changes, manually verify the affected gestures or voice
   commands and describe your webcam, microphone, and display setup in the PR.

Include what changed, why, and how you verified it in your pull request. Do not
claim hardware behavior was tested when only syntax or imports were checked.

## Dependencies and assets

`requirements.txt` records the versions from the working local environment.
When updating dependencies, verify MediaPipe, OpenCV, and protobuf together.
The experimental glove controller uses older ArUco APIs.

Preserve existing third-party license notices and credit the source of any
code, image, or calibration asset you contribute.
