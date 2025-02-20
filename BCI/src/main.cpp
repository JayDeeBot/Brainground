#include "DataAcquisition.h"

int main() {
    DataAcquisition daq;
    EEGData eegData = daq.readEDFFile("data/test.edf"); // Make sure you have a test file in the data folder

    return 0;
}
