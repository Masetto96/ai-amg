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
    duration: int = 4 # Duration in beats (assuming 4/4 time)

    def to_ableton_osc(self, start_time: int) -> list:
        """
        Convert the chord event to a MIDI list for Ableton OSC.
        Each note is (midi_note, start_time (in beats), duration, velocity, mute)
        Concatenates all the notes in a list to be sent to Ableton.
        """
        return [item for note in self.notes for item in (int(note), start_time, self.duration, self.velocity, 0)]
    
class MetaGenerator:
    """Generates chords and arpeggiator events based on emotional metrics"""
    def __init__(self):
        self.mode_vamp = None
        self.mode_intervals = None
        self._load_mode_data()
    
    def _load_mode_data(self):
        with open("music_gen/mode_intervals.json", "r") as f:
            self.mode_intervals = json.load(f)
            logger.debug("Loaded mode data: %s", self.mode_intervals)
        with open("music_gen/vamps.json", "r") as f:
            self.mode_vamp = json.load(f)
            logger.debug("Loaded vamp data: %s", self.mode_vamp)
    
    def generate_next_events(self, valence, arousal):
        """Move around the circle of fifths and generate a chord and arpeggiator event"""
        # compute mode, velocity and pitch based on emotional metrics
        vamp_midi_chords, midi_tonal_center, *_ = self._get_mode_data(valence)
        #TODO: review pitch and velocity computation, implement like in the paper
        # pitch = self._compute_pitch(valence)
        velocity = self._compute_velocity(arousal)
        chord_events = self._generate_modal_midi_vamp(vamp_midi_chords, midi_tonal_center, velocity)
        return chord_events

    def _generate_modal_midi_vamp(self, vamp_midi_chords, midi_tonal_center, velocity):
        """Generates a modal MIDI vamp based on the mode and tonal center"""
        chord_events = []
        for midi_chord in vamp_midi_chords:
            chord_events.append(ChordEvent(root=midi_tonal_center, notes=midi_chord, velocity=velocity))
        return chord_events

    def _get_mode_data(self, valence):
        """
        Maps valence value to a musical mode.
        Returns the mode vamp MIDI chords and MIDI tonal center for the given mode.
        
        Valence ranges:
        0.83-1.00: lydian
        0.78-0.83: ionian
        0.64-0.78: mixolydian  
        0.32-0.64: dorian
        0.16-0.32: aeolian
        0.00-0.16: phrygian
        """
        # Calculate index based on valence range (0-1)
        # Since IDX_TO_MODE is ordered from most positive to most negative,
        # and valence goes from 0 (negative) to 1 (positive),
        # we need to invert the index calculation
        index = int((1 - valence) * (len(IDX_TO_MODE) - 1))
        #TODO: review mapping from mode to valence
        # Get the mode name from the index
        mode_name = IDX_TO_MODE[index]
        logger.info("Selected mode: %s (index %d) for valence %f", mode_name, index, valence)
        # intervals = self.mode_intervals.get(mode_name).get("scale_degrees")
        mode_data = self.mode_vamp.get(mode_name)
        return mode_data.get("implementation"), mode_data.get("tonalcenter"), mode_name

    def _compute_pitch(self, valence) -> int:
        """This shall follow the intuition that lower tones sound negative and higher tones sound positive, right?"""
        return 12 if valence > 0.80 else -12 if valence < 0.20 else 0

    def _compute_velocity(self, arousal: float) -> int:
        #TODO: review velocity computation
        min_velocity = 50
        max_velocity = 127
        v = int(random.uniform(min_velocity, max_velocity * arousal))
        logger.debug("Arousal: %f, Computed velocity: %d", arousal, v)
        # v = min(max_velocity, v)
        return max(min_velocity, v) # making sure it's not more than 127
