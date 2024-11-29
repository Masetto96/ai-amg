import random
import json
from typing import List
from dataclasses import dataclass

@dataclass
class ChordEvent:
    notes: List[int] # MIDI notes
    # TODO: add mode and tonal midi note
    duration: int # Duration in beats (assuming 4/4 time)
    velocity: float # MIDI velocity (0-1)

class ChordProgressionGenerator:
    def __init__(self):
        self.mode_intervals = self._load_mode_intervals()
        self.circle = CircleOfFifthsFourths()
        self.current_chord = "C"

    def _load_mode_intervals(self):
        with open('music_gen/mode_intervals.json', 'r') as file:
            return json.load(file)

    def generate_next_chord(self, valence, arousal) -> str:
        steps = max(0, min(3, int(arousal * 3))) # TODO: review this
        direction = random.choice(['fifths', 'fourths'])
        self.current_chord, tonal_midi_note = self.circle.navigate_circle(self.current_chord, steps, direction)
        mode, chord_notes = self._get_chord_mode(valence)
        print(f"Mode: {mode}, tonal center: {self.current_chord}")
        velocity = self._compute_velocity(arousal)
        pitch = self._compute_pitch(valence)
        chord_event = self._construct_chord(tonal_midi_note, chord_notes, velocity, pitch)
        return chord_event, tonal_midi_note

    def _construct_chord(self, tonal_midi, chord_indexes, velocity, pitch:int):
        chord_midi_notes = [tonal_midi + note for note in chord_indexes]
        return ChordEvent(notes=chord_midi_notes+pitch, duration=8, velocity=velocity) # TODO where is voice leading? :(
          
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
        return 12 if valence > 0.75 else -12 if valence < 0.35 else 0

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
        'F♯/G♭': 66,
        'G': 67,
        'G♯/A♭': 68,
        'A': 69,
        'A♯/B♭': 70,
        'B': 71
    }
        
        # Circle of fourths (counterclockwise) - reverse of fifths
        self.fourth_order = self.fifth_order[::-1]
    
    def _to_midi_pitch(self, note:str) -> int:
        return self.note_to_midi[note]
    
    def navigate_circle(self, start_note, steps:int, direction='fifths'):
        """
        Navigate around the circle of fifths or fourths.
        
        :param start_note: Starting note on the circle
        :param steps: Number of steps to move (can be float)
        :param direction: 'fifths' (clockwise) or 'fourths' (counterclockwise)
        :return: Destination note as midi pitch and note name (e.g. 60 is 'C')
        """
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
        
        return self._to_midi_pitch(current_circle[dest_index]), current_circle[dest_index]