import json
import random
import os
from typing import List
from chord_generator import ChordEvent


# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to the JSON file
mapping_path = os.path.join(script_dir, "chord_mapping.json")

# Load JSON data from the file
with open(mapping_path, "r") as file:
    CHORD_MAPPING = json.load(file)


def chord_to_midi(chord_events: List[ChordEvent], include_third=True):
    """
    Convert a list of ChordEvent objects into MIDI note events, including a bass line.

    Args:
        chord_events: List of ChordEvent objects.
        include_third: Boolean indicating whether to include the third in the bass line.

    Returns:
        Tuple of two lists:
        - List of MIDI note tuples for chords in the format:
          (pitch, start_time, duration, velocity, mute)
        - List of MIDI note tuples for bass line in the same format.
    """
    midi_notes = []  # For chord notes
    bass_line = []  # For bass line
    current_time = 0.0  # Start time in beats

    for event in chord_events:
        chord_pitches = CHORD_MAPPING.get(event.chord, [])
        tonic = (
            chord_pitches[0] if chord_pitches else None
        )  # Assume the tonic is the first pitch
        third = (
            chord_pitches[1] if len(chord_pitches) > 1 else None
        )  # Assume the third is the second pitch

        # Generate chord notes
        for pitch in chord_pitches:
            variation = random.uniform(
                -20, 20
            )  # Add velocity variation for each note in the chord
            new_velocity = int(event.velocity + variation)
            midi_notes.append(
                (pitch, current_time, event.duration, new_velocity, 0)
            )  # Mute=0 for now

        # Generate bass line notes
        if tonic is not None:
            bass_line.append(
                (tonic - 12, current_time, event.duration, event.velocity, 0)
            )  # Add tonic to bass line, transpose by 12 semitones
        if include_third and third is not None:
            bass_line.append(
                (third - 12, current_time, event.duration, event.velocity, 0)
            )  # Add third to bass line if requested

        current_time += event.duration

    return midi_notes, bass_line


def transpose_midi_chords(midi_notes, transpose_amount):
    """
    Transpose a list of MIDI note events by a specified amount.

    Args:
        midi_notes: List of MIDI note tuples in the format:
                    (pitch, start_time, duration, velocity, mute)
        transpose_amount: Integer value to transpose the notes by.

    Returns:
        List of transposed MIDI note tuples.
    """
    transposed_notes = []
    for pitch, start_time, duration, velocity, mute in midi_notes:
        transposed_pitch = pitch + transpose_amount
        transposed_notes.append(
            (transposed_pitch, start_time, duration, velocity, mute)
        )
    return transposed_notes


def compute_weighted_average(
    valence,
    arousal,
    weight_valence=0.5,
    weight_arousal=0.5,
    method="weighted_average",
    output_range=(0, 127),
):
    """
    Some beautiful machine code ahah

    Calculate a distortion value based on valence and arousal.

    Parameters:
        valence (float): Valence value in the range [-1, 1].
        arousal (float): Arousal value in the range [-1, 1].
        weight_valence (float): Weight for valence (default 0.5).
        weight_arousal (float): Weight for arousal (default 0.5).
        output_range (tuple): Desired output range as (min, max).

    Returns:
        int: Distortion value in the specified output range.
    """
    # Normalize to [0, 2]
    valence_mapped = valence + 1
    arousal_mapped = arousal + 1

    # Combine valence and arousal based on the selected method
    combined = weight_valence * valence_mapped + weight_arousal * arousal_mapped

    # Map combined value to the specified output range
    min_out, max_out = output_range
    scale_factor = max_out - min_out
    distortion = (
        min_out + (combined / 2) * scale_factor
    )  # Normalized combined is in [0, 2]

    # Ensure within the specified range
    return int(min(max(distortion, min_out), max_out))
