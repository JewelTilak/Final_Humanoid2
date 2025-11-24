import serial
import time
import subprocess
from pathlib import Path

port = "/dev/ttyUSB0"   # change if needed


PIPER_MODEL = "voices/en_US-libritts-medium.onnx"   # this is good
# PIPER_MODEL = "voices/en_GB-jenny_dioco-medium.onnx" # THIS IS GOOD TOO BUT IT STUTTERS AT TIMES
OUTPUT_WAV = "piper_output.wav"



# def speak(path):
#     try:
#         subprocess.run(["aplay", path])
#     except Exception as e:
#         print("Audio Error:", e)

# aa = "1p_.wav"
# bb = "2p_.wav"
# cc = "3p_.wav"
# dd = "4p_.wav"
# ee = "5p_.wav"

def speak(text):
    cmd = [
        "piper",
        "--model", PIPER_MODEL,
        "--output_file", OUTPUT_WAV,
        "--sentence_silence", "0.4" 
    ]

    try:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        p.communicate(text.encode("utf-8"))  
    except Exception as e:
        print("Piper Error:", e)
        return

    subprocess.run(["aplay", OUTPUT_WAV])

aa = (
    "Greetings, everyone! "
    "Before my friend here says more, let me show you something special. "
    "These brilliant minds standing before you are the reason I exist. "
    "They gave me purpose, they gave me presence, "
    "and they shaped every part of who I am. "
    "Please enjoy this short video that captures my journey of creation."
)

bb = (
    " I am thrilled to be here, one of the most innovative and prestigious Schools."
)

cc = (
    "For now they have taught me to recognise faces, move, dance and communicate."
    "But what i cherish most is the compassion and creativity they have built into me."
)

dd = ("We both work on the same lines" 
"Same Logic"
"Same Processing"
"Same Output behaviour")

ee = (
    " of course. Now that I declare Blitzing 2025 open…"
"Will someone get me those dandiya sticks?"
"I’m all set to dance!"
)

ser = serial.Serial(port, 115200, timeout=1)
time.sleep(2)
print("Listening for ESP32...")
while True:
    raw = ser.readline()

    if not raw:
        continue

    data = ''.join(chr(b) for b in raw if 32 <= b <= 126).strip()

    if not data:
        continue

    print("Received:", data)

    if data == "16":
        print("Received 16→ Speaking: Hello")
        speak(aa)

    elif data == "17":
        print("Received 17 → Speaking full message")
        speak(bb)

    elif data == "18":
        print("Received 18 → Speaking Three")
        speak(cc)
    
    elif data == "19":
        print("Received 19 → Speaking Four")
        speak(dd)

    elif data == "20":
        print("Received 20 → Speaking Five")
        speak(ee)