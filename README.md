# iAware, a meditation training application.

## Description
This repository stores a prototype of iAware. The prototype contains a Python-based UI running on Windows 10 (/UI) and a C-based ESP32 firmware (/ESP32 fireware). The UI has an option of face login. The ESP32 firmware communicates with the UI through either Bluetooth or WI-FI.

## Installation
### UI
- We recommend using the conda environment.
- It runs with Python 3.7
- Install required packages using conda.
### ESP32 firmware
- Hardware requirements: ESP32-WROOM and EEG sensor.
- You need to build and upload the source code using ESP-IDF.

## Usage
- Connect ESP32 to PC using either Bluetooth or WI-FI.
- python main.py to execute the UI application.
- If it is your first time log-in to the system, we can create the password-based login or the face-based login.
- Install EEG sensor on the user. The user do meditation. If the user has mind wandering during meditation, iAware will warn the user.

## Product Overview


## License
This project is licensed under the MIT License.
