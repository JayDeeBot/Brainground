#ifndef DATA_ACQUISITION_H
#define DATA_ACQUISITION_H

#include <vector>
#include <string>

struct EEGData {
    std::vector<std::vector<double>> signals; // EEG signal data (channels x samples)
    std::vector<std::string> channelLabels;   // Channel names
    int sampleRate;                           // Sample rate (Hz)
    int numChannels;                          // Number of EEG channels
};

class DataAcquisition {
public:
    DataAcquisition();
    ~DataAcquisition();

    EEGData readEDFFile(const std::string& filename); // Reads EEG data from an EDF file

private:
    void printMetadata(const EEGData& data); // Helper function to display metadata
};

#endif // DATA_ACQUISITION_H
