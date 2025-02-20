#include "DataAcquisition.h"
#include <iostream>
#include <vector>
#include "edflib.h"  // Ensure EDFLib is installed and linked

DataAcquisition::DataAcquisition() {}
DataAcquisition::~DataAcquisition() {}

EEGData DataAcquisition::readEDFFile(const std::string& filename) {
    EEGData eegData;
    
    // Open EDF file
    int edfFile = edfopen_file_readonly(filename.c_str(), EDFLIB_READ_ALL_ANNOTATIONS);
    if (edfFile < 0) {
        std::cerr << "Error opening EDF file: " << filename << std::endl;
        return eegData;
    }

    // Get metadata
    eegData.numChannels = edf_get_signal_count(edfFile);
    eegData.sampleRate = edf_get_sample_frequency(edfFile, 0); // Assuming all channels have the same rate

    std::cout << "EDF File Loaded: " << filename << std::endl;
    std::cout << "Channels: " << eegData.numChannels << " | Sample Rate: " << eegData.sampleRate << " Hz" << std::endl;

    // Allocate storage
    eegData.signals.resize(eegData.numChannels);
    eegData.channelLabels.resize(eegData.numChannels);

    // Read channel labels
    for (int i = 0; i < eegData.numChannels; i++) {
        char label[EDF_MAX_LABEL_LENGTH];
        edf_get_label(edfFile, i, label);
        eegData.channelLabels[i] = std::string(label);
    }

    // Read EEG signal data
    for (int ch = 0; ch < eegData.numChannels; ch++) {
        int numSamples = edf_get_sample_count(edfFile, ch);
        eegData.signals[ch].resize(numSamples);

        std::vector<double> buffer(numSamples);
        edf_read_physical_samples(edfFile, ch, buffer.data(), numSamples);

        eegData.signals[ch] = buffer;
    }

    // Close EDF file
    edfclose_file(edfFile);

    // Print metadata
    printMetadata(eegData);
    
    return eegData;
}

void DataAcquisition::printMetadata(const EEGData& data) {
    std::cout << "=== EDF File Metadata ===" << std::endl;
    std::cout << "Number of Channels: " << data.numChannels << std::endl;
    std::cout << "Sample Rate: " << data.sampleRate << " Hz" << std::endl;
    std::cout << "Channels: ";
    for (const auto& label : data.channelLabels) {
        std::cout << label << " ";
    }
    std::cout << std::endl;
}
