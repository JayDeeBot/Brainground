from multiprocessing import Process, Queue
from data_acquisition import DataAquisition
from scan_processing import ScanProcessing
from eeg_interface import EegInterface

def main():
    file_path = "/home/jarred/git/Brainground/BCI/data/1.edf"

    # Create queues for inter-process communication
    data_queue = Queue()
    gui_queue = Queue()  # New queue for GUI communication

    # Define the channels for asymmetry calculation
    selected_channels = ["EEG F3-LE", "EEG F4-LE"]  # Left vs. Right frontal channels
    asymmetry_channels = (0, 1)  # Indices in selected channels list

    # Create DataAquisition and ScanProcessing instances
    data_acquisition = DataAquisition(file_path, data_queue)
    scan_processing = ScanProcessing(data_queue, gui_queue, filter_type='bandpass', low_cut=8, high_cut=12, 
                                     epoch_duration=1, epoch_interval=0.5, moving_avg_epochs=4, 
                                     asymmetry_channels=asymmetry_channels)

    # Start ScanProcessing and GUI in separate processes
    scan_process = Process(target=scan_processing.process_data)
    gui_process = Process(target=EegInterface.run, args=(gui_queue,))

    scan_process.start()
    gui_process.start()

    # Read the EDF file, select channels, and start real-time playback
    data_acquisition.read_edf()
    print(f"✅ Available Channels: {data_acquisition.raw.ch_names}")
    data_acquisition.select_channels(selected_channels)

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
