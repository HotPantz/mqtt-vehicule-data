import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from tkinter import ttk
import paho.mqtt.client as mqtt
from scapy.all import Ether
import folium
from io import BytesIO
from PIL import Image, ImageTk

client = None  # Global MQTT client
map_widget = None
vehicle_markers = {}
vehicle_paths = {}  # Global dictionary to store each vehicle's movement path

def decode_vehicle_info(packet):
    raw = packet.original
    # Vérifier qu'on a suffisamment d'octets
    if len(raw) < 68:
        return "Insufficient data for vehicle info", None, None, None

    # Identifiant véhicule à partir de raw[26:46]
    source_pos = raw[26:46]
    vehicle_id = source_pos[:8].hex()

    # Utilisation des offsets demandés
    # Timestamp : bytes 52 à 55 (slice raw[52:55])
    timestamp = int.from_bytes(raw[52:56], byteorder='big')
    # Latitude : bytes 56 à 59 (slice raw[56:59])
    latitude_int = int.from_bytes(raw[56:60], byteorder='big', signed=True)
    # Longitude : bytes 60 à 63 (slice raw[60:63])
    longitude_int = int.from_bytes(raw[60:64], byteorder='big', signed=True)
    # Vitesse : bytes 64 à 65 (slice raw[64:65]) - division par 100 pour obtenir m/s
    speed_int = int.from_bytes(raw[64:66], byteorder='big')
    # Heading : bytes 66 à 67 (slice raw[66:67])
    heading_int = int.from_bytes(raw[66:68], byteorder='big')

    latitude = latitude_int / 1e7
    longitude = longitude_int / 1e7
    speed = speed_int / 100.0
    # Ici heading est divisé par 10 pour obtenir les degrés (ajuster selon la spécification réelle)
    heading = heading_int / 10

    info = (f"Vehicle GN_ADDR: {vehicle_id}\n"
            f"Timestamp: {timestamp} ms\n"
            f"Latitude: {latitude}\n"
            f"Longitude: {longitude}\n"
            f"Speed: {speed} m/s\n"
            f"Heading: {heading} degrees")
    return info, vehicle_id, latitude, longitude

def on_message(client, userdata, message):
    packet = Ether(message.payload)
    raw_details = packet.show(dump=True)
    info, vehicle_id, latitude, longitude = decode_vehicle_info(packet)
    raw_text.insert(tk.END, raw_details + "\n\n")
    raw_text.see(tk.END)
    info_text.insert(tk.END, info + "\n\n")
    info_text.see(tk.END)
    update_map(vehicle_id, latitude, longitude)

def update_map(vehicle_id, latitude, longitude):
    global vehicle_markers, vehicle_paths, map_widget, map_label

    # Met à jour le chemin du véhicule
    if vehicle_id in vehicle_paths:
        vehicle_paths[vehicle_id].append([latitude, longitude])
    else:
        vehicle_paths[vehicle_id] = [[latitude, longitude]]

    # Supprime l'ancien marker si présent
    if vehicle_id in vehicle_markers:
        marker = vehicle_markers[vehicle_id]
        if marker.get_name() in map_widget._children:
            map_widget._children.pop(marker.get_name())

    # Place un nouveau marker à la dernière position reçue
    marker = folium.Marker(
        location=[latitude, longitude],
        popup=f"Vehicle ID: {vehicle_id}",
        icon=folium.Icon(color='red', icon='info-sign')
    )
    vehicle_markers[vehicle_id] = marker
    marker.add_to(map_widget)

    # Supprime la polyline précédente pour ce véhicule si elle existe, pour une mise à jour propre
    polyline_name = f"polyline_{vehicle_id}"
    if polyline_name in map_widget._children:
        map_widget._children.pop(polyline_name)
        
    # Dessine la trajectoire du véhicule avec une polyline
    folium.PolyLine(
        vehicle_paths[vehicle_id],
        color="blue",
        weight=2.5,
        opacity=1,
        name=polyline_name
    ).add_to(map_widget)

    # Régénère l'image de la carte et met à jour le label Tkinter
    map_data = map_widget._to_png(5)
    map_image = BytesIO(map_data)
    pic = Image.open(map_image)
    map_photo = ImageTk.PhotoImage(pic)
    map_label.config(image=map_photo)
    map_label.image = map_photo

    # Rafraîchir l'interface utilisateur
    root.update_idletasks()

def start_mqtt():
    global client
    if client is not None:
        stop_mqtt()
    ip = ip_entry.get()
    try:
        port = int(port_entry.get())
    except ValueError:
        messagebox.showerror("Erreur", "Le port doit être un nombre")
        return
    topic = topic_entry.get()
    try:
        client = mqtt.Client("Consumer")
        client.on_message = on_message
        client.connect(ip, port)
        client.loop_start()
        client.subscribe(topic)
        status_label.config(text="Connecté", fg="green")
    except Exception as e:
        messagebox.showerror("Erreur de connexion", str(e))
        status_label.config(text="Erreur de connexion", fg="red")

def stop_mqtt():
    global client
    try:
        if client is not None:
            client.loop_stop()
            client.disconnect()
            client = None
        status_label.config(text="Déconnecté", fg="red")
    except Exception:
        pass

def save_messages():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                             filetypes=[("Fichiers textes", "*.txt"), ("Tous les fichiers", "*.*")])
    if file_path:
        with open(file_path, 'w') as file:
            file.write("=== Raw Packets ===\n")
            file.write(raw_text.get("1.0", tk.END))
            file.write("\n=== Vehicle Information ===\n")
            file.write(info_text.get("1.0", tk.END))

root = tk.Tk()
root.title("MQTT Consumer Avancé")

config_frame = tk.Frame(root)
config_frame.pack(padx=10, pady=5, fill=tk.X)

tk.Label(config_frame, text="IP:").grid(row=0, column=0, sticky=tk.W)
ip_entry = tk.Entry(config_frame)
ip_entry.insert(tk.END, "127.0.0.1")
ip_entry.grid(row=0, column=1, sticky=tk.EW)

tk.Label(config_frame, text="Port:").grid(row=1, column=0, sticky=tk.W)
port_entry = tk.Entry(config_frame)
port_entry.insert(tk.END, "1883")
port_entry.grid(row=1, column=1, sticky=tk.EW)

tk.Label(config_frame, text="Topic:").grid(row=2, column=0, sticky=tk.W)
topic_entry = tk.Entry(config_frame)
topic_entry.insert(tk.END, "etsi-its-cam-unsecured")
topic_entry.grid(row=2, column=1, sticky=tk.EW)

config_frame.columnconfigure(1, weight=1)

control_frame = tk.Frame(root)
control_frame.pack(padx=10, pady=5)

start_button = tk.Button(control_frame, text="Start", command=start_mqtt)
start_button.grid(row=0, column=0, padx=5)
stop_button = tk.Button(control_frame, text="Stop", command=stop_mqtt)
stop_button.grid(row=0, column=1, padx=5)
save_button = tk.Button(control_frame, text="Save Messages", command=save_messages)
save_button.grid(row=0, column=2, padx=5)

status_label = tk.Label(root, text="Déconnecté", fg="red")
status_label.pack(pady=5)

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

raw_frame = tk.Frame(notebook)
raw_text = scrolledtext.ScrolledText(raw_frame, wrap=tk.WORD, width=100, height=30)
raw_text.pack(fill=tk.BOTH, expand=True)
notebook.add(raw_frame, text="Raw Packets")

info_frame = tk.Frame(notebook)
info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, width=100, height=30)
info_text.pack(fill=tk.BOTH, expand=True)
notebook.add(info_frame, text="Vehicle Info")

map_frame = tk.Frame(notebook)
map_label = tk.Label(map_frame)
map_label.pack(fill=tk.BOTH, expand=True)
notebook.add(map_frame, text="Map")

# Initialisation de la carte folium centrée sur une position par défaut
map_widget = folium.Map(location=[48.8566, 2.3522], zoom_start=12)

log_frame = tk.Frame(root)
log_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
tk.Label(log_frame, text="Log:").pack(anchor=tk.W)
log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=80, height=10)
log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

root.mainloop()