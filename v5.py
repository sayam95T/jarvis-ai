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
import speech_recognition as sr
import requests

# --- CONFIGURATION ---
WAKE_WORD = "jarvis"
PORCUPINE_KEY = "r9y1jmWBCeFEDy9S9JpQPTwzFDSCAAX5hCL6EToCpCU6zVJSDhBxhQ=="
GROQ_API_KEY = "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"

# --- TEXT TO SPEECH SETUP ---
import pyttsx3

# --- TEXT TO SPEECH SETUP ---
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)  # voice[0] is usually male
engine.setProperty('rate', 175)

def talk(text):
    print("Jarvis:", text)
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[Jarvis] Error while speaking: {e}")

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

# --- ONLINE SPEECH-TO-TEXT (Google STT) ---
def transcribe_audio():
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎙️ Listening for command...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
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
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {"role": "system", "content": "You are JARVIS, Sayam's smart assistant like the movie character Tony Star had one, who gives answers in short , quick , responses."},
            {"role": "user", "content": text}
        ]
    }
    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
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
                command = transcribe_audio()
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
