import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from tkinter import ttk
import paho.mqtt.client as mqtt
from scapy.all import Ether
import threading

client = None  # Global MQTT client

def decode_vehicle_info(packet):
    raw = packet.original
    if len(raw) < 62:
        return "Insufficient data for vehicle info"
    source_pos = raw[26:46]
    timestamp = int.from_bytes(raw[46:50], byteorder='big')
    latitude_int = int.from_bytes(raw[50:54], byteorder='big', signed=True)
    longitude_int = int.from_bytes(raw[54:58], byteorder='big', signed=True)
    speed_int = int.from_bytes(raw[58:60], byteorder='big')
    heading_int = int.from_bytes(raw[60:62], byteorder='big')
    latitude = latitude_int / 1e7
    longitude = longitude_int / 1e7
    speed = speed_int / 100.0
    vehicle_id = source_pos[:8].hex()
    
    return (f"Vehicle GN_ADDR: {vehicle_id}\n"
            f"Timestamp: {timestamp} ms\n"
            f"Latitude: {latitude}\n"
            f"Longitude: {longitude}\n"
            f"Speed: {speed} m/s\n"
            f"Heading: {heading_int} degrees")

def on_message(client, userdata, message):
    packet = Ether(message.payload)
    raw_details = packet.show(dump=True)
    vehicle_info = decode_vehicle_info(packet)
    raw_text.insert(tk.END, raw_details + "\n\n")
    raw_text.see(tk.END)
    info_text.insert(tk.END, vehicle_info + "\n\n")
    info_text.see(tk.END)

def start_mqtt():
    global client
    # Disconnect previous connection if any
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

root.mainloop()