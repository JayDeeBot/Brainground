# Brainground: Closed-loop Neurofeedback BCI in Anxiety Regulation

## Overview

Brainground is a Brain-Computer Interface (BCI) system that integrates EEG-based real-time neurofeedback with a Virtual Reality (VR) environment to support emotional self-regulation. The system detects asymmetry in frontal EEG activity (especially from the F3 and F4 regions) and dynamically adjusts a VR world to encourage practices for overcoming anxiety.

The system includes:

- **EEG Data Acquisition** (from `.edf` files)
- **Signal Processing** (filtering, epoching, asymmetry scoring)
- **Neurofeedback GUI** (score display, emoji visualization)
- **VR World** (lighting responds to the user's emotional state)

---

## Installation Instructions

### 1. Clone the Repository

```bash
cd ~/git
# (example path)
git clone <your-repo-url> Brainground
```

### 2. Set up a Python Environment

We recommend Python 3.8+.

```bash
python3 -m venv brainground-env
source brainground-env/bin/activate
```

### 3. Install Required Packages

```bash
pip install -r requirements.txt
```

If `requirements.txt` is missing, install manually:

```bash
pip install numpy scipy matplotlib PyQt5 mne panda3d simplepbr
```

**Additional:**

- Ensure system has `Panda3D` installed correctly for VR world rendering.
- Tested on Ubuntu 22.04 with Python 3.10.

---

## How to Run

### 1. Prepare EEG Data

- Store your EEG recordings in `.edf` format.
- Ensure that channels F3 and F4 (or equivalent) are available in your file.

### 2. Launch the System

From the root project directory:

```bash
python3 main.py
```

This will:

- Open a PyQt5 GUI for selecting the EEG file, channels, and filter range.
- Start the EEG real-time playback.
- Calculate the asymmetry score based on frontal alpha waves.
- Allow launching a VR world that responds to the emotional score.

### 3. GUI Controls

- **Select EEG File:** Choose a `.edf` EEG recording.
- **Select Channels:** Choose two channels (typically F3 and F4).
- **Set Filter:** Set low and high cut-off frequencies (default: 8-12 Hz for alpha band).
- **Run Scenario:** Starts EEG playback and neurofeedback processing.
- **Launch VR World:** Opens a simple VR environment with dynamic lighting based on user scores.

### 4. VR Environment Behavior

- Lighting brightness reflects user's frontal asymmetry score.
- Higher scores → Brighter environment → Positive emotional reinforcement.
- Lower scores → Dimmer environment → Encourages emotional regulation.

---

## File Structure

| File                  | Description                                                      |
| --------------------- | ---------------------------------------------------------------- |
| `main.py`             | Launches GUI, coordinates Data Acquisition and Signal Processing |
| `data_acquisition.py` | Reads and streams EEG data from `.edf` files                     |
| `scan_processing.py`  | Filters, epochs, and computes asymmetry scores                   |
| `eeg_interface.py`    | PyQt5 GUI for user interaction and feedback                      |
| `vr_world.py`         | Panda3D-based VR scene with real-time lighting control           |

---

## Notes

- Make sure paths to `img/` (emoji faces) and `models/` (skybox) folders are correct in your environment.
- Some hardcoded file paths (e.g., `/home/jarred/git/Brainground/`) may need updating if running on a different machine.

---

## Future Work

- Direct integration with live EEG hardware.
- Expansion of VR world complexity (terrain, weather).
- Optimization of real-time performance for lower latency neurofeedback.
- Broader emotion classification beyond anxiety.

---

## Author

- **Jarred Deluca**

## Supervisor

- **Dr. Yukai Wang**

---

## License

This project is for educational and research purposes only.