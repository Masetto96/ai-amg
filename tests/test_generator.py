import pytest
import numpy as np
from unittest.mock import patch, mock_open
from music_gen.generator import ChordEvent, ArpeggiatorEvent, MetaGenerator, CircleOfFifths, intervals_to_midi_notes

@pytest.fixture
def meta_generator():
    mock_json = '''
    {
        "lydian": {
            "intervals": {"T": 0, "S": 2, "M": 4, "L": 5, "H": 7},
            "rules": {"T": ["S", "M"], "S": ["M", "L"], "M": ["H"]}
        },
        "ionian": {
            "intervals": {"T": 0, "S": 2, "M": 4, "L": 5, "H": 7},
            "rules": {"T": ["S", "M"], "S": ["M", "L"], "M": ["H"]}
        },
        "mixolydian": {
            "intervals": {"T": 0, "S": 2, "M": 4, "L": 5, "H": 7},
            "rules": {"T": ["S", "M"], "S": ["M", "L"], "M": ["H"]}
        },
        "dorian": {
            "intervals": {"T": 0, "S": 2, "M": 4, "L": 5, "H": 7},
            "rules": {"T": ["S", "M"], "S": ["M", "L"], "M": ["H"]}
        },
        "aeolian": {
            "intervals": {"T": 0, "S": 2, "M": 4, "L": 5, "H": 7},
            "rules": {"T": ["S", "M"], "S": ["M", "L"], "M": ["H"]}
        },
        "phrygian": {
            "intervals": {"T": 0, "S": 2, "M": 4, "L": 5, "H": 7},
            "rules": {"T": ["S", "M"], "S": ["M", "L"], "M": ["H"]}
        }
    }'''
    with patch("builtins.open", mock_open(read_data=mock_json)):
        return MetaGenerator()

def test_chord_event_to_ableton_osc():
    event = ChordEvent(notes=np.array([60, 64, 67]), velocity=100, duration=4)
    result = event.to_ableton_osc(0)
    expected = [60, 0, 4, 100, 0, 64, 0, 4, 100, 0, 67, 0, 4, 100, 0]
    assert result == expected

def test_arpeggiator_event_to_ableton_osc():
    np.random.seed(42)
    event = ArpeggiatorEvent(notes=np.array([60, 64, 67]), velocity=100, duration=8)
    result = event.to_ableton_osc(0)

    assert len(result) == 15 # 3 notes * 5 parameters
    assert result[0] == 60
    assert result[5] == 64
    assert result[10] == 67
    assert result[2] + result[7] + result[12] == 8

def test_generate_next_event(meta_generator):
    mode_intervals = np.array([0, 2, 4, 5, 7, 9, 11])
    with patch.object(meta_generator.circle, 'navigate_circle', return_value=('C', 60)), \
         patch.object(meta_generator, '_generate_melody_interv', return_value=np.array([0, 4, 7])), \
         patch.object(meta_generator, '_get_mode', return_value=(mode_intervals, 'lydian')):

        chord_event, arp_event = meta_generator.generate_next_event(0.7, 0.8)

        assert isinstance(chord_event, ChordEvent)
        assert isinstance(arp_event, ArpeggiatorEvent)
        assert len(chord_event.notes) == 4
        assert chord_event.velocity >= 50
        assert chord_event.velocity <= 127
        assert chord_event.root == 60
        assert arp_event.root == 60
        assert len(arp_event.notes) == 3

def test_create_chord(meta_generator):
    mode_intervals = np.array([0, 2, 4, 5, 7, 9, 11])
    chord = meta_generator.create_chord(
        tonal_midi=60,
        mode_intervals=mode_intervals,
        velocity=100,
        pitch_shift=0
    )

    assert isinstance(chord, ChordEvent)
    assert len(chord.notes) == 4
    assert chord.root == 60
    assert chord.velocity == 100
    np.testing.assert_array_equal(chord.notes, [60, 64, 67, 71])

def test_create_arpeggiator(meta_generator):
    with patch.object(meta_generator, '_generate_melody_interv', return_value=np.array([0, 4, 7])):
        arp = meta_generator.create_arpeggiator(
            tonal_midi=60,
            mode_name="lydian",
            velocity=100,
            pitch_shift=0,
            k=3
        )

        assert isinstance(arp, ArpeggiatorEvent)
        assert len(arp.notes) == 3
        assert arp.root == 60
        assert arp.velocity == 100
        np.testing.assert_array_equal(arp.notes, [72, 76, 79])

def test_circle_navigate():
    circle = CircleOfFifths()

    # Test clockwise movement (fifths)
    note, midi = circle.navigate_circle('C', 1, 'fifths')
    assert note == 'G'
    assert midi == 55

    # Test counterclockwise movement (fourths)
    note, midi = circle.navigate_circle('C', 1, 'fourths')
    assert note == 'F'
    assert midi == 65

    # Test wrapping around
    note, midi = circle.navigate_circle('C', 12, 'fifths')
    assert note == 'C'
    assert midi == 60

def test_circle_navigate_invalid():
    circle = CircleOfFifths()
    with pytest.raises(ValueError):
        circle.navigate_circle('H', 1)

def test_intervals_to_midi_notes():
    intervals = np.array([0, 4, 7])
    midi_notes = intervals_to_midi_notes(intervals, 60, 0)
    np.testing.assert_array_equal(midi_notes, [60, 64, 67])

    # Test with pitch shift
    midi_notes = intervals_to_midi_notes(intervals, 60, 12)
    np.testing.assert_array_equal(midi_notes, [72, 76, 79])
