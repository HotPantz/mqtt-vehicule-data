import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import threading
import time, os
import paho.mqtt.client as mqtt
from scapy.all import rdpcap

class ProducerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Producteur MQTT Avancé")
        self.files = []
        self.total_packets = 0
        self.sent_packets = 0
        self.start_time = None
        self.paused = threading.Event()
        self.paused.set()
        self.sending_thread = None
        self.build_gui()

    def build_gui(self):
        self.config_frame = tk.Frame(self.root)
        self.config_frame.pack(padx=10, pady=5, fill=tk.X)
        tk.Label(self.config_frame, text="Broker:").grid(row=0, column=0, sticky=tk.W)
        self.broker_entry = tk.Entry(self.config_frame)
        self.broker_entry.insert(tk.END, "localhost")
        self.broker_entry.grid(row=0, column=1, sticky=tk.EW)

        tk.Label(self.config_frame, text="Port:").grid(row=1, column=0, sticky=tk.W)
        self.port_entry = tk.Entry(self.config_frame)
        self.port_entry.insert(tk.END, "1883")
        self.port_entry.grid(row=1, column=1, sticky=tk.EW)

        tk.Label(self.config_frame, text="Topic:").grid(row=2, column=0, sticky=tk.W)
        self.topic_entry = tk.Entry(self.config_frame)
        self.topic_entry.insert(tk.END, "etsi-its-cam-unsecured")
        self.topic_entry.grid(row=2, column=1, sticky=tk.EW)
        self.config_frame.columnconfigure(1, weight=1)

        file_frame = tk.Frame(self.root)
        file_frame.pack(padx=10, pady=5, fill=tk.X)
        self.files_var = tk.StringVar()
        tk.Label(file_frame, text="Fichiers PCAP:").pack(side=tk.LEFT)
        self.file_label = tk.Label(file_frame, textvariable=self.files_var, relief=tk.SUNKEN, width=50, anchor="w")
        self.file_label.pack(side=tk.LEFT, padx=5)
        choose_button = tk.Button(file_frame, text="Choisir fichiers", command=self.choose_files)
        choose_button.pack(side=tk.LEFT)

        delay_frame = tk.Frame(self.root)
        delay_frame.pack(padx=10, pady=5, fill=tk.X)
        tk.Label(delay_frame, text="Délai (sec) entre packets:").pack(side=tk.LEFT)
        self.delay_slider = tk.Scale(delay_frame, from_=0, to=1, resolution=0.05, orient=tk.HORIZONTAL)
        self.delay_slider.set(0.1)
        self.delay_slider.pack(side=tk.LEFT, padx=5)

        progress_frame = tk.Frame(self.root)
        progress_frame.pack(padx=10, pady=5, fill=tk.X)
        tk.Label(progress_frame, text="Progression:").pack(side=tk.LEFT)
        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(side=tk.LEFT, padx=5)

        stats_frame = tk.Frame(self.root)
        stats_frame.pack(padx=10, pady=5, fill=tk.X)
        self.stats_label = tk.Label(stats_frame, text="Paquets envoyés : 0 / 0 | Temps écoulé : 0s")
        self.stats_label.pack(side=tk.LEFT)

        preview_frame = tk.Frame(self.root)
        preview_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        tk.Label(preview_frame, text="Prévisualisation:").pack(anchor=tk.W)
        self.preview_text = scrolledtext.ScrolledText(preview_frame, wrap=tk.WORD, height=10)
        self.preview_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        preview_button = tk.Button(preview_frame, text="Prévisualiser fichiers", command=self.preview_files)
        preview_button.pack(pady=5)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(padx=10, pady=5)
        self.start_btn = tk.Button(btn_frame, text="Démarrer l'envoi", command=self.start_sending)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.pause_btn = tk.Button(btn_frame, text="Pause", command=self.pause_sending, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        self.resume_btn = tk.Button(btn_frame, text="Reprendre", command=self.resume_sending, state=tk.DISABLED)
        self.resume_btn.pack(side=tk.LEFT, padx=5)

        log_frame = tk.Frame(self.root)
        log_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        tk.Label(log_frame, text="Log:").pack(anchor=tk.W)
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, width=80, height=10)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def choose_files(self):
        files = filedialog.askopenfilenames(
            title="Sélectionnez des fichiers PCAP",
            filetypes=(("Fichiers PCAPNG", "*.pcapng"), ("Fichiers PCAP", "*.pcap"), ("Tous les fichiers", "*.*"))
        )
        if files:
            self.files = list(files)
            self.files_var.set("; ".join([os.path.basename(f) for f in self.files]))
            self.log("Fichiers sélectionnés: " + self.files_var.get())

    def preview_files(self):
        self.preview_text.delete("1.0", tk.END)
        if not self.files:
            messagebox.showinfo("Info", "Aucun fichier sélectionné")
            return
        for f in self.files:
            try:
                packets = rdpcap(f, count=3)
                self.preview_text.insert(tk.END, f"--- {os.path.basename(f)} ---\n")
                for p in packets:
                    self.preview_text.insert(tk.END, p.summary() + "\n")
                self.preview_text.insert(tk.END, "\n")
            except Exception as e:
                self.preview_text.insert(tk.END, f"Erreur lors de la lecture de {f} : {e}\n\n")

    def log(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def update_stats(self):
        elapsed = int(time.time() - self.start_time) if self.start_time else 0
        self.stats_label.config(text=f"Paquets envoyés : {self.sent_packets} / {self.total_packets} | Temps écoulé : {elapsed}s")

    def pause_sending(self):
        self.paused.clear()
        self.log("Envoi en pause")
        self.pause_btn.config(state=tk.DISABLED)
        self.resume_btn.config(state=tk.NORMAL)

    def resume_sending(self):
        self.paused.set()
        self.log("Reprise de l'envoi")
        self.pause_btn.config(state=tk.NORMAL)
        self.resume_btn.config(state=tk.DISABLED)

    def sending_worker(self):
        broker = self.broker_entry.get()
        try:
            port = int(self.port_entry.get())
        except ValueError:
            self.log("Erreur: Le port doit être un nombre")
            return
        topic = self.topic_entry.get()
        delay = self.delay_slider.get()
        client = mqtt.Client(client_id="Producer")  # Removed callback_api_version parameter
        try:
            client.connect(broker, port)
            client.loop_start()
            self.log(f"Connecté au broker {broker}:{port} sur le topic '{topic}'")
        except Exception as e:
            self.log(f"Erreur de connexion : {e}")
            return

        self.total_packets = 0
        pcap_packets = []
        for f in self.files:
            try:
                packets = rdpcap(f)
                pcap_packets.extend(packets)
            except Exception as e:
                self.log(f"Erreur lors de la lecture de {f} : {e}")
        self.total_packets = len(pcap_packets)
        self.progress["maximum"] = self.total_packets
        self.sent_packets = 0
        self.start_time = time.time()

        for pkt in pcap_packets:
            self.paused.wait()
            payload = bytes(pkt)
            result = client.publish(topic, payload)
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                self.log(f"Erreur lors de l'envoi d'un paquet: {result}")
            self.sent_packets += 1
            self.root.after(0, self.progress.step, 1)
            self.root.after(0, self.update_stats)
            time.sleep(delay)
        client.loop_stop()
        client.disconnect()
        self.log("Tous les paquets ont été envoyés.")
        # Re-enable MQTT configuration fields after sending
        self.broker_entry.config(state=tk.NORMAL)
        self.port_entry.config(state=tk.NORMAL)
        self.topic_entry.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.resume_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.NORMAL)

    def start_sending(self):
        if not self.files:
            messagebox.showerror("Erreur", "Veuillez sélectionner au moins un fichier PCAP.")
            return
        self.progress["value"] = 0
        self.sent_packets = 0
        self.total_packets = 0
        self.start_time = time.time()
        # Lock MQTT configuration so changes mid-send are prevented
        self.broker_entry.config(state=tk.DISABLED)
        self.port_entry.config(state=tk.DISABLED)
        self.topic_entry.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.resume_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)
        self.paused.set()
        self.sending_thread = threading.Thread(target=self.sending_worker, daemon=True)
        self.sending_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ProducerApp(root)
    root.mainloop()