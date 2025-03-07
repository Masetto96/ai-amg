import random
import numpy as np

# from unittest.mock import patch
import pytest
from music_gen.generator import MetaGenerator, ChordEvent


@pytest.fixture
def meta_generator():
    return MetaGenerator()


def test_compute_velocity_range(meta_generator):
    """Test that velocity always stays within valid MIDI range (50-127)"""
    for _ in range(100):  # Test multiple random values
        velocity = meta_generator._compute_velocity(arousal=random.random())
        assert 50 <= velocity <= 127


def test_generate_next_event(meta_generator):
    """Test event generation with high arousal/valence"""
    valence, arousal = 0.8, 0.9

    chord_event, *_ = meta_generator.generate_next_events(valence, arousal)

    assert chord_event is not None
    assert isinstance(chord_event[0], ChordEvent)
    assert isinstance(chord_event[1], ChordEvent)


# # ordered from most positive to most negative
IDX_TO_MODE = [
    "lydian",
    "ionian",
    "mixolydian",
    "dorian",
    "aeolian",
    "phrygian",
]
# Valence ranges:
# 0.83-1.00: lydian
# 0.78-0.83: ionian
# 0.64-0.78: mixolydian
# 0.32-0.64: dorian
# 0.16-0.32: aeolian
# 0.00-0.16: phrygian


def test_get_mode_real_data(meta_generator):
    """Test mode selection with real mode data"""
    # Test happy/high valence (lydian)
    chords_midi_notes, midi_note, mode_name = meta_generator._get_mode_data(1)
    # assert isinstance(chords_midi_notes[0], np.ndarray)
    assert mode_name == "lydian"
    # assert len(intervals) == 7  # All modes should have 7 intervals

    chords_midi_notes, midi_note, mode_name = meta_generator._get_mode_data(0.79)
    # assert isinstance(chords_midi_notes, np.ndarray)
    assert mode_name == "ionian"
    # assert np.array_equal(intervals, [0, 2, 4, 5, 7, 9, 11])
    # assert len(intervals) == 7  # All modes should have 7 intervals

    chords_midi_notes, midi_note, mode_name = meta_generator._get_mode_data(0.6)
    assert mode_name == "mixolydian"

    chords_midi_notes, midi_note, mode_name = meta_generator._get_mode_data(0.4)
    assert mode_name == "dorian"

    chords_midi_notes, midi_note, mode_name = meta_generator._get_mode_data(0.2)
    # assert isinstance(intervals, np.ndarray)
    assert mode_name == "aeolian"
    # assert intervals[0] == 0  # Tonic should always be 0

    # Test sad/low valence (phrygian)
    chords_midi_notes, midi_note, mode_name = meta_generator._get_mode_data(0)
    # assert isinstance(intervals, np.ndarray)
    assert mode_name == "phrygian"


def test_generate_modal_midi_vamp(meta_generator):
    """Test the generation of modal MIDI vamp"""
    vamp_midi_chords = [np.array([60, 64, 67]), np.array([62, 65, 69])]
    midi_tonal_center = 60
    velocity = 100

    chord_events = meta_generator._generate_modal_midi_vamp(vamp_midi_chords, midi_tonal_center, velocity)

    assert len(chord_events) == 2
    assert all(isinstance(event, ChordEvent) for event in chord_events)
    assert all(event.velocity == velocity for event in chord_events)
    assert all(event.root == midi_tonal_center for event in chord_events)
    assert all(event.duration == 4 for event in chord_events)
    assert np.array_equal(chord_events[0].notes, vamp_midi_chords[0])
    assert np.array_equal(chord_events[1].notes, vamp_midi_chords[1])
