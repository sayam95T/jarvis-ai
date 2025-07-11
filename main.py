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
import os
from dotenv import load_dotenv
load_dotenv()

# --- CONFIGURATION ---
WAKE_WORD = "jarvis"
PORCUPINE_KEY = os.getenv("PORCUPINE_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- TEXT TO SPEECH SETUP ---
import asyncio
import edge_tts
import threading
import simpleaudio as sa
import speech_recognition as sr
import time
import os

VOICE = "en-US-GuyNeural"  # Natural male voice
interrupt_words = ["stop", "cancel", "enough", "shut up"]
interrupted = False
play_obj = None

def listen_for_interrupt():
    global interrupted
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
            command = recognizer.recognize_google(audio).lower()
            if any(word in command for word in interrupt_words):
                interrupted = True
        except:
            pass

async def generate_tts(text, filename="jarvis_output.mp3"):
    communicate = edge_tts.Communicate(text=text, voice=VOICE)
    await communicate.save(filename)

def talk(text):
    global interrupted, play_obj
    interrupted = False
    print("Jarvis:", text)

    # Step 1: Generate TTS
    asyncio.run(generate_tts(text))

    # Step 2: Play sound in a thread
    def play_audio():
        global play_obj
        wave_obj = sa.WaveObject.from_wave_file("jarvis_output.mp3")
        play_obj = wave_obj.play()
        while play_obj.is_playing():
            if interrupted:
                play_obj.stop()
                print("[Jarvis] Speech interrupted.")
                break
            time.sleep(0.1)

    # Step 3: Start threads
    audio_thread = threading.Thread(target=play_audio)
    interrupt_thread = threading.Thread(target=listen_for_interrupt)

    interrupt_thread.start()
    audio_thread.start()

    interrupt_thread.join()
    audio_thread.join()



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
            {"role": "system", "content": "You are JARVIS, Tony Stark's smart assistant."},
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
