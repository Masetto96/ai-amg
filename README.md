# AI affective music generation system

1. Read in data from eeg and estimate emotional state (valence and arousal)
2. Generate music based on valence and arousal
3. Evaluate the generated music using a pre-trained model which computes valence and arousal values


## Overview
- Capture audio output from the system using [SoundCard](https://pypi.org/project/SoundCard/)
- Compute valence and arousal values using [Essentia Valence and Arousal Model](https://essentia.upf.edu/models.html#arousal-valence-deam)


## Installation

```bash
pip install -r requirements.txt
```

## TODO:
- implement eeg signal processing to extract alpha and beta waves
- implement and integrate affective music generation system with [DEAM dataset](https://cvml.unige.ch/databases/DEAM/) (or any other datasets)