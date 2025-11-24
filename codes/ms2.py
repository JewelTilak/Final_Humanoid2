import serial
import time
import subprocess
from pathlib import Path

port = "/dev/ttyUSB0"


def play_wav(path):
    try:
        subprocess.run(["aplay", path])
    except Exception as e:
        print("Audio Error:", e)

aa = "1p_.wav"
bb = "2p_.wav"
cc = "3p_.wav"
dd = "4p_.wav"
ee = "5p_.wav"

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

    if data == "11":
        print("Button 11 → Playing WAV 1")
        play_wav(aa)

    elif data == "12":
        print("Button 12 → Playing WAV 2")
        play_wav(bb)

    elif data == "13":
        print("Button 13 → Playing WAV 3")
        play_wav(cc)

    elif data == "14":
        print("Button 14 → Playing WAV 4")
        play_wav(dd)

    elif data == "15":
        print("Button 15 → Playing WAV 5")
        play_wav(ee)
