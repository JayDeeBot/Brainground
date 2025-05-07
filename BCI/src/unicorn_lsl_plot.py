import numpy as np
import matplotlib.pyplot as plt
from pylsl import StreamInlet, resolve_streams
import matplotlib.animation as animation

# --- Unicorn EEG Settings ---
num_channels = 8            # Unicorn Hybrid Black has 8 EEG channels
sampling_rate = 250         # Hz
window_size = sampling_rate # 1 second window (250 samples)

# --- Connect to LSL EEG Stream ---
print("Looking for a Unicorn EEG stream...")
streams = resolve_streams()
eeg_streams = [s for s in streams if s.name() == 'unicorn' or s.type() == 'Data']
if not eeg_streams:
    raise RuntimeError("No stream found. Make sure the Unicorn LSL streamer is running.")
inlet = StreamInlet(eeg_streams[0])
print(f"Connected to stream: {eeg_streams[0].name()}")

# --- Initialize data buffer ---
data_buffer = np.zeros((num_channels, window_size))

# --- Matplotlib plot setup ---
fig, axs = plt.subplots(num_channels, 1, figsize=(12, 8), sharex=True)
lines = []

for i, ax in enumerate(axs):
    line, = ax.plot(data_buffer[i], lw=1)
    ax.set_ylim(-1e6, 1e6)  # Adjust range if needed
    ax.set_ylabel(f'Ch {i+1}')
    lines.append(line)
axs[-1].set_xlabel("Time (samples)")
fig.suptitle("Unicorn EEG Live Stream", fontsize=16)

# --- Animation update function ---
def update(frame):
    global data_buffer
    sample, _ = inlet.pull_sample(timeout=0.1)  # 100 ms timeout
    if sample:
        print(f"Sample received: {sample[:8]}")  # print just 8 channels for brevity
        data_buffer = np.roll(data_buffer, -1, axis=1)
        data_buffer[:, -1] = sample[:8]  # Only use first 8 channels for EEG
        for i in range(8):
            lines[i].set_ydata(data_buffer[i])
    else:
        print("No sample received")
    return lines

# --- Start animation ---
ani = animation.FuncAnimation(fig, update, interval=1000 * (1 / sampling_rate), blit=True)
plt.tight_layout()
plt.show()
