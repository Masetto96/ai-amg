import random
import json
import logging
from typing import List, Dict

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
    notes: np.array  # MIDI notes of the event
    velocity: float  # MIDI velocity (0-127)
    root: int = None  # MIDI note of the root
    duration: int = 4  # Duration in beats (assuming 4/4 time)

    def to_ableton_osc(self, start_time: int) -> list:
        """
        Convert the chord event to a MIDI list for Ableton OSC.
        Each note is (midi_note, start_time (in beats), duration, velocity, mute)
        Concatenates all the notes in a list to be sent to Ableton.
        """
        return [
            item for note in self.notes for item in (int(note), start_time, self.duration, self.velocity, 0)
        ]


class MetaGenerator:
    """Generates chords and arpeggiator events based on emotional metrics"""

    def __init__(self):
        self.genetic_melodies = GeneticMelodies()
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
        """Generates the next chord and melody based on valence and arousal"""
        # compute mode, velocity and pitch based on emotional metrics
        vamp_midi_chords, midi_tonal_center, mode_name = self._get_mode_data(valence)
        # TODO: review pitch and velocity computation, implement like in the paper
        # pitch = self._compute_pitch(valence)
        velocity = self._compute_velocity(arousal)
        chord_events = self._generate_modal_midi_vamp(vamp_midi_chords, midi_tonal_center, velocity)
        char_int = self.mode_intervals.get(mode_name).get("characteristic_intervals")
        intervals = self.mode_intervals.get(mode_name).get("intervals")
        genetic_melody = self.genetic_melodies.generate_genetic_melody(intervals, char_int, arousal)
        notes, durations = zip(*genetic_melody)
        return chord_events, MelodyEvent(
            notes=np.array([note + midi_tonal_center for note in notes]),
            velocity=velocity,
            duration=durations,
        )

    def _generate_modal_midi_vamp(self, vamp_midi_chords, midi_tonal_center, velocity) -> List[ChordEvent]:
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
        # TODO: review mapping from mode to valence
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
        # TODO: review velocity computation
        min_velocity = 50
        max_velocity = 127
        v = int(random.uniform(min_velocity, max_velocity * arousal))
        logger.debug("Arousal: %f, Computed velocity: %d", arousal, v)
        # v = min(max_velocity, v)
        return max(min_velocity, v)  # making sure it's not more than 127


@dataclass
class MelodyEvent:
    notes: np.array  # MIDI notes of the event
    velocity: float  # MIDI velocity (0-127)
    duration: np.array  # Duration in beats (assuming 4/4 time)

    def to_ableton_osc(self, start_time: int) -> list:
        """
        Convert the chord event to a MIDI list for Ableton OSC.
        Each note is (midi_note, start_time (in beats), duration, velocity, mute)
        Concatenates all the notes in a list to be sent to Ableton.
        """
        events = []
        current_time = start_time
        for note, duration in zip(self.notes, self.duration):
            events.extend([int(note), current_time, duration, self.velocity, 0])
            current_time += duration
        return events
    
class GeneticMelodies:
    """Generates melodies based on emotional metrics"""

    def __init__(self):
        self.melody = None
        self.evaluator = GeneticMelodyEvaluator()

    def _generate_random_melody(self, mode_intervals: List[int], num_notes: int = 8) -> List[tuple]:
        """Generate a random melody with valid intervals for the given mode."""
        melody = []
        total_duration = 0
        while total_duration < num_notes:
            interval = random.choice(mode_intervals)
            duration = random.choice([0.5, 1.0, 2.0])
            melody.append((interval, duration))
            total_duration += duration
        return melody

    def _mutate(
        self, melody: List[tuple], mode_intervals: List[int], target_arousal: float  # Added target arousal
    ) -> List[tuple]:
        """Mutate melody with bias toward target arousal."""
        mutated = melody.copy()
        idx = random.randint(0, len(melody) - 1)
        new_interval = random.choice(mode_intervals)
        mutated[idx] = (new_interval, mutated[idx][1])

        # Bias mutation based on target arousal
        # if random.random() < 0.7:  # 70% chance to mutate rhythm for arousal
        #     # Shorter durations for higher arousal
        #     if target_arousal > 0.5:
        #         new_duration = random.choice([0.25, 0.5])  # Faster notes
        #     else:
        #         new_duration = random.choice([1.0, 2.0])  # Slower notes
        #     mutated[idx] = (mutated[idx][0], new_duration)
        # else:
        #     # Mutate pitch to stay in mode

        return mutated

    def _crossover(self, parent1: List[tuple], parent2: List[tuple]) -> List[tuple]:
        """Single-point crossover."""
        split = random.randint(1, min(len(parent1), len(parent2)) - 1)
        child = parent1[:split] + parent2[split:]
        
        # Ensure the total duration does not exceed 8
        total_duration = sum(duration for _, duration in child)
        while total_duration > 8:
            child.pop()
            total_duration = sum(duration for _, duration in child)
        
        return child

    def generate_genetic_melody(
        self,
        mode_intervals: List[int],  # Intervals for the mode (e.g., [2, 4, 5, 7, 9, 11])
        char_intervals: List[int],  # Characteristic intervals for the mode
        target_arousal: float,  # Target arousal (0-1)
        population_size: int = 50,  # Number of melodies per generation
        generations: int = 20,  # Number of generations
        elite_size: float = 0.2,  # Top 20% of population to keep
        mutation_rate: float = 0.6,  # Probability of mutating a melody
    ) -> List[tuple]:
        """
        Generate a melody conditioned on mode (valence) and target arousal.

        Args:
            mode (str): The mode to use (e.g., "lydian", "dorian").
            target_arousal (float): Desired arousal level (0-1).
            population_size (int): Number of melodies in each generation.
            generations (int): Number of generations to evolve.
            elite_size (float): Fraction of top melodies to keep.
            mutation_rate (float): Probability of mutating a melody.

        Returns:
            List[tuple]: The best melody found, as a list of (interval, duration) tuples.
        """
        # Initialize population
        population = [self._generate_random_melody(mode_intervals) for _ in range(population_size)]

        for gen in range(generations):
            # Evaluate fitness for each melody
            scores = [
                (self.evaluator.fitness(melody, mode_intervals, char_intervals, target_arousal), melody)
                for melody in population
            ]
            scores.sort(reverse=True, key=lambda x: x[0])  # Sort by fitness

            # Select elites (top 20%)
            elites = [m for (s, m) in scores[: int(elite_size * population_size)]]

            # Select rest of the population randomly (for diversity)
            rest = random.sample(
                [m for (s, m) in scores[int(elite_size * population_size) :]], population_size - len(elites)
            )
            parents = elites + rest

            # Breed next generation
            next_gen = elites.copy()  # Keep elites
            while len(next_gen) < population_size:
                # Select two parents randomly
                parent1, parent2 = random.sample(parents, 2)

                # Crossover
                child = self._crossover(parent1, parent2)

                # Mutate (with probability mutation_rate)
                if random.random() < mutation_rate:
                    child = self._mutate(child, mode_intervals, target_arousal)

                next_gen.append(child)

            population = next_gen

        # Return the best melody
        best_melody = max(
            population,
            key=lambda m: self.evaluator.fitness(m, mode_intervals, char_intervals, target_arousal),
        )
        logger.info(
            "Best melody fitness: %f",
            self.evaluator.fitness(best_melody, mode_intervals, char_intervals, target_arousal),
        )
        logger.debug("Best melody: %s", best_melody)
        return best_melody

class GeneticMelodyEvaluator:
    def _calculate_valence(self, melody: List[tuple], mode_intervals: List[int], char_intervals: List[int]) -> float:
        """Calculate valence score based on mode adherence and melodic quality."""
        if not melody:
            return 0.0
        
        # Characteristic interval usage
        char_count = sum(1 for note, _ in melody if note in char_intervals)
        char_ratio = char_count / len(melody)

        # Tonic frequency
        tonic_count = sum(1 for note, _ in melody if note == 0)
        tonic_ratio = tonic_count / len(melody)

        # Interval variety
        unique_intervals = len({note for note, _ in melody})
        variety_ratio = unique_intervals / len(mode_intervals)
        
        # Note repetition penalty
        repeated_notes = sum(1 for i in range(1, len(melody)) if melody[i][0] == melody[i-1][0])
        repetition_penalty = repeated_notes / len(melody)

        valence_score = (
            0.3 * char_ratio +          # Emphasize characteristic intervals
            0.3 * tonic_ratio +         # Reward frequent tonic usage 
            0.2 * variety_ratio -      # Encourage interval diversity
            0.2 * repetition_penalty   # Penalize note repetition
        )
        # logger.debug(
        #     "Valence calculation: char_ratio=%f, tonic_ratio=%f,  variety_ratio=%f, repetition_penalty=%f",
        #     char_ratio, tonic_ratio, variety_ratio, repetition_penalty,
        # )
        return valence_score

    def _calculate_arousal(self, melody: List[tuple]) -> float:
        """Calculate arousal score with enhanced rhythmic analysis."""
        if not melody:
            return 0.0
        
        # # Syncopation calculation
        # syncopated = 0
        # current_time = 0.0
        # for _, duration in melody:
        #     # Check if note starts on weak beat
        #     if not (current_time % 1.0 == 0.0):
        #         syncopated += 1
        #     current_time += duration
        # sync_ratio = syncopated / len(melody)

        # Rhythmic density calculation
        total_duration = sum(duration for _, duration in melody)
        density = len(melody) / total_duration if total_duration > 0 else 0

        # Dynamic tempo variation
        durations = [duration for _, duration in melody]
        duration_variation = np.std(durations) if len(durations) > 1 else 0
        # logger.debug(
        #     "Arousal calculation: sync_ratio=%f, density=%f, duration_variation=%f",
        #     sync_ratio, density, duration_variation
        # )
        return min(1.0, 
            0.8 * density + 
            0.2 * duration_variation
        )

    def fitness(
        self,
        melody: List[tuple],
        mode_intervals: List[int],
        char_intervals: List[int],
        target_arousal: float,
    ) -> float:
        """Enhanced fitness calculation with balanced emotional weighting."""
        valence_score = self._calculate_valence(melody, mode_intervals, char_intervals)
        actual_arousal = self._calculate_arousal(melody)

        # Arousal fitness with non-linear penalty
        arousal_error = abs(actual_arousal - target_arousal)
        arousal_fitness = 1.0 - (arousal_error)  # Square root for softer penalty
        logger.debug(
            "Arousal fitness: %f (actual: %f, target: %f)",
            arousal_fitness, actual_arousal, target_arousal
        )
        # Balanced weighting with dominance for primary emotion
        return 0.5 * valence_score + 0.5 * arousal_fitness