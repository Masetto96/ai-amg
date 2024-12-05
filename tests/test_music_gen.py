import random
import numpy as np
# from unittest.mock import patch
import pytest
from music_gen.generator import MetaGenerator


@pytest.fixture
def meta_generator():
    return MetaGenerator()

def test_melody_intervals_arp(meta_generator):
    k = 4
    intervals = meta_generator._generate_melody_interv("ionian", k=k)
    assert len(intervals) == k
    assert isinstance(intervals, np.ndarray)

def test_compute_velocity_range(meta_generator):
    """Test that velocity always stays within valid MIDI range (50-127)"""
    for _ in range(100):  # Test multiple random values
        velocity = meta_generator._compute_velocity(arousal=random.random())
        assert 50 <= velocity <= 127

def test_generate_next_event_high_arousal(meta_generator):
    """Test event generation with high arousal/valence"""
    valence, arousal = 0.8, 0.9
    
    chord_event, arp_event = meta_generator.generate_next_event(valence, arousal)
    
    assert chord_event is not None
    assert arp_event is not None
    # assert arp_event.velocity > 64  # Higher velocity with high arousal

def test_generate_next_event_low_arousal(meta_generator):
    """Test event generation with low arousal/valence"""
    valence, arousal = 0.2, 0.1
    
    chord_event, arp_event = meta_generator.generate_next_event(valence, arousal)
    
    assert chord_event is not None
    assert arp_event is not None
    # assert arp_event.velocity < 64  # Lower velocity with low arousal
    
# # ordered from most positive to most negative
# IDX_TO_MODE = [
#     "lydian",
#     "ionian",
#     "mixolydian",
#     "dorian",
#     "aeolian",
#     "phrygian",
# ]

# TESTING MODE DATA
def test_get_mode_real_data(meta_generator):
    """Test mode selection with real mode data"""
    # Test happy/high valence (lydian)
    intervals, mode = meta_generator._get_mode(1.0)
    assert isinstance(intervals, np.ndarray)
    assert mode == "lydian"
    assert len(intervals) == 7  # All modes should have 7 intervals

    intervals, mode = meta_generator._get_mode(0.8)
    assert isinstance(intervals, np.ndarray)
    assert mode == "ionian"
    assert np.array_equal(intervals, [0, 2, 4, 5, 7, 9, 11])
    assert len(intervals) == 7  # All modes should have 7 intervals
    
    intervals, mode = meta_generator._get_mode(0.2)
    assert isinstance(intervals, np.ndarray)
    assert mode == "aeolian"
    assert intervals[0] == 0  # Tonic should always be 0
    
    # Test sad/low valence (phrygian)
    intervals, mode = meta_generator._get_mode(0.0)
    assert isinstance(intervals, np.ndarray)
    assert mode == "phrygian"