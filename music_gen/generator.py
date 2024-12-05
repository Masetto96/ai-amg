import random
import json
import logging
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)

# ordered from most positive to most negative
IDX_TO_MODE = [
    "lydian",
    "ionian",
    "mixolydian",
    "dorian",
    "aeolian",
    "phrygian",
]

@dataclass
class ChordEvent:
    notes: np.array # MIDI notes of the event
    velocity: float # MIDI velocity (0-127)
    root: int = None # MIDI note of the root
    duration: int = 8 # Duration in beats (assuming 4/4 time)

    def to_ableton_osc(self, start_time: int) -> list:
        """
        Convert the chord event to a MIDI list for Ableton OSC.
        Each note is (midi_note, start_time (in beats), duration, velocity, mute)
        Concatenates all the notes in a list to be sent to Ableton.
        """
        return [item for note in self.notes for item in (int(note), start_time, self.duration, self.velocity, 0)]

@dataclass
class ArpeggiatorEvent(ChordEvent):
    def to_ableton_osc(self, start_time: int) -> list:
        """
        Convert the arpeggiator event to a MIDI list for Ableton OSC.
        Spreads notes evenly across 8 beats.
        Each note is (midi_note, start_time, duration, velocity, mute)
        """
        num_notes = len(self.notes)
        
        # Each note gets equal portion of total time
        note_duration = self.duration / max(num_notes, 1)
        
        return [
            item 
            for i, note in enumerate(self.notes) 
            for item in (
                int(note),                    # midi note
                start_time + i * note_duration,  # start time
                note_duration,                # duration
                self.velocity,               # velocity
                0                            # mute
            )
        ]
    
class MetaGenerator:
    """Generates chords and arpeggiator events based on emotional metrics"""
    def __init__(self):
        self.mode_data = self._load_mode_data()
        self.current_chord = "C" # to start with
        self.circle = CircleOfFifths()
    
    def _load_mode_data(self):
        with open("music_gen/modes.json", "r") as f:
            return json.load(f)
    
    def generate_next_event(self, valence, arousal):
        """Move around the circle of fifths and generate a chord and arpeggiator event"""
        # moving (randomly) around the circle 
        steps = 0 if random.random() < (1 - arousal) else random.choice([1, 2, 3])
        direction = random.choice(['fifths', 'fourths'])
        self.current_chord, tonal_midi_note = self.circle.navigate_circle(self.current_chord, steps, direction)
        # compute mode, velocity and pitch based on emotional metrics
        mode_intervals, mode_name = self._get_mode(valence)
        pitch = self._compute_pitch(valence)
        velocity = self._compute_velocity(arousal)
        chord_event = self.create_chord(tonal_midi_note, mode_intervals, velocity, pitch)
        k = int(4 + 12 * arousal) # number of notes in the arpeggiator
        arp_event = self.create_arpeggiator(tonal_midi=tonal_midi_note, mode_name=mode_name, k=k, velocity=velocity, pitch_shift=pitch)
        return chord_event, arp_event
    
    def _get_mode(self, valence):
        """Returns the mode intervals and mode name"""
        # Determine the mode index based on valence
        mode_idx = int(6 - (5 * valence)) - 1 # minus 1 to convert to 0-based index
        mode_name = IDX_TO_MODE[mode_idx]
        logger.info("Selected mode: %s for valence %f", mode_name, valence)
        mode_data = self.mode_data.get(mode_name)
        return np.array(list(mode_data.get("intervals").values())), mode_name

    def _compute_pitch(self, valence) -> int:
        return 12 if valence > 0.80 else -12 if valence < 0.20 else 0

    def _compute_velocity(self, arousal: float) -> int:
        v = random.uniform(50, 40 * arousal + 60)
        logger.debug("Arousal: %f, Computed velocity: %f", arousal, v)
        return max(50, min(127, int(v)))

    def create_chord(self, tonal_midi:int, mode_intervals, velocity:int, pitch_shift:int):
        """Returns a ChordEvent object constructed on the 1, 3, 5, 7 degrees of the mode intervals, applies pitch shift"""
        idx_intervals = [0, 2, 4, 6] # zero-indexed
        # get the 1st, 3rd, 5th, 7th degrees from the mode intervals to create the chord
        chord_intervals = mode_intervals[idx_intervals]
        # turn that to midi notes by adding midi tonal center (e.g. C = 60) and adding pitch shift amount in semitones
        chord_midi_notes = intervals_to_midi_notes(intervals=chord_intervals, midi_tonal_note=tonal_midi, pitch=pitch_shift)
        return ChordEvent(root=tonal_midi, notes=chord_midi_notes, duration=8, velocity=velocity)
    
    def create_arpeggiator(self, tonal_midi:int, mode_name:str, velocity, pitch_shift:int, k:int=4):
        """Returns an ArpeggiatorEvent note intervals are generated based on probabilities"""
        melody_intervals = self._generate_melody_interv(mode_name, k=k)
        arp_midi_notes = intervals_to_midi_notes(melody_intervals, tonal_midi, pitch_shift)
        return ArpeggiatorEvent(notes=arp_midi_notes, duration=8, velocity=velocity, root=tonal_midi)
    

    def _apply_l_system_rules(self, sequence: list, rules: dict) -> list:
        """Apply rules that can produce either single elements or sequences"""
        next_sequence = []
        logger.debug("L-System current sequence: %s", sequence)
        
        for symbol in sequence:
            if symbol in rules:
                choice = random.choice(rules[symbol])
                logger.debug("L-System rule applied: %s -> %s", symbol, choice)
                
                # Handle both single elements and sequences
                if isinstance(choice, list):
                    next_sequence.extend(choice)
                else:
                    next_sequence.append(choice)
            else:
                logger.warning("No L-System rule found for symbol: %s", symbol)
                next_sequence.append(symbol)
            
        logger.debug("L-System next sequence: %s", next_sequence)
        return next_sequence

    def _generate_melody_interv(self, mode_name:str, k: int):
        mode_data = self.mode_data.get(mode_name)
        rules = mode_data.get("rules")
        intervals = mode_data.get("intervals")
        sequence = "T" # for now we start with the tonic
        # TODO: idea for later is to randomly select the starting symbol (when rules are better defined)
        all_symbols = [intervals.get(sequence)]
        
        logger.info("Generating melody with %d iterations in %s mode", k, mode_name)
        
        for i in range(k*2): # dirty hack to make sure iterations are enough without getting stuck
            if len(all_symbols) == k:
                logger.debug("Melody generation complete with %d symbols", len(all_symbols))
                return np.array(all_symbols)
    
            sequence = self._apply_l_system_rules(sequence, rules)
            logger.debug("Iteration %d: Current sequence = %s", i, sequence)
            all_symbols.extend([intervals.get(symbol) for symbol in sequence])

        logger.debug("Final melody symbols: %s", all_symbols)
        return np.array(all_symbols)

class CircleOfFifths:
    """Class to navigate the circle of fifths and fourths"""
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

    def _to_midi_pitch(self, note: str) -> int:
        return self.note_to_midi[note]

    def navigate_circle(self, start_note, steps: int, direction='fifths'):
        """Returns next tonal center and its MIDI pitch based on the start note and steps"""
        # Select the appropriate circle based on direction
        current_circle = self.fifth_order if direction == 'fifths' else self.fourth_order
        logger.debug("Navigating %d steps %s from %s", steps, direction, start_note)      
        # Find the index of the start note
        try:
            start_index = current_circle.index(start_note)
        except ValueError:
            logger.error("Invalid note %s not found in the circle of fifths", start_note)
            raise ValueError(f"Note {start_note} not found in the circle")       
        # Calculate the destination index
        # Use modulo to wrap around the circle
        dest_index = int(round((start_index + steps) % len(current_circle)))    
        next_note = current_circle[dest_index]
        midi_pitch = self._to_midi_pitch(next_note)
        
        logger.info("Circle navigation: %s -> %s (%d steps %s)", 
                   start_note, next_note, steps, direction)
        logger.debug("Note %s has MIDI pitch %d", next_note, midi_pitch)
        return next_note, midi_pitch

def intervals_to_midi_notes(intervals:np.array, midi_tonal_note:int, pitch:int) -> np.array:
    """
    Converts a list of intervals to MIDI notes based on a tonal center and pitch shift 
    ([0, 2, 4] -> [60, 62, 64] when pitch is 0)
    """
    return midi_tonal_note + intervals + pitch
