import numpy as np
from essentia.standard import MonoLoader, TensorflowPredictMusiCNN, TensorflowPredict2D

class EssentiaPredictor:
    def __init__(self):
        self.embedding_model = TensorflowPredictMusiCNN(graphFilename="model_weights/msd-musicnn-1.pb", output="model/dense/BiasAdd")
        self.prediction_model = TensorflowPredict2D(graphFilename="model_weights/deam-msd-musicnn-2.pb", output="model/Identity")
    def predict(self, file_path):
        # TODO: suppress the annoying warning
        audio = MonoLoader(filename=file_path, sampleRate=16000, resampleQuality=4)()
        embeddings = self.embedding_model(audio)
        predictions = self.prediction_model(embeddings)
        return np.mean(predictions, axis=0)

if __name__ == "__main__":
    predictor = EssentiaPredictor()
    audio_stream = np.random.rand(16000)
    out = predictor.predict("sample.mp3")
    valence = out[0]
    arousal = out[1]
    print(f"valence: {valence}")
    print(f"arousal: {arousal}")