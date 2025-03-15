import pytest
import numpy as np
from emotion_detection.eeg_recording.simulate_eeg import MockEEGProcessor

@pytest.fixture
def eeg_processor():
    return MockEEGProcessor(sampling_rate=250)

def test_create_bandpass_filter(eeg_processor):
    b, a = eeg_processor.create_bandpass_filter(8, 13)
    assert len(b) > 0
    assert len(a) > 0
    assert isinstance(b, np.ndarray)
    assert isinstance(a, np.ndarray)

def test_process_sample_adds_to_buffer(eeg_processor):
    sample = {'TP9': 1.0, 'AF7': 2.0, 'AF8': 3.0, 'TP10': 4.0}
    eeg_processor.process_sample(sample)

    for ch in eeg_processor.channels:
        assert len(eeg_processor.buffers[ch]) == 1
        assert eeg_processor.buffers[ch][0] == sample[ch]

def test_process_sample_maintains_buffer_size(eeg_processor):
    sample = {'TP9': 1.0, 'AF7': 2.0, 'AF8': 3.0, 'TP10': 4.0}

    # Fill buffer beyond size
    for _ in range(eeg_processor.buffer_size + 10):
        eeg_processor.process_sample(sample)

    for ch in eeg_processor.channels:
        assert len(eeg_processor.buffers[ch]) == eeg_processor.buffer_size

def test_calculate_band_power_empty_data(eeg_processor):
    data = []
    b, a = eeg_processor.create_bandpass_filter(8, 13)
    power = eeg_processor.calculate_band_power(data, b, a)
    assert power == 0

def test_calculate_band_power_valid_data(eeg_processor):
    # Generate sine wave at 10 Hz (alpha band)
    t = np.linspace(0, 1, eeg_processor.buffer_size)
    data = np.sin(2 * np.pi * 10 * t)

    b, a = eeg_processor.create_bandpass_filter(8, 13)
    power = eeg_processor.calculate_band_power(data, b, a)

    assert power > 0
    assert isinstance(power, float)

def test_get_band_powers_empty_buffers(eeg_processor):
    powers = eeg_processor.get_band_powers()
    assert 'alpha' in powers
    assert 'beta' in powers
    assert len(powers['alpha']) == 0
    assert len(powers['beta']) == 0

def test_get_band_powers_full_buffers(eeg_processor):
    # Fill buffers with sine wave
    t = np.linspace(0, 1, eeg_processor.buffer_size)
    data = np.sin(2 * np.pi * 10 * t)

    sample = {ch: data[0] for ch in eeg_processor.channels}
    for i in range(eeg_processor.buffer_size):
        sample = {ch: data[i] for ch in eeg_processor.channels}
        eeg_processor.process_sample(sample)

    powers = eeg_processor.get_band_powers()

    assert 'alpha' in powers
    assert 'beta' in powers
    assert len(powers['alpha']) == len(eeg_processor.channels)
    assert len(powers['beta']) == len(eeg_processor.channels)

    for ch in eeg_processor.channels:
        assert ch in powers['alpha']
        assert ch in powers['beta']
        assert powers['alpha'][ch] > 0
        assert powers['beta'][ch] > 0
