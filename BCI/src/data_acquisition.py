import mne
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class DataAquisition:
    def __init__(self, file_path, queue, window_size=5):
        self.file_path = file_path
        self.raw = None
        self.sampling_rate = None
        self.window_size = window_size  # Time window in seconds for scrolling plot
        self.queue = queue  # Queue for sending data to ScanProcessing
        self.fig, self.ax = None, None
        self.lines = []
        self.data_buffer = None
        self.time_buffer = None
        self.selected_channels = None
        self.selected_data = None

    def read_edf(self):
        """Reads EEG data from an EDF file"""
        try:
            self.raw = mne.io.read_raw_edf(self.file_path, preload=True)
            self.sampling_rate = int(self.raw.info['sfreq'])
            print(f"EDF file '{self.file_path}' loaded successfully.")
            print(f"Sampling Rate: {self.sampling_rate} Hz")
            print(f"Available Channels: {self.raw.ch_names}")
            return self.raw
        except Exception as e:
            print(f"Error loading EDF file: {e}")
            return None

    def select_channels(self, channel_names):
        """Selects specific EEG channels for playback"""
        if self.raw is None:
            print("No EDF file loaded. Call read_edf() first.")
            return
        
        available_channels = self.raw.ch_names
        self.selected_channels = [ch for ch in channel_names if ch in available_channels]

        if not self.selected_channels:
            print("Error: None of the selected channels exist in this EDF file.")
            return

        self.raw = self.raw.pick_channels(self.selected_channels)
        self.selected_data, times = self.raw.get_data(return_times=True)

        self.time_buffer = np.linspace(0, self.window_size, int(self.sampling_rate * self.window_size))

        print(f"Selected Channels: {self.selected_channels}")
        print(f"Data Shape: {self.selected_data.shape} (Channels, Samples)")

    def setup_plot(self):
        """Initializes the real-time EEG plot"""
        num_channels = len(self.selected_channels)
        self.fig, self.ax = plt.subplots(num_channels, 1, figsize=(10, 6), sharex=True)

        if num_channels == 1:
            self.ax = [self.ax]

        for i in range(num_channels):
            line, = self.ax[i].plot(self.time_buffer, np.zeros_like(self.time_buffer), lw=1)
            self.lines.append(line)
            self.ax[i].set_xlim(0, self.window_size)
            self.ax[i].set_ylim(-50e-6, 50e-6)
            self.ax[i].set_ylabel(f"{self.selected_channels[i]}")

        self.ax[-1].set_xlabel("Time (s)")
        plt.suptitle("Real-Time EEG Streaming")

    def update_plot(self, frame):
        """Updates the EEG plot with new data"""
        for i, line in enumerate(self.lines):
            line.set_data(self.time_buffer, self.data_buffer[i])
        return self.lines

    def play_real_time(self):
        """Simulates real-time EEG scanning with visualization and sends data to ScanProcessing"""
        if self.raw is None or self.selected_data is None:
            print("No EDF file loaded or no channels selected. Call read_edf() and select_channels() first.")
            return

        num_channels, num_samples = self.selected_data.shape
        buffer_size = int(self.sampling_rate * self.window_size)
        self.data_buffer = np.zeros((num_channels, buffer_size))

        self.setup_plot()

        def data_generator():
            for i in range(num_samples):
                time.sleep(1 / self.sampling_rate)

                self.data_buffer = np.roll(self.data_buffer, -1, axis=1)
                new_values = self.selected_data[:, i]
                self.data_buffer[:, -1] = new_values

                # Send new data section to ScanProcessing
                self.queue.put(self.selected_data[:, i].reshape(-1, 1))  # Ensures a 2D array

                yield i

        ani = animation.FuncAnimation(self.fig, self.update_plot, frames=data_generator, interval=1000/self.sampling_rate, blit=True)
        plt.show()