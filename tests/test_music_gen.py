import pytest
import random
from music_gen.chord_generator import MetaGenerator
from unittest.mock import patch


@pytest.fixture
def meta_generator():
    return MetaGenerator()

@pytest.mark.parametrize("arousal,mock_value,expected", [
    (0.0, 50, 50),  # Minimum case
    (1.0, 100, 100),  # High arousal
    (0.5, 80, 80),  # Medium arousal
    (1.0, 130, 127),  # Test upper limit capping
    (0.0, 45, 50),  # Test lower limit capping
])
def test_compute_velocity(meta_generator, arousal, mock_value, expected):
    with patch('random.uniform', return_value=mock_value):
        velocity = meta_generator._compute_velocity(arousal)
        assert velocity == expected

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
    assert arp_event.velocity > 64  # Higher velocity with high arousal

def test_generate_next_event_low_arousal(meta_generator):
    """Test event generation with low arousal/valence"""
    valence, arousal = 0.2, 0.1
    
    chord_event, arp_event = meta_generator.generate_next_event(valence, arousal)
    
    assert chord_event is not None
    assert arp_event is not None
    assert arp_event.velocity < 64  # Lower velocity with low arousal
    
# # ordered from most positive to most negative
# IDX_TO_MODE = [
#     "lydian",
#     "ionian",
#     "mixolydian",
#     "dorian",
#     "aeolian",
#     "phrygian",
# ]

# TODO: test also the intervals aftrer reviewing them
def test_get_mode_real_data(meta_generator):
    """Test mode selection with real mode data"""
    # Test happy/high valence (lydian)
    intervals, mode = meta_generator._get_mode(1.0)
    assert mode == "lydian"
    assert len(intervals) == 7  # All modes should have 7 intervals

    # Test happy/high valence (lydian)
    intervals, mode = meta_generator._get_mode(0.8)
    assert mode == "ionian"
    assert len(intervals) == 7  # All modes should have 7 intervals
    
    # Test neutral valence (ionian/major)
    intervals, mode = meta_generator._get_mode(0.2)
    assert mode == "aeolian"
    assert intervals[0] == 0  # Tonic should always be 0
    
    # Test sad/low valence (phrygian)
    intervals, mode = meta_generator._get_mode(0.0)
    assert mode == "phrygian"