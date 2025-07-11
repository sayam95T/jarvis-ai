# JARVIS AI - Voice Assistant with Wake Word, GroqCloud, and GUI

import pvporcupine
import pyaudio
import struct
import sounddevice as sd
import scipy.io.wavfile as wavfile
import tempfile
import threading
import tkinter as tk
from tkinter import ttk
import pyttsx3
import os
import time
import datetime
import speech_recognition as sr
import requests
import re
import os
from dotenv import load_dotenv

load_dotenv()
chat_history = [
    {"role": "system", "content": "You are JARVIS, Sayam's smart assistant like Tony Stark's JARVIS.You talk quick , in few words."}
]
# Known apps and their paths or commands
APP_PATHS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "vscode": r"C:\Users\Sayam\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "spotify": r"C:\Users\Sayam\AppData\Roaming\Spotify\Spotify.exe"
    # Add more as needed
}
todo_list = []

# --- CONFIGURATION ---
WAKE_WORD = "jarvis"
PORCUPINE_KEY = os.getenv("PORCUPINE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# --- TEXT TO SPEECH SETUP ---
import pyttsx3

# --- TEXT TO SPEECH SETUP ---
engine = pyttsx3.init()
voices = engine.getProperty('voices')
male_voice = next((v for v in voices if "male" in v.name.lower() or "male" in v.id.lower()), voices[0])
engine.setProperty('voice', male_voice.id)
engine.setProperty('rate', 175)

def talk(text):
    def speak():
        print("Jarvis:", text)
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[Jarvis] Error while speaking: {e}")

    threading.Thread(target=speak, daemon=True).start()


# --- GUI SETUP ---
import psutil
import datetime
import threading
import random
import tkinter as tk
from tkinter import ttk

class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS AI")
        self.root.geometry("800x700")
        self.root.configure(bg="#0f0f0f")

        self.state = "idle"
        self.pulse_radius = 40
        self.arc_base_radius = 40
        self.pulse_direction = 1

        # Title with animation
        self.title_text = "JARVIS ONLINE"
        self.title = tk.Label(root, text=self.title_text, font=("Orbitron", 28, "bold"), bg="#0f0f0f", fg="#00ffff")
        self.title.pack(pady=10)
        self.blink_title()

        # Status label
        self.status = tk.Label(root, text="Waiting for wake word...", font=("Consolas", 14), bg="#0f0f0f", fg="#ffffff")
        self.status.pack(pady=5)

        # Arc Reactor Canvas Visualizer
        self.canvas = tk.Canvas(root, width=200, height=200, bg="#0f0f0f", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.arc_center_x = 100
        self.arc_center_y = 100
        self.animate_arc_reactor()

        # Response box with scrollbar
        self.response_frame = tk.Frame(root, bg="#0f0f0f")
        self.scrollbar = tk.Scrollbar(self.response_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.response = tk.Text(self.response_frame, wrap=tk.WORD, bg="#101010", fg="#00ff99", font=("Consolas", 12), height=12, width=90, yscrollcommand=self.scrollbar.set)
        self.response.pack(side=tk.LEFT, fill=tk.BOTH)
        self.scrollbar.config(command=self.response.yview)
        self.response_frame.pack(pady=10)

        # System info
        self.sysinfo = tk.Label(root, text="", font=("Consolas", 10), bg="#0f0f0f", fg="#888888")
        self.sysinfo.pack(pady=10)

        # Command box for manual testing
        self.command_entry = tk.Entry(root, font=("Consolas", 12), width=60, bg="#1a1a1a", fg="#00ff99", insertbackground="#00ff99")
        self.command_entry.pack(pady=5)
        self.command_entry.bind("<Return>", self.manual_command_submit)

        self.update_sysinfo()

    def blink_title(self):
        current_color = self.title.cget("fg")
        next_color = "#00ffff" if current_color == "#0f0f0f" else "#0f0f0f"
        self.title.config(fg=next_color)
        self.root.after(600, self.blink_title)

    def update_status(self, text):
        self.status.config(text=text)

    def show_response(self, text):
        self.response.insert(tk.END, f"\nJarvis: {text}\n")
        self.response.see(tk.END)

    def show_user_command(self, text):
        self.response.insert(tk.END, f"\nYou: {text}\n")
        self.response.see(tk.END)

    def manual_command_submit(self, event=None):
        command = self.command_entry.get().strip()
        if command:
            self.show_user_command(command)
            from threading import Thread
            Thread(target=self.process_command, args=(command,), daemon=True).start()
            self.command_entry.delete(0, tk.END)

    def process_command(self, command):
        self.set_state("speaking")
        self.update_status("🧠 Processing...")
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            chat_history.append({"role": "user", "content": command})
            payload = {
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "messages": chat_history
            }

            response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            if response.status_code == 200:
                result = response.json()["choices"][0]["message"]["content"]
                chat_history.append({"role": "assistant", "content": result})
                self.show_response(result)
                from threading import Thread
                Thread(target=talk, args=(result,), daemon=True).start()
            else:
                self.show_response("Error: Failed to get response.")
        except Exception as e:
            self.show_response(f"Error: {e}")
        finally:
            self.set_state("idle")
            self.update_status("Waiting for wake word...")

    def set_state(self, new_state):
        self.state = new_state

    def animate_arc_reactor(self):
        self.canvas.delete("all")
        color_map = {
            "idle": "#003366",
            "listening": "#00ffff",
            "speaking": "#ff3300"
        }
        glow_color = color_map.get(self.state, "#003366")

        r = self.pulse_radius
        self.canvas.create_oval(
            self.arc_center_x - r,
            self.arc_center_y - r,
            self.arc_center_x + r,
            self.arc_center_y + r,
            outline=glow_color,
            width=4
        )

        # Pulse effect logic
        if self.pulse_radius >= self.arc_base_radius + 10:
            self.pulse_direction = -1
        elif self.pulse_radius <= self.arc_base_radius:
            self.pulse_direction = 1

        self.pulse_radius += self.pulse_direction
        self.root.after(80, self.animate_arc_reactor)

    def update_sysinfo(self):
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
        now = datetime.datetime.now().strftime("%H:%M:%S %d-%b-%Y")
        self.sysinfo.config(text=f"CPU: {cpu}% | RAM: {memory}% | {now}")
        self.root.after(1000, self.update_sysinfo)


# --- ONLINE SPEECH-TO-TEXT (Google STT) ---
def transcribe_audio():
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙️ Listening for command...")
        try:
            audio = recognizer.listen(source)
        except Exception as e:
            raise Exception(f"Microphone listening failed: {e}")

    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        raise Exception("Speech was unintelligible.")
    except sr.RequestError as e:
        raise Exception(f"Speech recognition error: {e}")


# --- GROQ AI COMMAND HANDLING ---


def handle_command(text):
    print("User:", text)
    chat_history.append({"role": "user", "content": text})
    # --- App launch detection ---
    for app in APP_PATHS:
        if f"open {app}" in text.lower() or f"launch {app}" in text.lower():
                try: 
                    os.startfile(APP_PATHS[app])
                    return f"Launching {app.capitalize()}..."
                except Exception as e:
                     return f"Sorry, I couldn't open {app}. Error: {e}"
    lower_text = text.lower()

    # --- To-Do List Handling ---
    if "add" in lower_text and "to my list" in lower_text:
        item = lower_text.split("add", 1)[1].split("to my list")[0].strip()
        if item:
            todo_list.append(item)
            return f"Added '{item}' to your to-do list."
        else:
            return "What should I add to your list?"

    elif "remove" in lower_text and "from my list" in lower_text:
        item = lower_text.split("remove", 1)[1].split("from my list")[0].strip()
        if item:
            if item in todo_list:
                todo_list.remove(item)
                return f"Removed '{item}' from your to-do list."
            else:
                return f"'{item}' wasn't found in your to-do list."
        else:
            return "What should I remove from your list?"

    elif "what's on my list" in lower_text or "what is on my list" in lower_text or "show my list" in lower_text:
        if todo_list:
            items = "\n".join([f"- {i}" for i in todo_list])
            return f"Here’s what’s on your to-do list:\n{items}"
        else:
            return "Your to-do list is currently empty."
    lower_text = text.lower()


    # --- Otherwise, send to Groq ---
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": chat_history
    }

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        reply = response.json()["choices"][0]["message"]["content"]
        chat_history.append({"role": "assistant", "content": reply})
        return reply
    else:
        raise Exception(f"Groq API Error {response.status_code}: {response.text}")




# --- HOTWORD DETECTION THREAD ---
def start_hotword_detection(gui):
    porcupine = pvporcupine.create(access_key=PORCUPINE_KEY, keywords=[WAKE_WORD])
    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )
    print("[JARVIS] Hotword detection started...")

    while True:
        pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            gui.update_status("🎙️ Wake word detected! Listening...")
            try:
                talk("Yes Boss?")
                engine.runAndWait()
                gui.update_status("🎙️ Listening...")
                command = transcribe_audio()
                gui.show_user_command(command)
                gui.update_status("🧠 Processing...")
                response = handle_command(command)
                gui.show_response(response)
                talk(response)
            except Exception as e:
                gui.update_status("Error processing request.")
                print("Exception occurred:", e)
                talk(f"Sorry, I couldn't process that. Error: {e}")
            finally:
                gui.update_status("Waiting for wake word...")

# --- MAIN ENTRY POINT ---
if __name__ == '__main__':
    root = tk.Tk()
    gui = JarvisGUI(root)
    threading.Thread(target=start_hotword_detection, args=(gui,), daemon=True).start()
    root.mainloop()
