# AI Affective Music Generation System

A system that generates music based on emotional states detected from EEG signals and evaluates the musical output using emotion detection models.

## Overview

The system operates in three main steps:
1. Read EEG data to estimate emotional state (valence and arousal)
2. Generate music based on valence and arousal
3. Evaluate generated music using pre-trained emotion detection models

### 1. Emotion Detection from EEG
- MUSE headset - [muse-lsl](https://github.com/alexandrebarachant/muse-lsl) for brain signal processing
#### Available neuro metrics
- **Alpha/Theta Protocol**: is another popular neurofeedback metric for stress reduction -- higher theta over alpha is supposedly associated with reduced anxiety
- **Rafa Ramirez Protocol**: the beta/alpha ratio is a reasonable indicator of the arousal level
- **Beta Protocol**: beta waves have been used as a measure of mental activity and concentration -- this beta over theta ratio is commonly used as neurofeedback for ADHD
- **Alpha Protocol**: Simple redout of alpha power, divided by delta waves in order to rule out noise -- relaxation

### 2. Music Generation
- Chord generation based on valence & navigating the circle of fifths based on arousal
- Real-time Ableton Live control via [AbletonOSC](https://github.com/ideoforms/AbletonOSC)
- Continuosly control parameter of ableton tracks based on valence and arousal

### 3. Music Evaluation
- Uses [Essentia Valence and Arousal Model](https://essentia.upf.edu/models.html#arousal-valence-deam)
- Captures system audio using [SoundCard](https://pypi.org/project/SoundCard/)
- Real-time emotion detection from generated music

## Installation

```bash
pip install -r requirements.txt
```

## Usage
Start music neuro feedback
```bash
chmod +x start_music_nf.sh
./start_muse_stream.sh
```

## Troubleshooting
For real-time Essentia predictions debugging, refer to [this tutorial](https://essentia.upf.edu/tutorial_tensorflow_real-time_auto-tagging.html)

## Future Development (TODOs:)
### Emotion Detection
- Compute neuro metrics corresponding to valence, that is the brain activity asymmetry.

### Music Generation
- Refine and improve sonification:
    - Cherry pick best instruments from Ableton

### Evaluation    
- Implement evaluation with essentia models

## Ideas
- Find alternatives to extract valence and arousal from EEG (*for later*)
- Use suspended chords for neutral valence 
- Experiment with launching clips rather than deleting notes and adding new one