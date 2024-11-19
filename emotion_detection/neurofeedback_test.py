# -*- coding: utf-8 -*-
"""
Multi-Channel EEG Data Acquisition

This script connects to an EEG data stream, collects data from all channels,
and buffers the data for future use or analysis.

Adapted from https://github.com/NeuroTechX/bci-workshop
"""

import numpy as np
from pylsl import StreamInlet, resolve_byprop
from utils import update_buffer  # Import the required buffer update utility

# Configuration Parameters
BUFFER_LENGTH = 5  # EEG buffer length in seconds
SHIFT_LENGTH = 1   # Time (in seconds) to shift buffer for new data
NOTCH_FILTER = True  # Enable/Disable notch filtering

def connect_to_eeg_stream():
    """
    Resolves and connects to the first available EEG stream using LSL.
    
    Returns:
        inlet (StreamInlet): LSL StreamInlet for the EEG data
        fs (int): Sampling frequency of the EEG stream
        channel_count (int): Number of EEG channels
    """
    print("Looking for an EEG stream...")
    streams = resolve_byprop('type', 'EEG', timeout=2)
    if not streams:
        raise RuntimeError("No EEG streams found.")
    
    print("Connecting to the EEG stream...")
    inlet = StreamInlet(streams[0], max_chunklen=12)
    fs = int(inlet.info().nominal_srate())
    channel_count = inlet.info().channel_count()
    return inlet, fs, channel_count

def initialize_buffer(fs, channel_count, buffer_length=BUFFER_LENGTH):
    """
    Initializes an empty buffer for EEG data.

    Args:
        fs (int): Sampling frequency
        channel_count (int): Number of EEG channels
        buffer_length (int): Buffer length in seconds
    
    Returns:
        eeg_buffer (np.ndarray): Zero-initialized buffer
    """
    return np.zeros((int(fs * buffer_length), channel_count))

def main():
    """
    Main loop to acquire EEG data and buffer it in real-time.
    """
    try:
        # Step 1: Connect to EEG stream
        inlet, fs, channel_count = connect_to_eeg_stream()
        print(f"Number of channels {channel_count}")
        eeg_buffer = initialize_buffer(fs, channel_count)
        filter_state = None

        print("Press Ctrl+C to stop data acquisition.")
        while True:
            # Step 2: Acquire data from the stream
            eeg_data, timestamps = inlet.pull_chunk(
                timeout=1, max_samples=int(SHIFT_LENGTH * fs)
            )
                 
            if not eeg_data:
                print("No data received from the stream.")
                continue

            # Convert data to NumPy array
            new_data = np.array(eeg_data)

            # Step 3: Update buffer
            eeg_buffer, filter_state = update_buffer(
                eeg_buffer, new_data, notch=NOTCH_FILTER, filter_state=filter_state
            )

            print(eeg_buffer)

            print("Buffer updated with new data.")
            # Additional processing can be added here (e.g., feature extraction)

    except KeyboardInterrupt:
        print("\nData acquisition stopped by the user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Closing EEG stream.")

if __name__ == "__main__":
    main()
