# AI Affective Music Generation System

A system that generates music based on emotional states detected from EEG signals and evaluates the musical output using emotion detection models.

## Overview

The system operates in three main steps:
1. Read EEG data to estimate emotional state (valence and arousal)
2. Generate music based on valence and arousal
3. Evaluate generated music using pre-trained emotion detection models


### 1. Emotion Detection (EEG)
- Uses MUSE headset with [muse-lsl](https://github.com/alexandrebarachant/muse-lsl) for brain signal processing
#### Available neuro metrics
- **Alpha/Theta Protocol**: is another popular neurofeedback metric for stress reduction -- higher theta over alpha is supposedly associated with reduced anxiety
- **Rafa Ramirez Protocol**: the beta/alpha ratio is a reasonable indicator of the arousal level
- **Beta Protocol**: beta waves have been used as a measure of mental activity and concentration -- this beta over theta ratio is commonly used as neurofeedback for ADHD
- **Alpha Protocol**: Simple redout of alpha power, divided by delta waves in order to rule out noise -- relaxation

### 2. Music Generation
- Rule based chord progression generator with emotion-based parameters
- Real-time Ableton Live control via [AbletonOSC](https://github.com/ideoforms/AbletonOSC)
- Every 16 beats, it generates a new chord progression based on valence and arousal.
- Continuosly control parameter of ableton tracks based on valence and arousal.

#### In Details
- Track 1 (piano): mapping emotions to macro params of ableton. What else we got?
- Track 2 (arpeggiator): Control arp rate based on arousal, this for rhythm!; Control dry/wet of saturator based of inverse valence

### 3. Music Evaluation
- Uses [Essentia Valence and Arousal Model](https://essentia.upf.edu/models.html#arousal-valence-deam)
- Captures system audio using [SoundCard](https://pypi.org/project/SoundCard/)
- Real-time emotion detection from generated music

## Installation

```bash
pip install -r requirements.txt
```

## Usage
Connect MUSE headset:
```bash
# List available devices
muselsl list

# Start streaming
muselsl stream --address <address>
```

## Troubleshooting

For real-time Essentia predictions debugging, refer to [this tutorial](https://essentia.upf.edu/tutorial_tensorflow_real-time_auto-tagging.html)

## Future Development (TODOs:)
- Improve the way clips are created and launched 
- Figure out the appropriate scaling for neuro metrics
- Improve chord progression:
    - Use suspended chords for neutral valence 
- Compute neuro metrics corresponding to valence, that is the brain activity asymmetry
- Refine and improve sonification:
    - Cherry pick best instruments from Ableton
- Add function to modulate more parameters:
    - global params like tempo
    - volume of individual tracks