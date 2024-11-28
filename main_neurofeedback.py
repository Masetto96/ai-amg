# -*- coding: utf-8 -*-
"""
Estimate Relaxation from Band Powers

This example shows how to buffer, epoch, and transform EEG data from a single
electrode into values for each of the classic frequencies (e.g. alpha, beta, theta)
Furthermore, it shows how ratios of the band powers can be used to estimate
mental state for neurofeedback.

The neurofeedback protocols described here are inspired by
*Neurofeedback: A Comprehensive Review on System Design, Methodology and Clinical Applications* by Marzbani et. al

Adapted from https://github.com/NeuroTechX/bci-workshop
"""

import numpy as np  # Module that simplifies computations on matrices
from pylsl import StreamInlet, resolve_byprop  # Module to receive EEG data
from emotion_detection import utils  # Our own utility functions
from music_gen.ableton_controllers import AbletonMetaController
import matplotlib.pyplot as plt  # Module used for plotting


# Handy little enum to make code more readable
class Band:
    Delta = 0
    Theta = 1
    Alpha = 2
    Beta = 3

# Modify these to change aspects of the signal processing

# Length of the EEG data buffer (in seconds)
# This buffer will hold last n seconds of data and be used for calculations
BUFFER_LENGTH = 5

# Length of the epochs used to compute the FFT (in seconds)
EPOCH_LENGTH = 1

# Amount of overlap between two consecutive epochs (in seconds)
OVERLAP_LENGTH = 0.8

# Amount to 'shift' the start of each next consecutive epoch
SHIFT_LENGTH = EPOCH_LENGTH - OVERLAP_LENGTH

# Index of the channel(s) (electrodes) to be used
# 0 = left ear, 1 = left forehead, 2 = right forehead, 3 = right ear
INDEX_CHANNEL = [0] 

if __name__ == "__main__":

    # Search for active LSL streams
    streams = resolve_byprop('type', 'EEG', timeout=2)
    if len(streams) == 0:
        raise RuntimeError('Cannot find EEG stream.')

    # Set active EEG stream to inlet and apply time correction
    inlet = StreamInlet(streams[0], max_chunklen=12)
    eeg_time_correction = inlet.time_correction()

    # Initialize the Ableton controller
    controller = AbletonMetaController()
    controller.setup()

    arousal_scaler = utils.DynamicScaler()
    valence_scaler = utils.DynamicScaler()

    # Get the stream info and description
    info = inlet.info()
    description = info.desc()

    # Get the sampling frequency
    # This is an important value that represents how many EEG data points are
    # collected in a second. This influences our frequency band calculation.
    # for the Muse 2016, this should always be 256
    fs = int(info.nominal_srate())
    print("EEG Sampling frequency: ", fs, "Hz")

    # Initialize raw EEG data buffer
    eeg_buffer = np.zeros((int(fs * BUFFER_LENGTH), 1))
    filter_state = None  # For use with the notch filter

    # Wait until the buffer is fully populated
    print("Start reading your brain waves")
    while np.any(eeg_buffer == 0): # this is to avoide the initial computation based on initial zeros in the buffer
        print("Reading more of it")
        eeg_data, timestamp = inlet.pull_chunk(timeout=1, max_samples=int(SHIFT_LENGTH * fs))

        # Only keep the channel we're interested in
        ch_data = np.array(eeg_data)[:, INDEX_CHANNEL]

        # Update EEG buffer with the new data
        eeg_buffer, filter_state = utils.update_buffer(eeg_buffer, ch_data, notch=True, filter_state=filter_state)

    print("Buffer initialized! Starting computations.")
    # Compute the number of epochs in "buffer_length"
    n_win_test = int(np.floor((BUFFER_LENGTH - EPOCH_LENGTH) /
                              SHIFT_LENGTH + 1))

    # Initialize the band power buffer
    # bands will be ordered: [delta, theta, alpha, beta]
    band_buffer = np.zeros((n_win_test, 4))

    print('Press Ctrl-C in the console to break')
    try:
        # The following loop acquires data, computes band powers, and calculates neurofeedback metrics based on those band powers
        while True:

            # Obtain EEG data from the LSL stream
            eeg_data, timestamp = inlet.pull_chunk(
                timeout=1, max_samples=int(SHIFT_LENGTH * fs))

            # Only keep the channel we're interested in
            ch_data = np.array(eeg_data)[:, INDEX_CHANNEL]

            # Update EEG buffer with the new data
            eeg_buffer, filter_state = utils.update_buffer(
                eeg_buffer, ch_data, notch=True,
                filter_state=filter_state)

            # Get newest samples from the buffer
            data_epoch = utils.get_last_data(eeg_buffer,
                                             EPOCH_LENGTH * fs)

            # Compute band powers
            band_powers = utils.compute_band_powers(data_epoch, fs)
            band_buffer, _ = utils.update_buffer(band_buffer,
                                                 np.asarray([band_powers]))
                        
            smooth_band_powers = np.mean(band_buffer, axis=0) # This helps to smooth out noise

            # Alpha Protocol:
            # Simple redout of alpha power, divided by delta waves in order to rule out noise
            alpha_metric = smooth_band_powers[Band.Alpha] / \
                smooth_band_powers[Band.Delta]
            # print('Alpha Relaxation: ', alpha_metric)

            # Alpha/Theta Protocol:
            # This is another popular neurofeedback metric for stress reduction
            # Higher theta over alpha is supposedly associated with reduced anxiety
            valence = smooth_band_powers[Band.Theta] / \
                smooth_band_powers[Band.Alpha]

            # Rafa Ramirez Protocol
            # the beta/alpha ratio is a reasonable indicator of the arousal level
            arousal = smooth_band_powers[Band.Beta] / \
                smooth_band_powers[Band.Alpha]

            # watch out, ugly code
            arousal_scaler.update(arousal)
            valence_scaler.update(valence)
            scaled_arousal = arousal_scaler.scale(alpha_metric)
            scaled_valence = valence_scaler.scale(valence)
            controller.update_metrics(valence=scaled_valence, arousal=scaled_arousal)

            print('Theta/Alpha (V): ', valence)
            # print('Scaled (V): ', scaled_valence)
            print('Beta/Alpha:(A)', arousal)
            # print('Scaled (A): ', scaled_arousal)
            print("-"*80)
            utils.live_plot(scaled_valence, scaled_arousal)

            # Beta Protocol:
            # Beta waves have been used as a measure of mental activity and concentration
            # This beta over theta ratio is commonly used as neurofeedback for ADHD
            # beta_metric = smooth_band_powers[Band.Beta] / \
            #     smooth_band_powers[Band.Theta]
            # print('Beta Concentration: ', beta_metric)


    except KeyboardInterrupt:
        print('Closing!')