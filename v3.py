# JARVIS AI - Voice Assistant with Wake Word, OpenAI, and GUI

import pvporcupine
import pyaudio
import struct
from openai import OpenAI
import openai
import sounddevice as sd
import scipy.io.wavfile as wavfile
import tempfile
import threading
import tkinter as tk
from tkinter import ttk
import pyttsx3
import os
import time
import os
from dotenv import load_dotenv

load_dotenv()
# --- CONFIGURATION ---
WAKE_WORD = "jarvis"
PORCUPINE_KEY = os.getenv("PORCUPINE_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

# --- TEXT TO SPEECH SETUP ---
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # Choose male voice (voice[0] is usually male)
engine.setProperty('rate', 175)

def talk(text):
    print("Jarvis:", text)
    engine.say(text)
    engine.runAndWait()

# --- GUI SETUP ---
class JarvisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JARVIS AI")
        self.root.geometry("500x300")
        self.root.configure(bg="#0f0f0f")

        self.title = ttk.Label(root, text="JARVIS Online", font=("Orbitron", 24), background="#0f0f0f", foreground="#00ffff")
        self.title.pack(pady=20)

        self.status = ttk.Label(root, text="Waiting for wake word...", font=("Consolas", 14), background="#0f0f0f", foreground="#ffffff")
        self.status.pack(pady=10)

        self.response = tk.Text(root, wrap=tk.WORD, bg="#101010", fg="#00ff99", font=("Consolas", 12), height=6, width=50)
        self.response.pack(pady=10)

    def update_status(self, text):
        self.status.config(text=text)

    def show_response(self, text):
        self.response.delete(1.0, tk.END)
        self.response.insert(tk.END, text)

# --- WHISPER ONLINE TRANSCRIPTION ---
def transcribe_audio():
    fs = 16000
    duration = 5
    print("🎤 Listening for command...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as f:
            wavfile.write(f.name, fs, recording)
            print(f"[DEBUG] Audio saved at: {f.name}")
            audio_file = open(f.name, "rb")
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
            print(f"[DEBUG] Transcript: {transcript['text']}")
            return transcript['text']
    except Exception as e:
        print(f"❌ Whisper transcription failed: {e}")
        return ""

# --- CHATGPT PROCESSING ---
def handle_command(text):
    print("User:", text)
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are JARVIS, Tony Stark's smart assistant."},
                {"role": "user", "content": text}
            ]
        )
        reply = response.choices[0].message.content
        return reply
    except Exception as e:
        return f"Sorry, I couldn't process that. Error: {e}"

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
                command = transcribe_audio()
                gui.update_status("🧠 Processing...")
                response = handle_command(command)
                gui.show_response(response)
                talk(response)
            except Exception as e:
                gui.update_status("Error processing request.")
                talk("There was an error. Please try again.")
            finally:
                gui.update_status("Waiting for wake word...")

# --- MAIN ENTRY POINT ---
if __name__ == '__main__':
    root = tk.Tk()
    gui = JarvisGUI(root)
    threading.Thread(target=start_hotword_detection, args=(gui,), daemon=True).start()
    root.mainloop()
