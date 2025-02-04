```markdown
# MQTT Vehicle Data Project

![MQTT Vehicle Data Project](https://img.shields.io/badge/Python-3.7%2B-blue)
![MQTT Protocol](https://img.shields.io/badge/Protocol-MQTT-orange)
![GUI Framework](https://img.shields.io/badge/GUI-Tkinter-green)

A complete solution for transmitting and decoding vehicle data using MQTT protocol. Includes both producer and consumer applications with intuitive GUIs.

## Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [File Structure](#file-structure)
- [Broker Setup](#broker-setup)
- [Usage](#usage)
  - [Producer](#producer)
  - [Consumer](#consumer)
- [Sample Data](#sample-data)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features
- 📡 MQTT-based packet transmission
- 🖥️ Dual GUI interface for both producer and consumer
- 📁 PCAP file handling with preview capabilities
- ⏱️ Adjustable transmission delay
- 📊 Real-time progress tracking
- 🚗 Vehicle data decoding (position, speed, heading)
- 📝 Message logging and saving

## Prerequisites
- Python 3.7+
- Mosquitto MQTT broker
- Required Python packages:
  ```bash
  pip install scapy paho-mqtt
  ```

## File Structure
```
mqtt-vehicle-data/
├── consommateur.py        # Consumer application
├── producteur.py          # Producer application
├── etsi-its-cam-*.pcapng  # Sample PCAP files (secured/unsecured)
├── log.txt                # Sample packet log
└── README.md              # This documentation
```

## Broker Setup
1. Install Mosquitto:
   ```bash
   sudo apt-get install mosquitto mosquitto-clients
   ```
2. Configure `/etc/mosquitto/mosquitto.conf`:
   ```ini
   allow_anonymous true
   listener 1883 0.0.0.0
   ```
3. Restart service:
   ```bash
   sudo systemctl restart mosquitto
   ```

## Usage

### Producer
1. Launch application:
   ```bash
   python producteur.py
   ```
2. GUI Controls:
   - 🖿 **Choisir fichiers**: Select PCAP files
   - 👁️ **Prévisualiser**: Preview packet summaries
   - 🎚️ Delay slider: Set transmission interval (0-1s)
   - ▶️ **Démarrer l'envoi**: Start transmission
   - ⏸️/⏯️ Pause/Resume controls

![Producer GUI](https://via.placeholder.com/600x400?text=Producer+GUI+Preview)

### Consumer
1. Launch application:
   ```bash
   python consommateur.py
   ```
2. GUI Features:
   - 📡 Connect to broker with IP/Port/Topic
   - 📨 Real-time packet display in Raw Packets tab
   - 🚘 Decoded vehicle data in Vehicle Info tab
   - 💾 Save messages to text file

![Consumer GUI](https://via.placeholder.com/600x400?text=Consumer+GUI+Preview)

## Sample Data
Example log entry (`log.txt`):
```txt
###[ Ethernet ]###
  dst       = 62:61:3a:37:34:3a
  src       = 39:37:3a:30:35:3a
  type      = 0x6134
###[ Raw ]###
     load      = b':1d > ff:ff:ff:ff:ff:ff (0x8947) / Raw'
```

## Troubleshooting
- 🔗 **Connection Issues**: Verify broker IP/port and network connectivity
- 📦 **Missing Packets**: Check topic consistency between producer/consumer
- 🐞 **Decoding Errors**: Ensure PCAP files contain valid ETSI ITS CAM data
- ⏳ **Performance**: Reduce transmission speed for large PCAP files

## License
MIT License - Free for educational and commercial use. See [LICENSE](LICENSE) for details.

---

**Happy vehicular data streaming!** 🚗💨
```