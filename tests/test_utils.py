import pytest
import numpy as np
from emotion_detection.utils import (DynamicScaler, compute_band_powers, nextpow2,
                                   update_buffer, get_last_epoch, clamp, initialize_buffer,
                                   populate_initial_buffer, epoch)

@pytest.fixture
def dynamic_scaler():
    return DynamicScaler(window_size=5, target_range=(0, 1))

def test_dynamic_scaler_initialization(dynamic_scaler):
    assert dynamic_scaler.window_size == 5
    assert dynamic_scaler.target_range == (0, 1)
    assert len(dynamic_scaler.values) == 0
    assert not dynamic_scaler.ready

def test_dynamic_scaler_update(dynamic_scaler):
    dynamic_scaler.update(1.0)
    assert len(dynamic_scaler.values) == 1
    assert not dynamic_scaler.ready

    for i in range(4):
        dynamic_scaler.update(float(i))
    assert len(dynamic_scaler.values) == 5
    assert dynamic_scaler.ready

def test_dynamic_scaler_scale(dynamic_scaler):
    with pytest.raises(ValueError):
        dynamic_scaler.scale(1.0)

    for i in range(5):
        dynamic_scaler.update(float(i))

    assert dynamic_scaler.scale(2.0) == 0.5
    assert dynamic_scaler.scale(4.0) == 1.0
    assert dynamic_scaler.scale(0.0) == 0.0

def test_dynamic_scaler_same_values():
    scaler = DynamicScaler(window_size=3)
    for _ in range(3):
        scaler.update(5.0)
    assert scaler.scale(5.0) == 0.5

def test_compute_band_powers():
    fs = 256
    t = np.linspace(0, 1, fs)
    signal = np.sin(2 * np.pi * 10 * t)
    eegdata = np.column_stack((signal, signal))

    features = compute_band_powers(eegdata, fs)
    assert features.shape == (8,)

def test_compute_band_powers_edge_cases():
    fs = 256
    t = np.linspace(0, 0.1, fs//10)
    signal = np.zeros_like(t)
    eegdata = np.column_stack((signal, signal))

    features = compute_band_powers(eegdata, fs)
    assert features.shape == (8,)

def test_nextpow2():
    assert nextpow2(3) == 4
    assert nextpow2(4) == 4
    assert nextpow2(5) == 8
    assert nextpow2(7) == 8
    assert nextpow2(8) == 8
    assert nextpow2(9) == 16
    assert nextpow2(1) == 1
    assert nextpow2(0) == 1

def test_update_buffer():
    buffer = np.zeros((10, 2))
    new_data = np.ones((5, 2))

    updated_buffer, filter_state = update_buffer(buffer, new_data)
    assert updated_buffer.shape == (10, 2)
    assert np.array_equal(updated_buffer[-5:], new_data)
    assert np.array_equal(updated_buffer[:5], np.zeros((5, 2)))

def test_update_buffer_with_notch():
    buffer = np.zeros((10, 2))
    new_data = np.ones((5, 2))

    updated_buffer, filter_state = update_buffer(buffer, new_data, notch=True)
    assert updated_buffer.shape == (10, 2)
    assert filter_state is not None

def test_get_last_epoch():
    data = np.array([[1,2], [3,4], [5,6], [7,8]])
    result = get_last_epoch(data, 2)
    assert np.array_equal(result, np.array([[5,6], [7,8]]))

def test_clamp():
    assert clamp(5, 0, 10) == 5
    assert clamp(-1, 0, 10) == 0
    assert clamp(11, 0, 10) == 10
    assert clamp(5.5, 0, 10) == 5.5
    assert clamp(1.0, 1.0, 1.0) == 1.0
    assert clamp(-float('inf'), 0, 1) == 0
    assert clamp(float('inf'), 0, 1) == 1

def test_initialize_buffer():
    fs = 256
    buffer_length = 1
    index_channel = [0, 1]

    buffer, filter_state = initialize_buffer(fs, buffer_length, index_channel)
    assert buffer.shape == (256, 2)
    assert np.array_equal(buffer, np.zeros((256, 2)))
    assert filter_state is None

@pytest.mark.skip(reason="Requires LSL inlet which is not easily mockable")
def test_populate_initial_buffer():
    pass

def test_epoch():
    data = np.array([[1,2], [3,4], [5,6], [7,8], [9,10], [11,12]])
    samples_epoch = 3
    samples_overlap = 1

    epochs = epoch(data, samples_epoch, samples_overlap)
    expected_shape = (3, 2, 2)  # (samples_epoch, channels, n_epochs)
    assert epochs.shape == expected_shape

    # Test first epoch
    assert np.array_equal(epochs[:,:,0], np.array([[1,2], [3,4], [5,6]]))
    # Test second epoch
    assert np.array_equal(epochs[:,:,1], np.array([[5,6], [7,8], [9,10]]))

def test_epoch_no_overlap():
    data = np.array([[1,2], [3,4], [5,6], [7,8]])
    samples_epoch = 2

    epochs = epoch(data, samples_epoch)
    assert epochs.shape == (2, 2, 2)
    assert np.array_equal(epochs[:,:,0], np.array([[1,2], [3,4]]))
    assert np.array_equal(epochs[:,:,1], np.array([[5,6], [7,8]]))

def test_epoch_edge_cases():
    # Test with single channel
    data = np.array([[1], [2], [3], [4]])
    epochs = epoch(data, samples_epoch=2)
    assert epochs.shape == (2, 1, 2)

    # Test with minimal data
    data = np.array([[1,2], [3,4]])
    epochs = epoch(data, samples_epoch=2)
    assert epochs.shape == (2, 2, 1)

    # Test with empty data
    data = np.array([]).reshape(0, 2)
    epochs = epoch(data, samples_epoch=2)
    assert epochs.shape == (2, 2, 0)

def test_dynamic_scaler_edge_cases():
    scaler = DynamicScaler(window_size=1, target_range=(-1, 1))
    scaler.update(0)
    assert scaler.ready
    assert scaler.scale(0) == 0.0

    # Test with negative values
    scaler = DynamicScaler(window_size=2)
    scaler.update(-1)
    scaler.update(1)
    assert scaler.scale(0) == 0.5

    # Test with extreme values
    scaler = DynamicScaler(window_size=2)
    scaler.update(float('inf'))
    scaler.update(-float('inf'))
    assert 0 <= scaler.scale(0) <= 1
