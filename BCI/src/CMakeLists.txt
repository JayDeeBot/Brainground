cmake_minimum_required(VERSION 3.10)
project(BCI_Project)

set(CMAKE_CXX_STANDARD 17)

add_executable(BCI_Project src/main.cpp src/DataAcquisition.cpp)

target_include_directories(BCI_Project PRIVATE /usr/local/include)
target_link_libraries(BCI_Project PRIVATE edflib)