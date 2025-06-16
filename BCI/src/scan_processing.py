import numpy as np
import scipy.signal
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

## \class ScanProcessing
#  \brief Processes real-time EEG data including filtering, epoching, and asymmetry score calculation.
#
#  This class receives EEG data from a queue, applies signal processing (bandpass filtering),
#  segments the data into overlapping epochs, computes the power spectral density (PSD) using Welch's method,
#  calculates an asymmetry score (based on FAA), and sends the result to a GUI queue.
class ScanProcessing:
    ## \brief Constructor for ScanProcessing.
    #  \param queue Input queue for receiving EEG data (from DataAquisition).
    #  \param gui_queue Output queue for sending score data to the GUI.
    #  \param filter_type Type of filter to apply (e.g., 'bandpass').
    #  \param low_cut Low cutoff frequency for bandpass filter.
    #  \param high_cut High cutoff frequency for bandpass filter.
    #  \param sampling_rate Sampling frequency of EEG data.
    #  \param epoch_duration Duration of each epoch (seconds).
    #  \param epoch_interval Time interval between epochs (seconds).
    #  \param moving_avg_epochs Number of epochs to average for smoothing.
    #  \param asymmetry_channels Tuple of two EEG channel indices to use for asymmetry score.
    #  \param selected_channel_names Optional list of channel names or indices being processed.
    def __init__(self, queue, gui_queue, filter_type='bandpass', low_cut=10, high_cut=13, sampling_rate=256, 
                 epoch_duration=1, epoch_interval=0.5, moving_avg_epochs=4, asymmetry_channels=None, selected_channel_names=[0, 1]):
        self.queue = queue  
        self.gui_queue = gui_queue  # Queue for sending data to GUI
        self.filter_type = filter_type  
        self.low_cut = low_cut
        self.high_cut = high_cut
        self.sampling_rate = sampling_rate
        self.selected_channel_names = selected_channel_names  
        self.buffer = []  
        self.min_samples = 27  

        # Epoching settings
        self.epoch_duration = epoch_duration
        self.epoch_interval = epoch_interval
        self.epoch_samples = int(self.sampling_rate * self.epoch_duration)
        self.epoch_step = int(self.sampling_rate * self.epoch_interval)

        # Moving epoch average settings
        self.moving_avg_epochs = moving_avg_epochs
        self.epoch_history = []

        # Asymmetry DSP settings
        self.asymmetry_channels = asymmetry_channels  

    ## \brief Applies a bandpass Butterworth filter to EEG data.
    #  \param data Raw EEG signal (2D array: channels x samples).
    #  \return Filtered EEG data.
    def apply_filter(self, data):
        """Applies a bandpass filter for upper alpha waves (10-13 Hz)."""
        nyquist = 0.5 * self.sampling_rate
        filter_order = 4  

        if len(data.shape) == 1:
            data = data.reshape(1, -1)  # Ensure 2D shape [channels, samples]

        if data.shape[1] < self.min_samples:
            print(f"Not enough data for filtering ({data.shape[1]} samples). Waiting for more...")
            return data

        b, a = scipy.signal.butter(filter_order, [self.low_cut / nyquist, self.high_cut / nyquist], btype='band')
        return scipy.signal.filtfilt(b, a, data, axis=1)

    ## \brief Splits filtered EEG signal into overlapping epochs.
    #  \param filtered_data Bandpass filtered EEG signal (channels x samples).
    #  \return 3D NumPy array of epochs: (epochs, channels, samples).
    def extract_epochs(self, filtered_data):
        """Splits continuous filtered EEG data into overlapping epochs."""
        num_samples = filtered_data.shape[1]
        stride = self.epoch_step

        epochs = []
        for start in range(0, num_samples - self.epoch_samples + 1, stride):
            epoch = filtered_data[:, start:start + self.epoch_samples]
            epochs.append(epoch)

        epochs = np.array(epochs)
        print(f"✅ Extracted Epochs Shape: {epochs.shape} (Epochs, Channels, Samples)")
        return epochs

    ## \brief Computes power spectral density (PSD) using Welch’s method.
    #  \param epochs 3D array of EEG epochs (epochs x channels x samples).
    #  \return 2D NumPy array of PSD values: (epochs x channels).
    def compute_psd_welch(self, epochs):
        """Computes the Power Spectral Density (PSD) using Welch's method."""
        psd_list = []
        freqs, _ = scipy.signal.welch(epochs[0, 0, :], fs=self.sampling_rate, nperseg=self.epoch_samples)
        upper_alpha_idx = np.where((freqs >= self.low_cut) & (freqs <= self.high_cut))
        
        for epoch in epochs:
            psd_epoch = []
            for channel in epoch:
                f, psd = scipy.signal.welch(channel, fs=self.sampling_rate, nperseg=self.epoch_samples)
                psd_epoch.append(np.mean(psd[upper_alpha_idx]))
            psd_list.append(psd_epoch)
        
        return np.array(psd_list)  # Shape: (epochs, channels)

    ## \brief Computes the FAA-based asymmetry score from PSD data and sends result to GUI.
    #  \param psd_data PSD values per epoch (2D array: epochs x channels).
    def compute_asymmetry_score(self, psd_data):
        """Computes the upper alpha asymmetry score using the log formula and maps it to 0-100."""
        if self.asymmetry_channels is None or len(self.asymmetry_channels) != 2:
            print("❌ Invalid asymmetry channel configuration!")
            return

        left_idx, right_idx = 0, 1

        if psd_data.shape[1] < 2:
            print(f"❌ ERROR: PSD data does not have enough channels ({psd_data.shape[1]} channels). Skipping computation.")
            return

        left_psd = psd_data[:, left_idx]
        right_psd = psd_data[:, right_idx]

        asymmetry_score = np.log10(left_psd + 1e-10) - np.log10(right_psd + 1e-10)
        avg_score = np.mean(asymmetry_score)

        mapped_score = self.map_faa_score(avg_score)

        print(f"🧠 Raw FAA Score: {avg_score} → Mapped Score: {mapped_score}")

        self.gui_queue.put({"score": mapped_score})

        try:
            # with open("/home/jarred/git/Brainground/BCI/score_output.txt", "w") as f: # Linux
            with open(r"D:\Brainground\git\Brainground\BCI\score_output.txt", "w") as f: # Windows
                f.write(str(mapped_score))
        except Exception as e:
            print(f"❌ Failed to write score to file: {e}")

    ## \brief Maps the FAA asymmetry score from range (-0.1 to 0.1) into [0, 100] scale.
    #  \param faa_score Raw FAA score (log difference).
    #  \return Normalized score (0 to 100).
    def map_faa_score(self, faa_score):
        """Maps the FAA score (-0.1 to 0.1) to a range of 0-100."""
        if faa_score < -0.02:
            return max(0, 25 * (faa_score + 0.02) / (-0.08))
        elif -0.02 <= faa_score <= 0.02:
            return 25 + (faa_score + 0.02) * (50 / 0.04)
        else:
            return min(100, 75 + (faa_score - 0.02) * (25 / 0.08))

    ## \brief Main processing loop that handles streaming EEG data end-to-end.
    #
    #  This method continuously receives new data, applies filtering, epoching,
    #  computes the PSD and asymmetry score, and sends the result to the GUI.
    def process_data(self):
        """Receives, filters, epochs, computes PSD and asymmetry score in real-time."""
        print(f"ScanProcessing started with {self.filter_type} filter: {self.low_cut}-{self.high_cut} Hz")
        print(f"Epoching: {self.epoch_duration}s epochs every {self.epoch_interval}s")
        print(f"Asymmetry DSP enabled on channels: {self.asymmetry_channels}")

        while True:
            new_data = self.queue.get()
            print(f"🔍 Received New Data - Shape: {new_data.shape}")  # Debugging

            if new_data.shape[0] < 2:
                print("❌ Error: Not enough EEG channels detected before processing!")
                continue

            self.buffer.append(new_data)
            data_array = np.hstack(self.buffer)

            if data_array.shape[1] > self.epoch_samples * 10:
                data_array = data_array[:, -self.epoch_samples * 10:]

            if data_array.shape[1] < self.epoch_samples:
                print(f"⏳ Waiting for more data... Current size: {data_array.shape[1]} / {self.epoch_samples}")
                continue

            print(f"✅ Processing Data - Shape: {data_array.shape}")  # Debugging
            filtered_data = self.apply_filter(data_array)
            epochs = self.extract_epochs(filtered_data)

            if epochs.size > 0:
                psd_data = self.compute_psd_welch(epochs)
                self.compute_asymmetry_score(psd_data)

            self.buffer = [data_array[:, -self.epoch_samples:]]
