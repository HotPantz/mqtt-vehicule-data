import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from tkinter import ttk
import paho.mqtt.client as mqtt
from scapy.all import Ether
import threading

def decode_vehicle_info(packet):
    # Get the raw frame bytes
    raw = packet.original
    # Verify we have enough bytes for all fields (at least through byte 61)
    if len(raw) < 62:
        return "Insufficient data for vehicle info"
    
    # Ethernet header: bytes 0–13 (14 bytes) [not used for vehicle info]
    # GeoNetworking Basic Header: bytes 14–17 (4 bytes)
    # Common Header: bytes 18–25 (8 bytes)
    # Source Position: bytes 26–45 (20 bytes)
    source_pos = raw[26:46]
    # Following fields:
    # Timestamp: bytes 46–49 (4 bytes)
    timestamp = int.from_bytes(raw[46:50], byteorder='big')
    # Latitude: bytes 50–53 (4 bytes, signed)
    latitude_int = int.from_bytes(raw[50:54], byteorder='big', signed=True)
    # Longitude: bytes 54–57 (4 bytes, signed)
    longitude_int = int.from_bytes(raw[54:58], byteorder='big', signed=True)
    # Speed: bytes 58–59 (2 bytes)
    speed_int = int.from_bytes(raw[58:60], byteorder='big')
    # Heading: bytes 60–61 (2 bytes)
    heading_int = int.from_bytes(raw[60:62], byteorder='big')
    
    # Conversion/scaling (adjust factors as required):
    # For example, assume:
    # • Latitude and Longitude are in 1e7 fixed point format
    # • Speed scaled by 100 yields m/s
    latitude = latitude_int / 1e7
    longitude = longitude_int / 1e7
    speed = speed_int / 100.0
    
    # Interpret the first 8 bytes of Source Position as a vehicle identifier (GN_ADDR)
    vehicle_id = source_pos[:8].hex()
    
    return (f"Vehicle GN_ADDR: {vehicle_id}\n"
            f"Timestamp: {timestamp} ms\n"
            f"Latitude: {latitude}\n"
            f"Longitude: {longitude}\n"
            f"Speed: {speed} m/s\n"
            f"Heading: {heading_int} degrees")

def on_message(client, userdata, message):
    # Parse the payload as an Ethernet frame
    packet = Ether(message.payload)
    raw_details = packet.show(dump=True)
    vehicle_info = decode_vehicle_info(packet)
    # Insert raw packet details into the Raw Packets tab
    raw_text.insert(tk.END, raw_details + "\n\n")
    raw_text.see(tk.END)
    # Insert decoded information into the Vehicle Info tab
    info_text.insert(tk.END, vehicle_info + "\n\n")
    info_text.see(tk.END)

def start_mqtt():
    global client
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
    try:
        client.loop_stop()
        client.disconnect()
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

# Tkinter setup
root = tk.Tk()
root.title("MQTT Consumer Avancé")

# Configuration frame for IP, Port and Topic
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

# Control buttons
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

# Notebook with two tabs: Raw Packets and Vehicle Info
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Tab for Raw Packets
raw_frame = tk.Frame(notebook)
raw_text = scrolledtext.ScrolledText(raw_frame, wrap=tk.WORD, width=100, height=30)
raw_text.pack(fill=tk.BOTH, expand=True)
notebook.add(raw_frame, text="Raw Packets")

# Tab for Decoded Vehicle Info
info_frame = tk.Frame(notebook)
info_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, width=100, height=30)
info_text.pack(fill=tk.BOTH, expand=True)
notebook.add(info_frame, text="Vehicle Info")

root.mainloop()