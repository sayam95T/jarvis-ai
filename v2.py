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
import openai
ACCESS_KEY='r9y1jmWBCeFEDy9S9JpQPTwzFDSCAAX5hCL6EToCpCU6zVJSDhBxhQ=='
openai.api_key='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'
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

    if command:
        try:
            print("Sending to ChatGPT...")
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # or "gpt-4" if you have access
                messages=[
                    {"role": "system", "content": "You are Jarvis, a helpful voice AI assistant."},
                    {"role": "user", "content": command}
                ],
                max_tokens=100,
                temperature=0.7
            )

            reply = response['choices'][0]['message']['content'].strip()
            print("Jarvis:", reply)
            talk(reply)

        except Exception as e:
            print("Error with OpenAI:", e)
            talk("Sorry, I couldn't process that.")


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
