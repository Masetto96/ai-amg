# -*- coding: utf-8 -*-
"""
Multi-Channel EEG Data Acquisition

This script connects to an EEG data stream, collects data from all channels,
and buffers the data for future use or analysis.

Adapted from https://github.com/NeuroTechX/bci-workshop
"""

import numpy as np  # Module that simplifies computations on matrices
from pylsl import StreamInlet, resolve_byprop  # Module to receive EEG data
import utils  # Utility functions for buffering

""" EXPERIMENTAL PARAMETERS """
BUFFER_LENGTH = 5  # Length of the EEG data buffer (in seconds)
SHIFT_LENGTH = 1  # Amount to 'shift' the start of each next epoch (1 second)

if __name__ == "__main__":

    """ 1. CONNECT TO EEG STREAM """

    # Search for an active EEG stream
    print('Looking for an EEG stream...')
    streams = resolve_byprop('type', 'EEG', timeout=2)
    if len(streams) == 0:
        raise RuntimeError("Can't find EEG stream.")

    # Set the active EEG stream to an inlet and apply time correction
    print("Start acquiring data")
    inlet = StreamInlet(streams[0], max_chunklen=12)
    eeg_time_correction = inlet.time_correction()

    # Get the stream info and description
    info = inlet.info()
    fs = int(info.nominal_srate())  # Get the sampling frequency
    channel_count = info.channel_count()  # Get the number of available channels

    """ 2. INITIALIZE BUFFER """

    # Initialize an EEG data buffer for all channels
    eeg_buffer = np.zeros((int(fs * BUFFER_LENGTH), channel_count))
    filter_state = None  # for use with the notch filter

    print("Press Ctrl-C in the console to break the while loop.")

    try:
        while True:

            """ 3. ACQUIRE AND BUFFER DATA """
            # Obtain EEG data from the LSL stream
            eeg_data, timestamp = inlet.pull_chunk(
                timeout=1, max_samples=int(SHIFT_LENGTH * fs))

            # Convert the data to a NumPy array and keep all channels
            ch_data = np.array(eeg_data)

            # Update the EEG buffer with the new data for all channels
            eeg_buffer, filter_state = utils.update_buffer(
                eeg_buffer, ch_data, notch=True, filter_state=filter_state)

            # Print the updated buffer contents (optional)
            print("EEG buffer updated with latest data for all channels")

    except KeyboardInterrupt:
        print("Closing!")
