# MQTT Vehicle Data Project

![Python](https://img.shields.io/badge/Python-3.7%2B-blue) ![MQTT](https://img.shields.io/badge/Protocol-MQTT-orange) ![GUI](https://img.shields.io/badge/GUI-Tkinter-green)

A complete solution for transmitting and decoding vehicle data using the MQTT protocol. This project includes a **producer** application, built with Tkinter, and a **consumer** application featuring a Flask-based graphical interface.

> **Note:** The consumer no longer uses [`consommateur.py`](consommateur.py) as its GUI; instead, it is implemented with [`app.py`](app.py). Also, it is mandatory to use the provided virtual environment (`venv`) for the Flask application to work properly.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Virtual Environment Setup](#virtual-environment-setup)
- [Network Requirements](#network-requirements)
- [Broker Setup](#broker-setup)
- [Role-Specific Instructions](#role-specific-instructions)
  - [Producer Instructions](#producer-instructions)
  - [Consumer Instructions](#consumer-instructions)
- [File Structure](#file-structure)
- [Sample Data](#sample-data)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Contact](#contact)

## Overview
This project enables seamless vehicle data transmission over MQTT. Key features include:
- 📱 MQTT-based packet transmission
- 🖥️ GUI for the producer (Tkinter) and consumer (Flask)
- 📁 PCAP file handling and preview (producer)
- ⏱️ Adjustable transmission delay
- 📊 Real-time progress tracking
- 🚗 Vehicle data decoding (position, speed, heading)
- 📝 Message logging and saving
- 🔧 Configurable **broker IP, port, and topic name** in both producer and consumer

## Prerequisites
- Python 3.7+
- Mosquitto MQTT broker
- Required Python packages:
  ```bash
  pip install scapy paho-mqtt flask flask-socketio folium pillow
  ```
- Tkinter (for GUI support)
  - Ubuntu/Debian:
    ```bash
    sudo apt-get install tk
    ```
  - Arch Linux:
    ```bash
    sudo pacman -S tk
    ```

## Installation
Clone the repository:
```bash
git clone https://github.com/your-repo/mqtt-vehicle-data.git
cd mqtt-vehicle-data
```

## Virtual Environment Setup
1. **Create a virtual environment and use it for the Flask app:**
   ```bash
   python -m venv venv
   ```
2. **Activate the virtual environment:**
   - On Linux/macOS:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
3. **Install the required packages:**
   ```bash
   pip install scapy paho-mqtt flask flask-socketio folium pillow
   ```

## Network Requirements
- All machines (broker, producer, and consumer) **must be on the same network**.
- Ensure firewall rules allow MQTT traffic (default port **1883**).
- If using a virtualized environment, configure networking to **Bridged Adapter** for proper communication.

## Broker Setup
### Install and Configure Mosquitto
1. **Install Mosquitto MQTT broker:**
   - Ubuntu/Debian:
     ```bash
     sudo apt-get install mosquitto mosquitto-clients
     ```
   - Arch Linux:
     ```bash
     sudo pacman -S mosquitto
     ```
2. **Configure Mosquitto to allow anonymous connections (for testing):**
   ```ini
   sudo nano /etc/mosquitto/mosquitto.conf
   ```
   Add the following lines:
   ```ini
   allow_anonymous true
   listener 1883 0.0.0.0
   ```
3. **Restart Mosquitto service:**
   ```bash
   sudo systemctl restart mosquitto
   ```

## Role-Specific Instructions

### Producer Instructions
1. Start the producer application:
   ```bash
   python producteur.py
   ```
2. **GUI Controls:**
   - 🗃 **Select Files**: Choose PCAP files to send
   - 👁 **Preview**: Display packet summaries before transmission
   - ⏱️ **Transmission Delay**: Adjust delay between packets (0-1s)
   - ▶️ **Start Transmission**: Begin sending packets to the broker
   - ⏸️/⏯️ **Pause/Resume**: Control transmission dynamically
   - 🌐 **Set Broker IP/Port and Topic**: Choose custom MQTT settings

![Producer GUI](https://via.placeholder.com/600x400?text=Producer+GUI+Preview)

### Consumer Instructions
1. **Activate the virtual environment before starting the Flask app.**
2. Start the consumer application:
   ```bash
   python app.py
   ```
3. **GUI Features (accessed via a web browser):**
   - 🛡 **Connect** to broker with IP, Port, and Topic
   - 📨 **View Raw Packets** in real time
   - 🚘 **Decoded Vehicle Data** (position, speed, heading)
   - 🔒 **Save Messages** to a log file
   - 🌐 **Set Broker IP/Port and Topic**: Choose custom MQTT settings

![Consumer GUI](https://via.placeholder.com/600x400?text=Consumer+GUI+Preview)

## File Structure
```
mqtt-vehicle-data/
├── app.py                 # Flask application for dynamic map display (consumer)
├── producteur.py          # Producer application (Tkinter based)
├── etsi-its-cam-secured.pcapng    # Sample PCAP file (secured)
├── etsi-its-cam-unsecured.pcapng  # Sample PCAP file (unsecured)
├── templates/
│   └── index.html         # HTML template for the consumer application
├── venv/                  # Virtual environment (mandatory for the Flask app)
└── README.md              # This documentation
```

## Sample Data
- *etsi-its-cam-secured.pcapng*
- *etsi-its-cam-unsecured.pcapng*

## Troubleshooting
- 🔗 **Connection Issues**: Ensure all devices are on the same network and verify broker IP/port.
- 📦 **Missing Packets**: Check that producer and consumer are using the same MQTT topic.
- 🧐 **Decoding Errors**: Ensure PCAP files contain valid ETSI ITS CAM data.
- ⏳ **Performance Issues**: Reduce transmission speed for large PCAP files.

## License
MIT License - Free for educational and commercial use. See LICENSE for details.

## Contact
For any questions or support, please contact:

- **Selyan KABLIA**: selyan.kablia@ens.uvsq.fr
- **Nathan LESTRADE**: nathan.lestrade@ens.uvsq.fr
- **Frederic MUSIAL**: frederic.musial@ens.uvsq.fr

---

**Happy vehicular data streaming!** 🚗💨