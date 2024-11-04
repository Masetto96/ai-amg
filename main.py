import numpy as np
import soundcard as sc

from essentia.standard import MonoLoader, TensorflowPredictMusiCNN, TensorflowPredict2D, MonoMixer

if __name__ == "__main__":
    loopback_device = sc.all_microphones(include_loopback=True)[1]
    embedding_model = TensorflowPredictMusiCNN(graphFilename="model_weights/msd-musicnn-1.pb", output="model/dense/BiasAdd")
    prediction_model = TensorflowPredict2D(graphFilename="model_weights/deam-msd-musicnn-2.pb", output="model/Identity")
    mono_mixer = MonoMixer()
    try:
        with loopback_device.recorder(samplerate=16000) as mic:
            print("Recording... Press Ctrl+C to stop.")
            while True:
                audio_data = mic.record(numframes=4056)
                audio_mono = mono_mixer(audio_data, 1) # TODO: something goes wrong here! =(
                embed = embedding_model(audio_mono)
                foo = prediction_model(embed)
                print(foo)

    except KeyboardInterrupt:
        print("\nRecording stopped gracefully.")



