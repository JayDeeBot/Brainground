import numpy as np
import scipy.signal
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

class ScanProcessing:
    def __init__(self, queue, gui_queue, filter_type='bandpass', low_cut=10, high_cut=13, sampling_rate=256, 
                 epoch_duration=1, epoch_interval=0.5, moving_avg_epochs=4, asymmetry_channels=None):
        self.queue = queue  
        self.gui_queue = gui_queue  # Queue for sending data to GUI
        self.filter_type = filter_type  
        self.low_cut = low_cut
        self.high_cut = high_cut
        self.sampling_rate = sampling_rate  
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

    def compute_asymmetry_score(self, psd_data):
        """Computes the upper alpha asymmetry score using the log formula and maps it to 0-100."""
        if self.asymmetry_channels is None or len(self.asymmetry_channels) != 2:
            print("❌ Invalid asymmetry channel configuration!")
            return

        left_idx, right_idx = self.asymmetry_channels

        # Ensure indices are integers
        if not isinstance(left_idx, int) or not isinstance(right_idx, int):
            print(f"❌ ERROR: Asymmetry channel indices should be integers, got: {self.asymmetry_channels}")
            return

        if left_idx >= psd_data.shape[1] or right_idx >= psd_data.shape[1]:
            print(f"❌ ERROR: Invalid channel indices: {left_idx}, {right_idx}. Skipping computation.")
            return

        left_psd = psd_data[:, left_idx]
        right_psd = psd_data[:, right_idx]

        # Compute FAA Score (Logarithmic Difference)
        asymmetry_score = np.log10(right_psd + 1e-10) - np.log10(left_psd + 1e-10)  # Avoid log(0)
        avg_score = np.mean(asymmetry_score)

        # Apply Mapping Function
        mapped_score = self.map_faa_score(avg_score)

        # Debugging Output
        print(f"🧠 Raw FAA Score: {avg_score} → Mapped Score: {mapped_score}")

        # Send Mapped Score to GUI
        self.gui_queue.put({"score": mapped_score})

    def map_faa_score(self, faa_score):
        """Maps the FAA score (-0.1 to 0.1) to a range of 0-100."""
        if faa_score < -0.02:
            return max(0, 25 * (faa_score + 0.02) / (-0.08))  # Map -0.1 to 0.02 → 0 to 25
        elif -0.02 <= faa_score <= 0.02:
            return 25 + (faa_score + 0.02) * (50 / 0.04)  # Map -0.02 to 0.02 → 25 to 75
        else:
            return min(100, 75 + (faa_score - 0.02) * (25 / 0.08))  # Map 0.02 to 0.1 → 75 to 100

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
            data_array = np.hstack(self.buffer)  # Stack data horizontally

            if data_array.shape[1] < self.epoch_samples:
                print(f"⏳ Waiting for more data... Current size: {data_array.shape[1]} / {self.epoch_samples}")
                continue

            print(f"✅ Processing Data - Shape: {data_array.shape}")  # Debugging
            filtered_data = self.apply_filter(data_array)
            epochs = self.extract_epochs(filtered_data)

            if epochs.size > 0:
                psd_data = self.compute_psd_welch(epochs)
                self.compute_asymmetry_score(psd_data)

            # Remove old samples to allow continuous updates
            self.buffer = [data_array[:, -self.epoch_samples:]]