import subprocess
import sounddevice as sd
import soundfile as sf
import os
from pathlib import Path


MODEL_PATH = r"voices/en_GB-jenny_dioco-medium.onnx"


OUTPUT_WAV = "Welcome.wav"


def speak(text: str):
    """Generate TTS using Piper and play it."""
    try:

        command = [
            "piper",
            "--model", MODEL_PATH,
            "--output_file", OUTPUT_WAV
        ]

        # Run Piper and feed the text
        subprocess.run(
            command,
            input=text.encode("utf-8"),
            check=True
        )

        # ----- PLAY AUDIO -----
        if os.path.exists(OUTPUT_WAV):
            data, samplerate = sf.read(OUTPUT_WAV)
            sd.play(data, samplerate)
            sd.wait()

    except Exception as e:
        print("TTS Error:", e)


if __name__ == "__main__":
    speak("Hello, Welcome to Utpal Sanghvi Global School")

