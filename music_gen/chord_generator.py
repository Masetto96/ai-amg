import random
import json
from dataclasses import dataclass
import numpy as np
from typing import List

@dataclass
class ChordEvent:
    """Represents a chord"""
    # TODO: add mode name
    notes: np.array # MIDI notes of the chord
    root: int # MIDI note of the root
    velocity: float # MIDI velocity (0-127)
    duration: int = 8 # Duration in beats (assuming 4/4 time)

    def to_ableton_osc(self, start_time: int) -> list:
        """
        Convert the chord event to a MIDI list for Ableton OSC.
        Each note is (midi_note, start_time (in beats), duration, velocity, mute)
        Adds all the notes in a list to be sent to Ableton.
        """
        return [item for note in self.notes for item in (int(note), start_time, self.duration, self.velocity, 0)]


class ChordGenerator:
    def __init__(self):
        self.mode_intervals = self._load_mode_intervals()
        self.circle = CircleOfFifthsFourths()
        self.current_chord = "C"
        self.index_to_mode = [
            "lydian",
            "ionian",
            "mixolydian",
            "dorian",
            "aeolian",
            "phrygian",
            "locrian"
        ]

    def _load_mode_intervals(self):
        with open('music_gen/mode_intervals.json', 'r') as file:
            return json.load(file)

    def generate_next_chord(self, valence, arousal) -> str:
        """Generate the next chord based on the valence and arousal"""
        steps = 0 if random.random() < (1 - arousal) else random.choice([1, 2, 3])
        direction = random.choice(['fifths', 'fourths'])
        self.current_chord, tonal_midi_note = self.circle.navigate_circle(self.current_chord, steps, direction)
        mode_intervals = self._get_mode(valence)
        print(f"Mode intervals: {mode_intervals}, tonal center: {self.current_chord} \n")
        velocity = self._compute_velocity(arousal)
        pitch = self._compute_pitch(valence)
        chord_event = self._construct_chord(int(tonal_midi_note), mode_intervals, velocity, pitch)
        return chord_event

    def _construct_chord(self, tonal_midi:int, mode_intervals, velocity, pitch_shift:int):
        idx_intervals = [0, 2, 4, 6]
        # get the 1st, 3rd, 5th, 7th degrees from the mode intervals to create the chord
        chord_notes = mode_intervals[idx_intervals]
        # turn that to midi notes by adding midi tonal center (e.g. C = 60) and adding pitch shift amount in semitones
        chord_midi_notes = chord_notes + tonal_midi + pitch_shift
        return ChordEvent(notes=chord_midi_notes, duration=8, velocity=velocity, root=tonal_midi) # TODO where is voice leading? :(
          
    def _get_mode(self, valence):
        # Determine the mode index based on valence
        mode_idx = int(7 - (6 * valence)) - 1 # minus 1 to convert to 0-based index
        mode_name = self.index_to_mode[mode_idx]
        print(f"Current mode: {mode_name}")
        mode_intervals = self.mode_intervals[mode_name]  # Get the mode intervals
        return np.array(mode_intervals)

    def _compute_pitch(self, valence) -> int:
        return 12 if valence > 0.80 else -12 if valence < 0.20 else 0

    def _compute_velocity(self, arousal: float) -> int:
        v = random.uniform(50, 40 * arousal + 60)
        return max(50, min(127, int(v)))

class CircleOfFifthsFourths:
    def __init__(self):
        # Standard circle of fifths (clockwise)
        self.fifth_order = [
            'C', 'G', 'D', 'A', 'E', 'B', 'F♯/G♭', 'C♯/D♭', 
            'G♯/A♭', 'D♯/E♭', 'A♯/B♭', 'F'
        ]
        self.note_to_midi = {
        'C': 60,
        'C♯/D♭': 61,
        'D': 62,
        'D♯/E♭': 63,
        'E': 64,
        'F': 65,
        'F♯/G♭': 54,
        'G': 55,
        'G♯/A♭': 56,
        'A': 57,
        'A♯/B♭': 58,
        'B': 59
    }
              
        # Circle of fourths (counterclockwise) - reverse of fifths
        self.fourth_order = self.fifth_order[::-1]
   
    def _to_midi_pitch(self, note:str) -> int:
        return self.note_to_midi[note]
   
    def navigate_circle(self, start_note, steps:int, direction='fifths'):
        """Returns next notal center and its MIDI pitch based on the start note and steps"""
        # Select the appropriate circle based on direction
        current_circle = self.fifth_order if direction == 'fifths' else self.fourth_order      
        # Find the index of the start note
        try:
            start_index = current_circle.index(start_note)
        except ValueError:
            raise ValueError(f"Note {start_note} not found in the circle")       
        # Calculate the destination index
        # Use modulo to wrap around the circle
        dest_index = int(round((start_index + steps) % len(current_circle)))    
        return current_circle[dest_index], self._to_midi_pitch(current_circle[dest_index])