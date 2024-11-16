# AI Affective Music Generation System

A system that generates music based on emotional states detected from EEG signals and evaluates the musical output using emotion detection models.

## Overview

The system operates in three main steps:
1. Read EEG data to estimate emotional state (valence and arousal)
2. Generate music based on valence and arousal
3. Evaluate generated music using pre-trained emotion detection models


### 1. Emotion Detection (EEG)
- Uses MUSE headset with [muse-lsl](https://github.com/alexandrebarachant/muse-lsl) for brain signal processing
- TODO: Implement EEG signal processing to extract alpha and beta waves

### 2. Music Generation

- Rule based chord progression generator with emotion-based parameters
- Real-time Ableton Live control via OSC
- Every 16 beats, it generates a new chord progression based on valence and arousal.
- Continuosly control parameter of ableton tracks based on valence and arousal.
- TODO: Fix missing chords in progression generation

#### In Details
Track 1 (piano): mapping emotions to macro params of ableton. What else we got?
Track 2 (arpeggiator): Control arp rate based on arousal, this for rhythm!; Control dry/wet of saturator based of inverse valence
Track 3 (bass): weighted sum to control drive param
Track 4 (drums): Control frequency of filter; Note that drums is an audio clip and not midi

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

## Future Development
- Orchestrate EEG with music generation
- Global modulation system (BPM, volume based on emotions)
- Refined drum and bass generation