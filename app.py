# app.py (Flask application)
import logging
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import threading
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

def decode_vehicle_info(packet):
    raw = packet.original
    if len(raw) < 68:
        logging.debug("Packet too short for decoding")
        return "Insufficient data", None, None, None
    vehicle_id = raw[26:34].hex()
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
        f"Heading: {heading}°"
    )
    logging.debug("Decoded info: %s", info)
    return info, vehicle_id, latitude, longitude

def on_connect(client, userdata, flags, rc):
    logging.debug("Connected to MQTT broker with result code %s", rc)
    client.subscribe(MQTT_TOPIC)
    logging.debug("Subscribed to topic: %s", MQTT_TOPIC)

def on_message(client, userdata, message):
    logging.debug("MQTT message received on topic %s", message.topic)
    try:
        packet = Ether(message.payload)
        raw_data = packet.show(dump=True)
        info, vehicle_id, latitude, longitude = decode_vehicle_info(packet)
        
        RAW_MESSAGES.append(raw_data)
        if info:
            TRANSLATED_MESSAGES.append(info)
        if vehicle_id:
            VEHICLE_DATA.setdefault(vehicle_id, []).append([latitude, longitude])
        
        # Emit events for each tab
        socketio.emit('raw', {'data': raw_data})
        socketio.emit('translated', {'data': info})
        socketio.emit('update', {
            'vehicle_id': vehicle_id,
            'latitude': latitude,
            'longitude': longitude
        })
        logging.debug("Emitted events for vehicle_id: %s", vehicle_id)
    except Exception as e:
        logging.error("Error processing MQTT message: %s", e)


# Dans la fonction start_mqtt(), utilisez callback_api_version="1.0" (en chaîne) :
def start_mqtt():
    global mqtt_client, mqtt_thread_handle
    with mqtt_lock:
        if mqtt_client:
            try:
                mqtt_client.disconnect()
            except Exception as e:
                logging.error("Error disconnecting previous MQTT client: %s", e)
        # Initialisation du client MQTT sans callback_api_version
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