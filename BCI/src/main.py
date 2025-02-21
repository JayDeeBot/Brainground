from multiprocessing import Process, Queue
from data_acquisition import DataAquisition
from scan_processing import ScanProcessing

def main():
    file_path = "/home/jarred/git/Brainground/BCI/data/1.edf"

    # Create a queue for inter-process communication
    data_queue = Queue()

    # Define the channels for asymmetry calculation
    selected_channels = ["EEG F3-LE", "EEG F4-LE"]  # Left vs. Right frontal channels
    asymmetry_channels = (0, 1)  # Indices in selected channels list

    # Create DataAquisition and ScanProcessing instances
    data_acquisition = DataAquisition(file_path, data_queue)
    scan_processing = ScanProcessing(data_queue, filter_type='bandpass', low_cut=8, high_cut=12, 
                                     epoch_duration=1, epoch_interval=0.5, moving_avg_epochs=4, 
                                     asymmetry_channels=asymmetry_channels)

    # Start ScanProcessing in a separate process
    scan_process = Process(target=scan_processing.process_data)
    scan_process.start()

    # Read the EDF file, select channels, and start real-time playback
    data_acquisition.read_edf()
    
    # Debugging: Print available channels
    print(f"✅ Available Channels: {data_acquisition.raw.ch_names}")

    data_acquisition.select_channels(selected_channels)

    # ✅ **Add a check before proceeding**
    if data_acquisition.selected_data is None:
        print("❌ ERROR: No valid EEG channels were selected! Exiting...")
        scan_process.terminate()  # Stop the processing
        return  # Exit the program safely

    print(f"✅ Expected Data Shape Before Sending: {data_acquisition.selected_data.shape}")

    data_acquisition.play_real_time()

    # Join processes
    scan_process.join()

if __name__ == "__main__":
    main()