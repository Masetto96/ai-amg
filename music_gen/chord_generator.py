from typing import List
from dataclasses import dataclass
import random

@dataclass
class ChordEvent:
    chord: str      # Chord symbol
    duration: float # Duration in beats (assuming 4/4 time)
    velocity: float # MIDI velocity (0-1)

class ChordProgressionGenerator:
    def __init__(self):
        self.quadrant_progressions = {
            # Calm and stable, major chords without extensions
            'low_arousal_high_valence': [
                ['I', 'IV'],           # Simple and stable
                ['I', 'IVmaj7']        # Adding slight tension with IV7
            ],
            
            # Bright, energetic major chords with dynamic extensions
            'high_arousal_high_valence': [
                ['I', 'IV7', 'V', 'I'],       # IV7 for subtle tension
                ['I', 'V', 'vi7', 'IV'],      # vi7 adds richness to the minor
                ['I', 'V7', 'vi7', 'IV9'],    # V7 and IV9 create a more colorful sequence
            ],
            
            # Somber and introspective minor chords, no extensions for low energy
            'low_arousal_low_valence': [
                ['i', 'iv'],          # Simple and stable in minor
                ['i', 'iv7']          # Adding a hint of richness with iv7
            ],
            
            # Dark and dramatic minor chords with tension-rich extensions
            'high_arousal_low_valence': [
                ['i', 'VI', 'III7', 'VII'],     # III7 for unexpected brightness
                ['i', 'VII7', 'VI7', 'V'],      # VII7 adds drama
            ]
        }


    def generate_progression(self, valence: float, arousal: float) -> List[ChordEvent]:
        """
        Generate a chord progression based on valence and arousal quadrant.
        
        Args:
            valence: Float between -1 (negative) and 1 (positive)
            arousal: Float between -1 (low) and 1 (high)
            
        Returns:
            List of ChordEvent objects for the progression
        """
        # Determine quadrant
        if valence >= 0 and arousal < 0:
            quadrant = 'low_arousal_high_valence'
        elif valence >= 0 and arousal >= 0:
            quadrant = 'high_arousal_high_valence'
        elif valence < 0 and arousal < 0:
            quadrant = 'low_arousal_low_valence'
        else:
            quadrant = 'high_arousal_low_valence'
        
        base_progression = random.choice(self.quadrant_progressions[quadrant])
        
        # Set chord duration based on arousal
        if arousal >= 0:
            beats_per_chord = 4
        else:
            beats_per_chord = 8
        
        # Generate chord events
        events = [ChordEvent(chord=chord, duration=beats_per_chord, velocity=self._compute_velocity(arousal)) for chord in base_progression]

        return events

    def _compute_velocity(self, arousal: float) -> int:
        """
        Compute the velocity based on arousal level, constrained between 50 and 120.
        
        Args:
            arousal: Float between -1 (low arousal) and 1 (high arousal)
        
        Returns:
            An integer velocity value in the range [50, 120].
        """
        # TODO: maybe valence could play a role here to. Add valence in the equation.
        # Map arousal (-1 to 1) to velocity range [50, 120]
        base_velocity = 85 + 35 * arousal  # Maps arousal to midpoint (85) ± 35
        variation = random.uniform(-5, 5)  # Add slight variation
        velocity = int(base_velocity + variation)
        
        # Clamp the result to ensure it stays within [50, 120]
        return max(50, min(120, velocity))

# def demonstrate_generator():
#     generator = ChordProgressionGenerator()
    
#     # Test different emotional combinations
#     test_cases = [
#         (0.8, 0.8, "High energy, positive (4 chords)"),
#         (-0.8, 0.8, "High energy, negative (4 chords)"),
#         (0.8, -0.8, "Low energy, positive (2 chords)"),
#         (-0.8, -0.8, "Low energy, negative (2 chords)")
#     ]
    
#     for valence, arousal, description in test_cases:
#         print(f"\n{description}")
#         print(f"Valence: {valence}, Arousal: {arousal}")
        
#         events = generator.generate_progression(valence, arousal)
        
#         # Display the progression
#         print("\nProgression (4 bars total):")
#         for i, event in enumerate(events):
#             print(f"Chord {i+1}: {event.chord} ({event.duration} beats, velocity: {event.velocity:.2f})")

# if __name__ == "__main__":
#     demonstrate_generator()