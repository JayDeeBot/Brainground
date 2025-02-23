import numpy as np
import scipy.signal
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

class ScanProcessing:
    def __init__(self, queue, filter_type='bandpass', low_cut=1, high_cut=40, sampling_rate=256, 
                 epoch_duration=1, epoch_interval=0.5, moving_avg_epochs=4, asymmetry_channels=None):
        self.queue = queue  
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
        """Applies temporal filtering (bandpass, high-pass, or low-pass)"""
        nyquist = 0.5 * self.sampling_rate
        filter_order = 4  

        if len(data.shape) == 1:
            data = data.reshape(1, -1)  # Ensure 2D shape [channels, samples]

        if data.shape[1] < self.min_samples:
            print(f"Not enough data for filtering ({data.shape[1]} samples). Waiting for more...")
            return data

        if self.filter_type == 'bandpass':
            b, a = scipy.signal.butter(filter_order, [self.low_cut / nyquist, self.high_cut / nyquist], btype='band')
        elif self.filter_type == 'lowpass':
            b, a = scipy.signal.butter(filter_order, self.high_cut / nyquist, btype='low')
        elif self.filter_type == 'highpass':
            b, a = scipy.signal.butter(filter_order, self.low_cut / nyquist, btype='high')
        else:
            raise ValueError("Invalid filter type. Choose 'bandpass', 'lowpass', or 'highpass'.")

        return scipy.signal.filtfilt(b, a, data, axis=1)

    def extract_epochs(self, filtered_data):
        """Splits continuous filtered EEG data into overlapping epochs."""
        num_samples = filtered_data.shape[1]
        samples_per_epoch = int(self.epoch_duration * self.sampling_rate)
        stride = int(self.epoch_interval * self.sampling_rate)

        if filtered_data.shape[0] < 2:  # Ensure at least two channels
            print("❌ Error: Not enough EEG channels detected before epoching!")
            print(f"Filtered Data Shape: {filtered_data.shape}")
            return []

        epochs = []
        for start in range(0, num_samples - samples_per_epoch + 1, stride):
            epoch = filtered_data[:, start:start + samples_per_epoch]  # Keep all channels
            epochs.append(epoch)

        epochs = np.array(epochs)  # Convert to numpy array
        print(f"✅ Extracted Epochs Shape: {epochs.shape} (Epochs, Channels, Samples)")
        return epochs

        return epochs

    def compute_moving_average(self, new_epochs):
        """Computes the moving average of the last N epochs"""
        self.epoch_history.extend(new_epochs)

        if len(self.epoch_history) > self.moving_avg_epochs:
            self.epoch_history = self.epoch_history[-self.moving_avg_epochs:]

        if len(self.epoch_history) >= self.moving_avg_epochs:
            avg_epoch = np.mean(self.epoch_history, axis=0)
            print(f"Moving Average Epoch: {avg_epoch[:, :5]} ... {avg_epoch[:, -5:]}")

    def asymmetry_dsp(self, epochs):
        """Computes the asymmetry score based on selected EEG channels"""
        
        print(f"Asymmetry DSP - Epochs Shape: {epochs.shape}")  # ✅ Debugging output

        if epochs.shape[1] < 2:
            print("❌ Not enough channels for asymmetry calculation. Need at least 2.")
            return

        # Ensure we are selecting the correct indices
        left_channel_idx, right_channel_idx = self.asymmetry_channels
        if left_channel_idx >= epochs.shape[1] or right_channel_idx >= epochs.shape[1]:
            print(f"❌ Invalid channel indices: {left_channel_idx}, {right_channel_idx}. Skipping.")
            return

        left_channel_data = epochs[:, left_channel_idx, :]
        right_channel_data = epochs[:, right_channel_idx, :]

        # Compute power for both channels
        left_power = np.mean(left_channel_data**2, axis=1)
        right_power = np.mean(right_channel_data**2, axis=1)

        # Compute asymmetry score (normalize between 0-100)
        asymmetry_ratio = np.abs(left_power - right_power) / (left_power + right_power + 1e-10)
        asymmetry_score = (1 - asymmetry_ratio) * 100

        print(f"🧠 Asymmetry Score: {asymmetry_score}")  # ✅ Expected numerical output


    def process_data(self):
        """Receives, filters, epochs, and computes moving average + asymmetry DSP"""
        print(f"ScanProcessing started with {self.filter_type} filter: {self.low_cut}-{self.high_cut} Hz")
        print(f"Epoching: {self.epoch_duration}s epochs every {self.epoch_interval}s")
        print(f"Moving Average over last {self.moving_avg_epochs} epochs")
        print(f"Asymmetry DSP enabled on channels: {self.asymmetry_channels}")

        min_required_samples = 30  # Ensure enough data before applying the filter

        while True:
            new_data = self.queue.get()

            # ✅ Debugging: Check the shape of incoming data
            print(f"🔍 Received Data Shape: {new_data.shape}")

            # ✅ Ensure at least 2 channels before processing
            if new_data.shape[0] < 2:
                print("❌ Error: Not enough EEG channels detected before processing!")
                continue  # Skip this batch

            # Ensure new_data is 2D [channels, samples]
            if len(new_data.shape) == 1:
                new_data = new_data.reshape(1, -1)  # Convert (samples,) → (1, samples)

            self.buffer.append(new_data)

            # Ensure all buffers have the same number of channels before stacking
            buffer_shapes = {arr.shape[0] for arr in self.buffer}
            if len(buffer_shapes) > 1:
                print(f"⚠️ WARNING: Mismatched buffer shapes {buffer_shapes}. Adjusting dimensions.")
                self.buffer = [arr if arr.shape[0] == max(buffer_shapes) 
                            else arr.reshape(max(buffer_shapes), -1) 
                            for arr in self.buffer]

            # Stack buffer contents
            try:
                data_array = np.hstack(self.buffer)  # Combine into one large array
            except ValueError as e:
                print(f"❌ ERROR: Buffer shape mismatch. Buffer contents: {[arr.shape for arr in self.buffer]}")
                raise e

            # ✅ Ensure enough samples before applying the filter
            if data_array.shape[1] < min_required_samples:
                print(f"⏳ Waiting for more data... Current size: {data_array.shape[1]} / {min_required_samples}")
                continue  # Skip processing until enough samples accumulate

            # Apply filtering once enough data exists
            filtered_data = self.apply_filter(data_array)

            # Extract epochs
            epochs = self.extract_epochs(filtered_data)

            # ✅ Ensure epochs are not empty before proceeding
            if epochs.size > 0:
                print(f"✅ Extracted Epochs Shape: {epochs.shape}")

                # Compute moving average
                self.compute_moving_average(epochs)

                # ✅ Ensure at least 2 channels before asymmetry processing
                if epochs.shape[1] >= 2:
                    self.asymmetry_dsp(epochs)
                else:
                    print("⚠️ Skipping asymmetry calculation due to insufficient channels.")

            else:
                print("⚠️ No valid epochs extracted. Skipping processing.")

            # Keep only the latest epoch-sized buffer
            self.buffer = [data_array[:, -self.epoch_samples:]]  # Keep the most recent window