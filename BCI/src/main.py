from multiprocessing import Process, Queue
from data_acquisition import DataAquisition
from scan_processing import ScanProcessing
from eeg_interface import EegInterface
import time
from PyQt5.QtWidgets import QApplication

def run_gui(queue):
    """Runs the GUI in a separate process."""
    app = QApplication([])
    interface = EegInterface(queue)
    interface.show()
    app.exec_()

def main():
    # Create queues for inter-process communication
    data_queue = Queue()
    gui_queue = Queue()  # Queue for GUI communication

    # Start GUI in a separate process
    gui_process = Process(target=run_gui, args=(gui_queue,))
    gui_process.start()
    
    print("🟢 Waiting for user to select an EEG file, channels, and bandpass filter range...")
    file_path = None
    asymmetry_channels = None
    low_cut = None
    high_cut = None
    available_channels = [
        'EEG Fp1-LE', 'EEG F3-LE', 'EEG C3-LE', 'EEG P3-LE', 'EEG O1-LE', 
        'EEG F7-LE', 'EEG T3-LE', 'EEG T5-LE', 'EEG Fz-LE', 'EEG Fp2-LE', 
        'EEG F4-LE', 'EEG C4-LE', 'EEG P4-LE', 'EEG O2-LE', 'EEG F8-LE', 
        'EEG T4-LE', 'EEG T6-LE', 'EEG Cz-LE', 'EEG Pz-LE', 'EEG A2-A1', 
        'EEG 23A-23R', 'EEG 24A-24R'
    ]
    
    # Wait for valid input from the GUI
    while file_path is None or asymmetry_channels is None or low_cut is None or high_cut is None:
        try:
            while not gui_queue.empty():
                message = gui_queue.get()
                if isinstance(message, dict):
                    if message.get("command") == "start":
                        file_path = message.get("file_path")
                        channel_indices = message.get("asymmetry_channels")  # Indices from GUI
                        low_cut = message.get("low_cut")
                        high_cut = message.get("high_cut")

                        if channel_indices and len(channel_indices) == 2:
                            # Convert indices to channel names
                            asymmetry_channels = (
                                available_channels[channel_indices[0]],  # Convert index to name
                                available_channels[channel_indices[1]]   # Convert index to name
                            )

                        print(f"✅ Received start command with file: {file_path}, channels: {asymmetry_channels}, bandpass: {low_cut}-{high_cut} Hz")
                        break  # Exit loop when valid file path and channels are received
        except Exception as e:
            print(f"❌ Error retrieving message from GUI queue: {e}")
        
    print(f"✅ Selected EEG File: {file_path}")
    print(f"✅ Selected Asymmetry Channels: {asymmetry_channels}")
    print(f"✅ Selected Bandpass Filter: {low_cut}-{high_cut} Hz")
    
    # Create DataAquisition and ScanProcessing instances
    data_acquisition = DataAquisition(file_path, data_queue)

    # Convert selected channel names to their index in the full EEG list
    selected_channel_indices = [
        available_channels.index(asymmetry_channels[0]), 
        available_channels.index(asymmetry_channels[1])
    ]

    # Pass these indices to `ScanProcessing`
    scan_processing = ScanProcessing(
        data_queue, 
        gui_queue, 
        filter_type='bandpass', 
        low_cut=low_cut, 
        high_cut=high_cut, 
        epoch_duration=1, 
        epoch_interval=0.5, 
        moving_avg_epochs=4, 
        asymmetry_channels=[0, 1],  # ✅ Adjusted to be relative to the extracted PSD data
        selected_channel_names=asymmetry_channels
    )

    # Start ScanProcessing in a separate process
    scan_process = Process(target=scan_processing.process_data)
    scan_process.start()

    # Read the EDF file, select channels, and start real-time playback
    data_acquisition.read_edf()
    print(f"✅ Available Channels: {data_acquisition.raw.ch_names}")
    data_acquisition.select_channels([asymmetry_channels[0], asymmetry_channels[1]])

    if data_acquisition.selected_data is None:
        print("❌ ERROR: No valid EEG channels were selected! Exiting...")
        scan_process.terminate()
        gui_process.terminate()
        return

    print(f"✅ Expected Data Shape Before Sending: {data_acquisition.selected_data.shape}")
    data_acquisition.play_real_time()

    # Join processes
    scan_process.join()
    gui_process.join()

if __name__ == "__main__":
    main()
