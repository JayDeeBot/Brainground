import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from pylsl import StreamInlet, resolve_streams
import time

## \class SignalAcquisition
#  \brief Acquires real-time EEG data from the Unicorn headset via LSL, visualizes it, and sends it to ScanProcessing.
#
#  This class connects to the Unicorn Hybrid Black EEG headset using the Lab Streaming Layer (LSL), reads EEG signals,
#  displays them in real time using Matplotlib, and sends sample-wise EEG data to the ScanProcessing class via a multiprocessing queue.
class SignalAcquisition:
    def __init__(self, queue, window_size=5):
        self.queue = queue
        self.window_size = window_size  # seconds
        self.sampling_rate = 250  # Unicorn Hybrid Black fixed at 250 Hz
        self.num_channels = 8

        self.inlet = None
        self.data_buffer = np.zeros((self.num_channels, self.sampling_rate * self.window_size))
        self.time_buffer = np.linspace(0, self.window_size, self.sampling_rate * self.window_size)

        self.fig, self.ax = None, None
        self.lines = []

    def connect_stream(self):
        print("Looking for a Unicorn EEG stream...")
        streams = resolve_streams()
        eeg_streams = [s for s in streams if s.name() == 'unicorn' or s.type() == 'Data']
        if not eeg_streams:
            raise RuntimeError("No stream found. Make sure the Unicorn LSL streamer is running.")
        self.inlet = StreamInlet(eeg_streams[0])
        print(f"Connected to stream: {eeg_streams[0].name()}")

    def setup_plot(self):
        self.fig, self.ax = plt.subplots(self.num_channels, 1, figsize=(12, 8), sharex=True)
        if self.num_channels == 1:
            self.ax = [self.ax]

        for i in range(self.num_channels):
            line, = self.ax[i].plot(self.time_buffer, np.zeros_like(self.time_buffer), lw=1)
            self.lines.append(line)
            self.ax[i].set_ylim(-1e6, 1e6)
            self.ax[i].set_ylabel(f"Ch {i+1}")

        self.ax[-1].set_xlabel("Time (s)")
        plt.suptitle("Real-Time Unicorn EEG Streaming")

    def update_plot(self, frame):
        sample, _ = self.inlet.pull_sample(timeout=0.1)
        if sample:
            selected_sample = np.array([sample[i] for i in self.selected_channels])
            normalized = (selected_sample - np.mean(selected_sample)) / 1e5
            self.data_buffer = np.roll(self.data_buffer, -1, axis=1)
            self.data_buffer[:, -1] = normalized

            self.queue.put(normalized.reshape(-1, 1))

            for i in range(self.num_channels):
                self.lines[i].set_ydata(self.data_buffer[i])

        return self.lines

    def play_real_time(self):
        self.connect_stream()
        self.setup_plot()

        ani = animation.FuncAnimation(
            self.fig, self.update_plot,
            interval=1000 / self.sampling_rate,
            blit=False,
            cache_frame_data=False
        )
        plt.tight_layout()
        plt.show()

    def select_channels(self, channels):
        """Specify which EEG channels to use for streaming and processing."""
        self.selected_channels = channels
        self.num_channels = len(channels)
        buffer_length = self.sampling_rate * self.window_size
        self.data_buffer = np.zeros((self.num_channels, buffer_length))
        self.time_buffer = np.linspace(0, self.window_size, buffer_length)
