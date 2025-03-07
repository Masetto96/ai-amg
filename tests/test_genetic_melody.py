import pytest
from music_gen.generator import GeneticMelodies, GeneticMelodyEvaluator


@pytest.fixture
def setup_genetic_melodies():
    genetic_melodies = GeneticMelodies()
    evaluator = GeneticMelodyEvaluator()
    mode_intervals = [0, 2, 4, 5, 7, 9, 11]  # Example intervals for a major scale
    char_intervals = [4, 7]  # Example characteristic intervals for a major scale
    return genetic_melodies, evaluator, mode_intervals, char_intervals


def test_generate_random_melody(setup_genetic_melodies):
    genetic_melodies, _, mode_intervals, _ = setup_genetic_melodies
    melody = genetic_melodies._generate_random_melody(mode_intervals)
    assert len(melody) > 0, "Generated melody should not be empty"
    for note, duration in melody:
        assert note in mode_intervals, "Note should be in mode intervals"
        assert duration in [0.25, 0.5, 1.0, 2.0], "Duration should be one of the allowed values"


def test_mutate_melody(setup_genetic_melodies):
    genetic_melodies, _, mode_intervals, _ = setup_genetic_melodies
    original_melody = genetic_melodies._generate_random_melody(mode_intervals)
    mutated_melody = genetic_melodies._mutate(original_melody, mode_intervals, 0.8)
    assert original_melody != mutated_melody, "Mutated melody should be different from the original"


def test_crossover_melody(setup_genetic_melodies):
    genetic_melodies, _, mode_intervals, _ = setup_genetic_melodies
    parent1 = genetic_melodies._generate_random_melody(mode_intervals)
    parent2 = genetic_melodies._generate_random_melody(mode_intervals)
    child = genetic_melodies._crossover(parent1, parent2)
    assert len(child) > 0, "Child melody should not be empty"
    assert any(
        note in mode_intervals for note, _ in child
    ), "Child melody should have notes in mode intervals"


def test_generate_genetic_melody(setup_genetic_melodies):
    genetic_melodies, _, mode_intervals, char_intervals = setup_genetic_melodies
    melody = genetic_melodies.generate_genetic_melody(mode_intervals, char_intervals, target_arousal=0.8)
    assert len(melody) > 0, "Generated genetic melody should not be empty"
    for note, duration in melody:
        assert note in mode_intervals, "Note should be in mode intervals"
        assert duration in [0.25, 0.5, 1.0, 2.0], "Duration should be one of the allowed values"


def test_fitness_evaluation(setup_genetic_melodies):
    genetic_melodies, evaluator, mode_intervals, char_intervals = setup_genetic_melodies
    melody = genetic_melodies._generate_random_melody(mode_intervals)
    fitness_score = evaluator.fitness(melody, mode_intervals, char_intervals, target_arousal=0.8)
    assert 0 <= fitness_score <= 1, "Fitness score should be between 0 and 1"
