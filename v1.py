import tkinter as tk
from tkinter import Label
import threading
import pyttsx3
import datetime
import os
import pvporcupine
import pyaudio
import struct
import json
import vosk
import queue
import sounddevice as sd
import os
from dotenv import load_dotenv

load_dotenv()
ACCESS_KEY=os.getenv("PORCUPINE_KEY")
# --- Offline TTS ---
engine = pyttsx3.init()
voices = engine.getProperty('voices')

# Try setting to male voice
for voice in voices:
    if "male" in voice.name.lower() or "david" in voice.name.lower():  # 'David' is common male voice on Windows
        engine.setProperty('voice', voice.id)
        break



def talk(text):
    update_status("Speaking...")
    print("Jarvis:", text)
    engine.say(text)
    engine.runAndWait()
    update_status("Waiting for Hotword...")

# --- Offline Speech Recognition with VOSK ---
model = vosk.Model("model")
q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status)
    q.put(bytes(indata))

def listen():
    update_status("Listening...")
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        rec = vosk.KaldiRecognizer(model, 16000)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                command = result.get("text", "")
                if command:
                    print("You:", command)
                    return command.lower()

# --- Basic Command Handling ---
def run_jarvis():
    command = listen()
    if "time" in command:
        now = datetime.datetime.now().strftime("%I:%M %p")
        talk(f"The time is {now}")
    elif "stop" in command or "exit" in command:
        talk("Goodbye!")
        root.quit()
    elif "hello" in command:
        talk("Hello! How can I help?")
    elif "ronaldo" in command:
        talk("Number 1 footballer in the world - SIUUUUUUUUUU")
    else:
        talk("I didn't understand that yet.")


# --- Hotword Detection ---
def start_hotword_detection():
    porcupine = pvporcupine.create(access_key=ACCESS_KEY,keywords=["jarvis"])
    pa = pyaudio.PyAudio()
    stream = pa.open(format=pyaudio.paInt16,
                     channels=1,
                     rate=porcupine.sample_rate,
                     input=True,
                     frames_per_buffer=porcupine.frame_length)

    update_status("Waiting for Hotword...")

    while True:
        pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
        result = porcupine.process(pcm)

        if result >= 0:
            talk("Yes boss?")
            run_jarvis()

# --- GUI ---
root = tk.Tk()
root.title("Jarvis AI (Optimized)")
root.geometry("400x200")
root.resizable(False, False)

status_label = Label(root, text="Initializing...", font=("Helvetica", 14))
status_label.pack(pady=20)

def update_status(text):
    status_label.config(text=text)

# --- Launch in Thread ---
threading.Thread(target=start_hotword_detection, daemon=True).start()

update_status("Booting up...")
root.mainloop()
