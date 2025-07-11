# JARVIS AI - Voice Assistant with Wake Word, Hugging Face API, and GUI

import pvporcupine
import pyaudio
import struct
import requests
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
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_TOKEN")
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.1"

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
    print("🎙️ Listening for 5 seconds...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            filepath = f.name
            wavfile.write(filepath, fs, recording)

        with open(filepath, "rb") as audio_file:
            headers = {
                "Authorization":"Bearer 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"
            }
            files = {
                "file": audio_file
            }
            print("📤 Sending audio to Hugging Face...")
            response = requests.post(
                "https://api-inference.huggingface.co/models/openai/whisper-large-v2",
                headers=headers,
                files=files
            )

            print("📥 Response Status:", response.status_code)
            print("📥 Raw Response:", response.text)

            result = response.json()
            if "text" in result:
                return result["text"].strip()
            elif "error" in result:
                return f"Error from Hugging Face: {result['error']}"
            else:
                return "Unknown response format."

    except Exception as e:
        print("❌ Exception during transcription:", str(e))
        return f"Exception occurred: {str(e)}"

    finally:
        # Clean up the temp file manually since delete=False
        try:
            os.remove(filepath)
        except:
            pass



# --- HUGGING FACE CHAT COMPLETION ---
def handle_command(text):
    print("User:", text)
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": f"[INST] {text} [/INST]",
        "options": {"use_cache": True}
    }
    try:
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{HF_MODEL}",
            headers=headers,
            json=payload
        )
        result = response.json()

        if isinstance(result, dict) and "error" in result:
            print("HF Error:", result["error"])
            return f"Hugging Face Error: {result['error']}"

        if isinstance(result, list):
            return result[0].get("generated_text", "Sorry, I couldn't process that.")

        return "Unexpected response format."
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
                if not command:
                    gui.update_status("Didn't catch that. Please try again.")
                    talk("I didn't catch that. Please try again.")
                    continue
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
