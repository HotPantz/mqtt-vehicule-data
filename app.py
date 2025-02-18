import logging
import time
import re
import threading
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
from scapy.all import Ether

# Setup logging
logging.basicConfig(level=logging.DEBUG,
                    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, logger=True, engineio_logger=True)

# Global containers for data
RAW_MESSAGES = []
TRANSLATED_MESSAGES = []
VEHICLE_DATA = {}  # { vehicle_id: [[lat, lon], ...] }

# MQTT configuration globals
MQTT_BROKER = '127.0.0.1'
MQTT_PORT = 1883
MQTT_TOPIC = 'v2v'

# Global MQTT client variable and thread handle
mqtt_client = None
mqtt_thread_handle = None
mqtt_lock = threading.Lock()

# Global variable to store the base vehicle timestamp (from the first packet)
base_vehicle_timestamp = None

def decode_vehicle_info(packet):
    raw = packet.original
    if len(raw) < 68:
        logging.debug("Packet too short for decoding")
        return "Insufficient data", None, None, None, 0, 0, None
    vehicle_id = int.from_bytes(raw[78:82], byteorder='big')
    timestamp = int.from_bytes(raw[52:56], byteorder='big')
    latitude_int = int.from_bytes(raw[56:60], byteorder='big', signed=True)
    longitude_int = int.from_bytes(raw[60:64], byteorder='big', signed=True)
    speed_int = int.from_bytes(raw[64:66], byteorder='big')
    heading_int = int.from_bytes(raw[66:68], byteorder='big')
    latitude = latitude_int / 1e7
    longitude = longitude_int / 1e7
    speed = speed_int / 100.0
    heading = heading_int / 10
    info = (
        f"Vehicle ID: {vehicle_id}\n"
        f"Timestamp: {timestamp} ms\n"
        f"Latitude: {latitude}\n"
        f"Longitude: {longitude}\n"
        f"Speed: {speed} m/s\n"
        f"Heading: {heading}"
    )
    logging.debug("Decoded info: %s", info)
    return info, vehicle_id, latitude, longitude, speed, heading, timestamp

def on_connect(client, userdata, flags, rc):
    logging.debug("Connected to MQTT broker with result code %s", rc)
    client.subscribe(MQTT_TOPIC)
    logging.debug("Subscribed to topic: %s", MQTT_TOPIC)

def on_message(client, userdata, message):
    # Ignore any packets that are not CAM (payload length != 121)
    if len(message.payload) != 121:
        logging.debug("Ignoring non-CAM packet with payload length: %s", len(message.payload))
        return

    global base_vehicle_timestamp
    logging.debug("MQTT message received on topic %s", message.topic)
    try:
        data_str = message.payload.decode('utf-8', errors='replace')
        logging.debug("Decoded payload (text): %s", data_str)
        # Try to extract fields from the text payload
        vehicle_ids = re.findall(r"Vehicle ID:\s*(\S+)", data_str)
        latitudes = re.findall(r"Latitude:\s*([0-9.]+)", data_str)
        longitudes = re.findall(r"Longitude:\s*([0-9.]+)", data_str)
        speeds = re.findall(r"Speed:\s*([0-9.]+)", data_str)
        headings = re.findall(r"Heading:\s*([0-9.]+)", data_str)
        # For text messages no timestamp is present.
        if vehicle_ids and latitudes and longitudes:
            vehicle_id = vehicle_ids[-1]
            latitude = float(latitudes[-1])
            longitude = float(longitudes[-1])
            speed = float(speeds[-1]) if speeds else 0
            heading = float(headings[-1]) if headings else 0
            timestamp = int(time.time() * 1000)  # use local time in ms as fallback timestamp
            info = f"Vehicle ID: {vehicle_id}, Latitude: {latitude}, Longitude: {longitude}, Speed: {speed} m/s, Heading: {heading}"
        else:
            # If text parsing fails, try binary decoding via Scapy.
            info, vehicle_id, latitude, longitude, speed, heading, timestamp = decode_vehicle_info(Ether(message.payload))
            if not vehicle_id:
                logging.error("Failed to parse required fields from both text and binary formats")
                return

        # Set the base vehicle timestamp if not already set.
        if timestamp is None:
            timestamp = int(time.time() * 1000)
        if base_vehicle_timestamp is None:
            base_vehicle_timestamp = timestamp

        # Calculate elapsed vehicle time
        elapsed = timestamp - base_vehicle_timestamp

        RAW_MESSAGES.append(data_str)
        TRANSLATED_MESSAGES.append(info)
        VEHICLE_DATA.setdefault(vehicle_id, []).append([latitude, longitude])
        
        # Emit events including additional timestamp and elapsed time fields.
        socketio.emit('raw', {'data': data_str})
        socketio.emit('translated', {'data': info})
        socketio.emit('update', {
            'vehicle_id': vehicle_id,
            'latitude': latitude,
            'longitude': longitude,
            'speed': speed,
            'heading': heading,
            'timestamp': timestamp,
            'elapsed': elapsed
        })
        logging.debug("Emitted events for vehicle_id: %s, elapsed: %s ms", vehicle_id, elapsed)
    except Exception as e:
        logging.error("Error processing MQTT message: %s", e)

def start_mqtt():
    global mqtt_client, mqtt_thread_handle
    with mqtt_lock:
        if mqtt_client:
            try:
                mqtt_client.disconnect()
            except Exception as e:
                logging.error("Error disconnecting previous MQTT client: %s", e)
        mqtt_client = mqtt.Client(client_id="ConsumerFlask")
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message

        try:
            logging.debug("Connecting to MQTT broker at %s:%s", MQTT_BROKER, MQTT_PORT)
            mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        except Exception as e:
            logging.error("MQTT connection failed: %s", e)
            return

        mqtt_thread_handle = threading.Thread(target=mqtt_client.loop_forever, daemon=True)
        mqtt_thread_handle.start()
        logging.debug("MQTT client loop started in background thread")

# Start the initial MQTT connection on app launch
start_mqtt()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_config', methods=['POST'])
def update_config():
    global MQTT_BROKER, MQTT_PORT, MQTT_TOPIC
    data = request.form
    new_broker = data.get('broker', MQTT_BROKER)
    new_port = data.get('port', MQTT_PORT)
    new_topic = data.get('topic', MQTT_TOPIC)
    try:
        new_port = int(new_port)
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Port must be a number'}), 400

    MQTT_BROKER = new_broker
    MQTT_PORT = new_port
    MQTT_TOPIC = new_topic
    logging.debug("Updated config: Broker:%s, Port:%s, Topic:%s", MQTT_BROKER, MQTT_PORT, MQTT_TOPIC)
    return jsonify({'status': 'success', 'broker': MQTT_BROKER, 'port': MQTT_PORT, 'topic': MQTT_TOPIC})

@app.route('/connect_broker', methods=['POST'])
def connect_broker():
    start_mqtt()
    logging.debug("Connect broker endpoint called.")
    return jsonify({'status': 'success', 'message': 'Connected to broker at {}:{}'.format(MQTT_BROKER, MQTT_PORT)})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)