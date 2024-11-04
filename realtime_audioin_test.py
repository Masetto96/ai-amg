import soundcard as sc
import numpy as np


# List all loopback devices to choose the right one
for mic in sc.all_microphones(include_loopback=True):
    print(mic)

# Define your sample rate and buffer size... NOTE: this depends on the model we are using (check the metadata of the model)
SAMPLE_RATE = 44100  
BUFFER_SIZE = 1024   

# Capture and process the speakers loopback
loopback_device = sc.all_microphones(include_loopback=True)[1]  # Adjust the index if needed

try:
    with loopback_device.recorder(samplerate=SAMPLE_RATE) as mic:
        print("Recording... Press Ctrl+C to stop.")
        while True:
            audio_data = mic.record(numframes=BUFFER_SIZE)  # Capture audio
            print(audio_data)
            # TODO: here we can process the audio data, that is feeding it to the essentia model

except KeyboardInterrupt:
    print("\nRecording stopped gracefully.")

# Optional: Any additional cleanup can go here
