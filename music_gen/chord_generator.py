import random
import json
from typing import List
from dataclasses import dataclass
from circle import CircleOfFifthsFourths

@dataclass
class ChordEvent:
    notes: List[int] # MIDI notes
    duration: int # Duration in beats (assuming 4/4 time)
    velocity: float # MIDI velocity (0-1)

class ChordProgressionGenerator:
    def __init__(self):
        self.mode_intervals = self._load_mode_intervals()
        self.circle = CircleOfFifthsFourths()
        self.current_chord = "C"

    def _load_mode_intervals(self):
        with open('mode_intervals.json', 'r') as file:
            return json.load(file)

    def generate_next_chord(self, valence, arousal) -> str:
        steps = arousal * 1
        direction = 'fifths' if valence > 0 else 'fourths'
        self.current_chord, tonal_midi_note = self.circle.navigate_circle(self.current_chord, steps, direction)
        mode, chord_notes = self._get_chord_mode(valence)
        print(f"Mode: {mode}, tonal center: {self.current_chord}")
        velocity = self._compute_velocity(arousal)
        pitch = self._compute_pitch(valence)
        chord_event = self._construct_chord(tonal_midi_note, chord_notes, velocity, pitch)
        return chord_event

    def _construct_chord(self, tonal_midi, chord_indexes, velocity, pitch):
        chord_midi_notes = [tonal_midi + note for note in chord_indexes]
        return ChordEvent(notes=chord_midi_notes+pitch, duration=8, velocity=velocity)   
          
    def _get_chord_mode(self, valence):
        # Determine the mode index based on valence
        mode_idx = int(7 - (6 * valence)) - 1 # minus 1 to convert to 0-based index
        mode = self.mode_intervals[mode_idx]  # Get the mode intervals
        # Get the indexes for the chord notes
        indexes = [0, 2, 4, 6]  # 1st, 3rd, 5th, 7th degrees of the mode
        # Select the chord notes using the specified indexes
        chord_notes = [mode[i] for i in indexes]
        return mode, chord_notes

    def _compute_pitch(self, valence) -> int:
        """It should transpose octave up or down based on valence"""
        #TODO: do pitch based on paper computation
        return 0

    def _compute_velocity(self, arousal: float) -> int:
        v = random.uniform(50, 40 * arousal + 60) # this is the formula in the paper
        return int(v) # TODO shall it be clamped between 50 and 120?
