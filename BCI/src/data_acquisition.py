import mne
import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

class DataAquisition:
    def __init__(self, file_path, window_size=5):
        self.file_path = file_path
        self.raw = None
        self.sampling_rate = None
        self.window_size = window_size  # Time window in seconds for scrolling plot
        self.fig, self.ax = None, None  # Matplotlib figure and axes
        self.lines = []  # List to hold line plots
        self.data_buffer = None  # Stores last few seconds of data
        self.time_buffer = None  # Stores time stamps for last few seconds

    def read_edf(self):
        """Reads EEG data from an EDF file"""
        try:
            self.raw = mne.io.read_raw_edf(self.file_path, preload=True)
            self.sampling_rate = int(self.raw.info['sfreq'])  # Get sample rate
            print(f"EDF file '{self.file_path}' loaded successfully.")
            print(f"Sampling Rate: {self.sampling_rate} Hz")
            return self.raw
        except Exception as e:
            print(f"Error loading EDF file: {e}")
            return None

    def get_eeg_data(self):
        """Extracts EEG data as a NumPy array"""
        if self.raw is None:
            print("No EDF file loaded. Call read_edf() first.")
            return None

        eeg_channels = self.raw.pick_types(eeg=True)  # Select EEG channels
        data, times = eeg_channels.get_data(return_times=True)  # Get EEG signals
        return data, times

    def setup_plot(self, num_channels):
        """Initializes the real-time EEG plot"""
        self.fig, self.ax = plt.subplots(num_channels, 1, figsize=(10, 6), sharex=True)
        if num_channels == 1:
            self.ax = [self.ax]  # Ensure ax is a list even for one channel

        for i in range(num_channels):
            line, = self.ax[i].plot([], [], lw=1)
            self.lines.append(line)
            self.ax[i].set_xlim(0, self.window_size)
            self.ax[i].set_ylim(-50e-6, 50e-6)  # Adjust Y-limits for EEG scale
            self.ax[i].set_ylabel(f"Ch {i+1}")

        self.ax[-1].set_xlabel("Time (s)")
        plt.suptitle("Real-Time EEG Streaming")

    def update_plot(self, frame):
        """Updates the EEG plot with new data"""
        for i, line in enumerate(self.lines):
            line.set_data(self.time_buffer, self.data_buffer[i])
        return self.lines

    def play_real_time(self, num_channels=3):
        """Simulates real-time EEG scanning with visualization"""
        if self.raw is None:
            print("No EDF file loaded. Call read_edf() first.")
            return

        data, times = self.get_eeg_data()
        num_samples = data.shape[1]

        self.data_buffer = np.zeros((num_channels, self.sampling_rate * self.window_size))
        self.time_buffer = np.linspace(0, self.window_size, self.sampling_rate * self.window_size)

        self.setup_plot(num_channels)

        def data_generator():
            """Yields real-time EEG data sample by sample"""
            for i in range(num_samples):
                time.sleep(1 / self.sampling_rate)  # Simulate real-time delay

                # Shift data left and add new values
                self.data_buffer = np.roll(self.data_buffer, -1, axis=1)
                self.data_buffer[:, -1] = data[:num_channels, i]  # Update with new EEG values

                yield i  # Yield index for animation update

        ani = animation.FuncAnimation(self.fig, self.update_plot, frames=data_generator, interval=1000/self.sampling_rate, blit=True)
        plt.show()