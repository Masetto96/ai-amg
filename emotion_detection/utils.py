# -*- coding: utf-8 -*-
"""
Muse LSL Example Auxiliary Tools

These functions perform the lower-level operations involved in buffering,
epoching, and transforming EEG data into frequency bands

@author: Cassani
"""

import logging
from collections import deque
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, lfilter, lfilter_zi


logger = logging.getLogger(__name__)


class DynamicScaler:
    def __init__(self, window_size=100, target_range=(0, 1)):
        """
        Initialize the scaler with a rolling window to track recent values.
        :param window_size: Number of recent values to consider for scaling.
        :param target_range: The range to scale values into.
        """
        logger.debug("Scaler initialized with history of %d and target range of %s", window_size, target_range)
        self.window_size = window_size
        self.target_range = target_range
        self.values = []  # List to store the rolling window of values.
        self.ready = False  # Flag to indicate if the scaler is ready.

    def update(self, value):
        """
        Update the rolling window with a new value.
        :param value: The latest metric to be added to the window.
        """
        self.values.append(value)
        if len(self.values) > self.window_size:
            self.values.pop(0)  # Remove oldest value to maintain window size.

        # Set the scaler as ready once the window is fully populated.
        if len(self.values) == self.window_size:
            logger.debug("Scaler is ready")
            self.ready = True

    def scale(self, value):
        """
        Scale a value based on the current min and max of the rolling window.
        Clamps the scaled value to the target range.
        :param value: The value to scale.
        :return: Scaled value within the target range.
        """
        if not self.ready:
            raise ValueError("Scaler is not ready yet, window is not full.")
        
        min_val = min(self.values)
        max_val = max(self.values)
        
        if max_val == min_val:
            logger.warning("Division by zero avoided in scaling.")
            # Avoid division by zero if all values in the window are identical.
            return round(sum(self.target_range) / 2, 1)  # Neutral value in target range.
        
        # Linear scaling calculation
        scaled_value = (value - min_val) / (max_val - min_val)
        
        # Scale to target range
        scaled_result = self.target_range[0] + scaled_value * (self.target_range[1] - self.target_range[0])
        
        clamped_result = clamp(scaled_result, min_val=self.target_range[0], max_val=self.target_range[1])
        
        return round(clamped_result, 2)

def compute_band_powers(eegdata, fs):
    #  TODO: refactor this function
    """Extract the features (band powers) from the EEG.

    Args:
        eegdata (numpy.ndarray): array of dimension [number of samples,
                number of channels]
        fs (float): sampling frequency of eegdata

    Returns:
        (numpy.ndarray): feature matrix of shape [number of feature points,
            number of different features]
    """
    # 1. Compute the PSD
    winSampleLength, nbCh = eegdata.shape

    # Apply Hamming window
    w = np.hamming(winSampleLength)
    dataWinCentered = eegdata - np.mean(eegdata, axis=0)  # Remove offset
    dataWinCenteredHam = (dataWinCentered.T * w).T

    NFFT = nextpow2(winSampleLength)
    Y = np.fft.fft(dataWinCenteredHam, n=NFFT, axis=0) / winSampleLength
    PSD = 2 * np.abs(Y[0:int(NFFT / 2), :])
    f = fs / 2 * np.linspace(0, 1, int(NFFT / 2))

    # SPECTRAL FEATURES
    # Average of band powers
    # Delta <4
    ind_delta, = np.where(f < 4)
    meanDelta = np.mean(PSD[ind_delta, :], axis=0)
    # Theta 4-8
    ind_theta, = np.where((f >= 4) & (f <= 8))
    meanTheta = np.mean(PSD[ind_theta, :], axis=0)
    # Alpha 8-12
    ind_alpha, = np.where((f >= 8) & (f <= 12))
    meanAlpha = np.mean(PSD[ind_alpha, :], axis=0)
    # Beta 12-30
    ind_beta, = np.where((f >= 12) & (f < 30))
    meanBeta = np.mean(PSD[ind_beta, :], axis=0)

    feature_vector = np.concatenate((meanDelta, meanTheta, meanAlpha,
                                     meanBeta), axis=0)

    feature_vector = np.log10(feature_vector)

    return feature_vector

def nextpow2(i):
    """
    Find the next power of 2 for number i
    """
    n = 1
    while n < i:
        n *= 2
    return n

NOTCH_B, NOTCH_A = butter(4, np.array([55, 65]) / (256 / 2), btype='bandstop')
def update_buffer(data_buffer, new_data, notch=False, filter_state=None):
    """
    Concatenates "new_data" into "data_buffer", applies optional notch filtering,
    and returns an updated buffer of the same size as `data_buffer`.

    Parameters:
    - data_buffer: Existing buffer of shape (buffer_size, channels).
    - new_data: Incoming data of shape (samples, channels) or (samples,).
    - notch: Boolean, whether to apply a notch filter.
    - filter_state: State for the notch filter.

    Returns:
    - new_buffer: Updated buffer of the same shape as `data_buffer`.
    - filter_state: Updated filter state.
    """
    # Apply notch filter if requested
    if notch:
        if filter_state is None:
            # Initialize filter state for each channel
            filter_state = np.array([lfilter_zi(NOTCH_B, NOTCH_A) for _ in range(data_buffer.shape[1])]).T

        # Apply filter independently to each channel
        new_data, filter_state = lfilter(NOTCH_B, NOTCH_A, new_data, axis=0, zi=filter_state)

    # Concatenate along time axis and trim to buffer size
    new_buffer = np.concatenate((data_buffer, new_data), axis=0)
    new_buffer = new_buffer[-data_buffer.shape[0]:, :]  # Keep only the most recent data

    return new_buffer, filter_state

def get_last_epoch(buffer_array, num_samples):
    return buffer_array[-num_samples:, :]

def clamp(value, min_val, max_val):
    return max(min_val, min(max_val, value))

def initialize_buffer(fs, buffer_length, index_channel):
    """
    Initialize the EEG buffer and filter state.
    :param fs: Sampling frequency.
    :param buffer_length: Length of the buffer in seconds.
    :param index_channel: List of channel indices.
    :return: Initialized buffer and filter state.
    """
    logger.info("Initializing buffer with length %d seconds and sampling frequency %d Hz", buffer_length, fs)
    eeg_buffer = np.zeros((int(fs * buffer_length), len(index_channel)))  # shape [samples, channels]
    filter_state = None
    return eeg_buffer, filter_state

def populate_initial_buffer(inlet, eeg_buffer, filter_state, shift_length, fs, index_channel):
    """
    Populate the initial EEG buffer with data.
    :param inlet: LSL inlet to pull data from.
    :param eeg_buffer: EEG buffer to populate.
    :param filter_state: Filter state for notch filtering.
    :param shift_length: Length to shift the buffer.
    :param fs: Sampling frequency.
    :param index_channel: List of channel indices.
    :return: Updated EEG buffer and filter state.
    """
    logger.debug("Populating initial buffer with EEG data")
    while np.any(eeg_buffer == 0):
        eeg_data, _ = inlet.pull_chunk(timeout=1, max_samples=int(shift_length * fs))
        ch_data = np.array(eeg_data)[:, index_channel]
        eeg_buffer, filter_state = update_buffer(
            eeg_buffer, ch_data, notch=True, filter_state=filter_state
        )
    logger.debug("Buffer populated successfully")
    return eeg_buffer, filter_state

def live_plot(valence, arousal, title:str="", max_points:int=100):
    """
    Live plot for two data streams in a distinct figure based on the title.
    Includes numeric display for the latest values in the plot.
    :param data1: First data stream (e.g., valence or raw).
    :param data2: Second data stream (e.g., arousal or scaled).
    :param title: Title of the plot, used as a unique identifier for the figure.
    :param max_points: Maximum number of points to display in the live plot.
    """
    # Static storage for figures and plots
    if not hasattr(live_plot, "plots"):
        live_plot.plots = {}

    # Initialize the plot if this title is new
    if title not in live_plot.plots:
        fig, ax = plt.subplots(figsize=(8, 4))
        fig.suptitle(title)
        line1, = ax.plot([], [], label="Valence")
        line2, = ax.plot([], [], label="Arousal")
        ax.legend()
        ax.grid(True)

        # Add text placeholders for numeric values
        val_text = ax.text(0.02, 0.02, '', transform=ax.transAxes, fontsize=10, color='blue')
        arousal_text = ax.text(0.02, 0.1, '', transform=ax.transAxes, fontsize=10, color='orange')

        live_plot.plots[title] = {
            "valence_data": deque(maxlen=max_points),
            "arousal_data": deque(maxlen=max_points),
            "fig": fig,
            "ax": ax,
            "line1": line1,
            "line2": line2,
            "val_text": val_text,
            "arousal_text": arousal_text,
        }

    # Update the stored data for this plot
    plot = live_plot.plots[title]
    plot["valence_data"].append(valence)
    plot["arousal_data"].append(arousal)

    plot["line1"].set_data(range(len(plot["valence_data"])), plot["valence_data"])
    plot["line2"].set_data(range(len(plot["arousal_data"])), plot["arousal_data"])

    plot["val_text"].set_text(f"V: {valence:.2f}")
    plot["arousal_text"].set_text(f"A: {arousal:.2f}")

    # Adjust axes limits
    plot["ax"].relim()
    plot["ax"].autoscale_view()

    # Redraw the plot
    plt.pause(0.001)

def epoch(data, samples_epoch, samples_overlap=0):
    """Extract epochs from a time series.

    Given a 2D array of the shape [n_samples, n_channels]
    Creates a 3D array of the shape [wlength_samples, n_channels, n_epochs]

    Args:
        data (numpy.ndarray or list of lists): data [n_samples, n_channels]
        samples_epoch (int): window length in samples
        samples_overlap (int): Overlap between windows in samples

    Returns:
        (numpy.ndarray): epoched data of shape
    """

    if isinstance(data, list):
        data = np.array(data)

    n_samples, n_channels = data.shape

    samples_shift = samples_epoch - samples_overlap

    n_epochs = int(
        np.floor((n_samples - samples_epoch) / float(samples_shift)) + 1)

    # Markers indicate where the epoch starts, and the epoch contains samples_epoch rows
    markers = np.asarray(range(0, n_epochs + 1)) * samples_shift
    markers = markers.astype(int)

    # Divide data in epochs
    epochs = np.zeros((samples_epoch, n_channels, n_epochs))

    for i in range(0, n_epochs):
        epochs[:, :, i] = data[markers[i]:markers[i] + samples_epoch, :]

    return epochs
