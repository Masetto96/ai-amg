from typing import List
from music_gen.chord_generator import ChordEvent

# def chord_event_to_midi(chord_event: ChordEvent, start_time=0.0, mute=0):
#     """
#     Converts a ChordEvent into a flattened list of MIDI note attributes.
    
#     Parameters:
#         chord_event (ChordEvent): The chord event to convert.
#         start_time (float): The start time of the chord in beats.
#         mute (bool): Whether the notes should be muted.
    
#     Returns:
#         list: A flattened list of MIDI note attributes in the format:
#               [pitch, start_time, duration, velocity, mute, ...]
#     """
#     midi_list = []
#     for note in chord_event.notes:
#         midi_list.extend([int(note), start_time, chord_event.duration, chord_event.velocity, mute])
#     return midi_list


# def chord_to_midi(chord_events: List[ChordEvent], include_third=True):
#     """
#     Convert a list of ChordEvent objects into MIDI note events, including a bass line.

#     Args:
#         chord_events: List of ChordEvent objects.
#         include_third: Boolean indicating whether to include the third in the bass line.

#     Returns:
#         Tuple of two lists:
#         - List of MIDI note tuples for chords in the format:
#           (pitch, start_time, duration, velocity, mute)
#         - List of MIDI note tuples for bass line in the same format.
#     """
#     midi_notes = []  # For chord notes
#     bass_line = []  # For bass line
#     current_time = 0.0  # Start time in beats

#     for event in chord_events:
#         chord_pitches = CHORD_MAPPING.get(event.chord, [])
#         tonic = (
#             chord_pitches[0] if chord_pitches else None
#         )  # Assume the tonic is the first pitch
#         third = (
#             chord_pitches[1] if len(chord_pitches) > 1 else None
#         )  # Assume the third is the second pitch

#         # Generate chord notes
#         for pitch in chord_pitches:
#             variation = random.uniform(
#                 -20, 20
#             )  # Add velocity variation for each note in the chord
#             new_velocity = int(event.velocity + variation)
#             midi_notes.append(
#                 (pitch, current_time, event.duration, new_velocity, 0)
#             )  # Mute=0 for now

#         # Generate bass line notes
#         if tonic is not None:
#             bass_line.append(
#                 (tonic - 12, current_time, event.duration, event.velocity, 0)
#             )  # Add tonic to bass line, transpose by 12 semitones
#         if include_third and third is not None:
#             bass_line.append(
#                 (third - 12, current_time, event.duration, event.velocity, 0)
#             )  # Add third to bass line if requested

#         current_time += event.duration

#     return midi_notes, bass_line


# def transpose_midi_chords(midi_notes, transpose_amount):
#     """
#     Transpose a list of MIDI note events by a specified amount.

#     Args:
#         midi_notes: List of MIDI note tuples in the format:
#                     (pitch, start_time, duration, velocity, mute)
#         transpose_amount: Integer value to transpose the notes by.

#     Returns:
#         List of transposed MIDI note tuples.
#     """
#     transposed_notes = []
#     for pitch, start_time, duration, velocity, mute in midi_notes:
#         transposed_pitch = pitch + transpose_amount
#         transposed_notes.append(
#             (transposed_pitch, start_time, duration, velocity, mute)
#         )
#     return transposed_notes