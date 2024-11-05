# AI affective music generation system

1. Read in data from eeg and estimate emotional state (valence and arousal)
2. Generate music based on valence and arousal
3. Evaluate the generated music using a pre-trained model which computes valence and arousal values


## Overview
- Capture audio output from the system using [SoundCard](https://pypi.org/project/SoundCard/)
- Compute valence and arousal values using [Essentia Valence and Arousal Model](https://essentia.upf.edu/models.html#arousal-valence-deam)
- Connecting MUSE headset to python using [muse-lsl](https://github.com/alexandrebarachant/muse-lsl)


## Installation

```bash
pip install -r requirements.txt
```


## Usage
To view all avaliable muse devices to connect:
```bash
muselsl list
```

To start streaming eeg data:
```bash
muselsl stream --address <address> 
```



## TODO:
- implement eeg signal processing to extract alpha and beta waves, following [this](https://github.com/alexandrebarachant/muse-lsl/blob/master/examples/neurofeedback.py) & using the formulas from the liteature
- implement affective music generation system which receives valence and arousal as input


## Troubleshooting
- To debug the real-time predictions with essentia, refer to [this](https://essentia.upf.edu/tutorial_tensorflow_real-time_auto-tagging.html); Note that we dont need to use the spectrogram!
