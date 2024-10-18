# iAware Prototype

## Description
This repository stores a prototype of iAware, a meditation training application. The prototype contains a Python-based UI (/UI) connecting with MUSE, an affordable EEG data acquisition, through Bluetooth. The UI has an option of face login.
The UI receives EEG from MUSE and performs mind-wandering detection using the support vector machine, see Rungsilp et al. 2021 published as a conference paper at CELDA 2021.

The prototype also contains a C-based ESP32 firmware (/ESP32 fireware). The firmware connects with TGAM, another affordable EEG data acquisition. The ESP32 firmware gets the attention level from TGAM and 
displays it in real time, as well as communicates with PC through either Bluetooth or WI-FI.

## UI
### Installation
- Hardware requirement: PC and MUSE
- We recommend using the conda environment for Python installation.
- It runs with Python 3.7.
- Install required packages using conda.
- Install PyQt 5.

### Usage
- User wears MUSE.
- Connect MUSE to PC through Bluetooth.
- python main.py to execute the UI application. New User can sign-in with either password or face recognition.

### Product Overview
![Image](/images/iAware_app.png)

## ESP32 firmware
### Installation
- Hardware requirements: ESP32-WROOM and TGAM.
- You need to build and upload the source codes using ESP-IDF.

### Usage
- User wear TGAM.
- Your attention level will appear at the 7-segment display.

### Product Overview
![Image](/images/esp32.JPG)

## License
This project is licensed under the MIT License.
