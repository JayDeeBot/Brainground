from data_acquisition import DataAquisition

def main():
    file_path = "/home/jarred/git/Brainground/BCI/data/1.edf"  # Update with your actual file
    data_acquisition = DataAquisition(file_path)

    # Load the EDF file
    data_acquisition.read_edf()

    # Play the EEG data in real-time with visualization
    data_acquisition.play_real_time(num_channels=3)  # Adjust number of channels to display

if __name__ == "__main__":
    main()