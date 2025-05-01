# Brainground: Closed-Loop Neurofeedback BCI

Brainground is a capstone project demonstrating a functional closed-loop Brain-Computer Interface (BCI) that uses EEG signal processing and Virtual Reality (VR) feedback for emotional state regulation. The system monitors upper-alpha asymmetry in EEG signals and provides dynamic visual feedback in a VR environment to support anxiety and depression management through neurofeedback.

## Features

- EEG data acquisition from `.edf` files (simulated real-time)
- Signal processing with bandpass filtering and Welch’s PSD
- Frontal Alpha Asymmetry (FAA) score calculation (F3–F4)
- Asymmetry mapping to 0–100 for user-friendly interpretation
- Real-time feedback in a Panda3D-rendered VR environment
- PyQt GUI for EEG config, FAA display, and VR interaction
- Modular multiprocessing pipeline for scalable real-time performance

## Installation

### Dependencies

- Python 3.10+
- MNE
- SciPy
- NumPy
- PyQt5
- Panda3D
- Matplotlib

Install dependencies with pip:

```bash
pip install mne scipy numpy pyqt5 panda3d matplotlib
```

## Running the System

1. Clone the repository:
```bash
git clone https://github.com/JayDeeBot/Brainground.git
cd Brainground
```

2. Launch the GUI:
```bash
python BCI/src/main_gui.py
```

3. Load an `.edf` file and configure EEG channels and filters.

4. Press play to simulate real-time EEG playback and view FAA scores.

5. Launch the VR environment from the GUI to activate neurofeedback lighting.

## System Architecture

```
[EDF File / EEG Device]
         ↓
  [Data Acquisition] → [Scan Processing] → [GUI + VR World]
```

- **DataAcquisition:** Loads `.edf` file, simulates playback
- **ScanProcessing:** Applies filters, epochs, computes PSD & FAA
- **GUI:** Displays score and interacts with the VR world
- **VR:** Panda3D-based world changes lighting based on FAA

## Future Work

- Live EEG headset support (Muse, OpenBCI)
- Emotional state ground truth validation
- Alternate feedback methods (sound, haptics)
- Testing other EEG bands (theta, delta, beta)
- Deployment on high-performance VR platforms

## Repository

Source code: [https://github.com/JayDeeBot/Brainground](https://github.com/JayDeeBot/Brainground)

For access or inquiries: jarred.g.deluca@student.uts.edu.au

## License

This project is developed as part of UTS Engineering Capstone 2025.