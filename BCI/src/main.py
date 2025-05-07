## \file main.py
#  \brief Entry point for running the full BCI system.
#
#  This script launches the EEG GUI in a separate process, waits for user input,
#  then coordinates EEG data acquisition, filtering, epoching, and asymmetry score
#  processing using multiprocessing. It connects the GUI, DataAquisition, and
#  ScanProcessing components into a functional pipeline.

from multiprocessing import Process, Queue
from data_acquisition import DataAquisition
from signal_acquisition import SignalAcquisition
from scan_processing import ScanProcessing
from eeg_interface import EegInterface
import time
from PyQt5.QtWidgets import QApplication

# Map for predefined EEG frequency bands
FREQUENCY_BANDS = {
    "Delta": (0.5, 4),
    "Theta": (4, 8),
    "Alpha": (8, 12),
    "Beta": (13, 30),
    "Gamma": (30, 100)
}

## \brief Runs the PyQt5 GUI in a separate process.
#  \param queue Multiprocessing queue used to receive messages from GUI (e.g., start command).
def run_gui(queue):
    """Runs the GUI in a separate process."""
    app = QApplication([])
    interface = EegInterface(queue)
    interface.show()
    app.exec_()

## \brief Main function that initializes and manages all components of the BCI pipeline.
#
#  This function:
#  - Starts the GUI process
#  - Waits for user input (EEG file, channels, filter settings)
#  - Starts DataAquisition and ScanProcessing as coordinated processes
#  - Loads and plays EEG data in real time
def main():
    data_queue = Queue()
    gui_queue = Queue()

    gui_process = Process(target=run_gui, args=(gui_queue,))
    gui_process.start()

    print("🟢 Waiting for user to start scenario from GUI...")

    while True:
        command = None
        asymmetry_channels = None
        freq_band = None
        file_path = None

        # Wait for a start command
        while command is None:
            try:
                while not gui_queue.empty():
                    message = gui_queue.get()
                    if isinstance(message, dict):
                        command = message.get("command")
                        asymmetry_channels = message.get("asymmetry_channels")
                        freq_band = message.get("frequency_band")
                        if command == "start_file":
                            file_path = message.get("file_path")
                        elif command == "stop":
                            print("🛑 Received stop before starting. Ignoring.")
                            command = None
                        print(f"📨 Received command: {command}")
                        break
            except Exception as e:
                print(f"❌ Error retrieving message from GUI queue: {e}")
            time.sleep(0.1)

        if command is None:
            continue  # wait again

        # Setup frequency band
        low_cut, high_cut = FREQUENCY_BANDS.get(freq_band, (8, 12))
        print(f"🔍 Selected Band: {freq_band} ({low_cut}-{high_cut} Hz)")

        # Start scan processing
        scan_processing = ScanProcessing(
            data_queue,
            gui_queue,
            filter_type='bandpass',
            low_cut=low_cut,
            high_cut=high_cut,
            epoch_duration=1,
            epoch_interval=0.5,
            moving_avg_epochs=4,
            asymmetry_channels=[0, 1],
            selected_channel_names=asymmetry_channels
        )
        scan_process = Process(target=scan_processing.process_data)
        scan_process.start()

        # Start data acquisition based on source
        if command == "start_file":
            print("📁 Starting with EDF file...")
            available_channels = [
                'EEG Fp1-LE', 'EEG F3-LE', 'EEG C3-LE', 'EEG P3-LE', 'EEG O1-LE', 
                'EEG F7-LE', 'EEG T3-LE', 'EEG T5-LE', 'EEG Fz-LE', 'EEG Fp2-LE', 
                'EEG F4-LE', 'EEG C4-LE', 'EEG P4-LE', 'EEG O2-LE', 'EEG F8-LE', 
                'EEG T4-LE', 'EEG T6-LE', 'EEG Cz-LE', 'EEG Pz-LE', 'EEG A2-A1', 
                'EEG 23A-23R', 'EEG 24A-24R'
            ]
            channel_names = (
                available_channels[asymmetry_channels[0]],
                available_channels[asymmetry_channels[1]]
            )
            data_acquisition = DataAquisition(file_path, data_queue)
            data_acquisition.read_edf()
            data_acquisition.select_channels(list(channel_names))

            if data_acquisition.selected_data is None:
                print("❌ ERROR: No valid EEG channels were selected! Skipping...")
                scan_process.terminate()
                continue

            print(f"✅ Playing file data from: {file_path}")
            # Run the acquisition in a separate process so we can stop it cleanly
            acquisition_process = Process(target=data_acquisition.play_real_time)
            acquisition_process.start()

        elif command == "start_device":
            print("📡 Starting with Unicorn device...")
            data_acquisition = SignalAcquisition(data_queue)
            data_acquisition.select_channels(asymmetry_channels)
            acquisition_process = Process(target=data_acquisition.play_real_time)
            acquisition_process.start()
        else:
            continue

        # Wait for stop signal
        while True:
            if not gui_queue.empty():
                msg = gui_queue.get()
                if isinstance(msg, dict) and msg.get("command") == "stop":
                    print("🛑 Stopping current scenario...")
                    acquisition_process.terminate()
                    scan_process.terminate()
                    acquisition_process.join()
                    scan_process.join()
                    print("🔁 Ready to start a new scenario.")
                    break
            time.sleep(0.1)


if __name__ == "__main__":
    main()