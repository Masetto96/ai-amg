import numpy as np
from pylsl import StreamInlet, resolve_byprop
from music_gen.ableton_controllers import AbletonMetaController
from emotion_detection import utils 

class Band:
    Delta = 0
    Theta = 1
    Alpha = 2
    Beta = 3

# Length of the EEG data buffer (in seconds)
BUFFER_LENGTH = 5

# Length of the epochs used to compute the FFT (in seconds)
EPOCH_LENGTH = 1

# Amount of overlap between two consecutive epochs (in seconds)
OVERLAP_LENGTH = 0.8

# Amount to 'shift' the start of each next consecutive epoch
SHIFT_LENGTH = EPOCH_LENGTH - OVERLAP_LENGTH

BAND_BUFFER_LENGTH = 10

# All the 4 electrodes
INDEX_CHANNEL = [0, 1, 2, 3]

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

    # Initialize the scalers
    arousal_scaler = utils.DynamicScaler()
    valence_scaler = utils.DynamicScaler()

    # Get the stream info and description
    info = inlet.info()
    description = info.desc()

    # for the Muse 2016 fs should be 256
    # TODO: do logging more beutifully
    fs = int(info.nominal_srate())
    print("EEG Sampling frequency: ", fs, "Hz")
    print("Data will be collected in a buffer of", BUFFER_LENGTH, "second chunks")
    print("FFT will be computed on each", EPOCH_LENGTH, "second epoch in the buffer with an overlap of", OVERLAP_LENGTH, "seconds", "\n")

    # Initialize buffers for all channels
    eeg_buffer = np.zeros((int(fs * BUFFER_LENGTH), len(INDEX_CHANNEL))) # shape [samples, channels]

    filter_state = None
    # Wait until the buffer is fully populated
    print("Reading your brain waves until buffer and scalers are ready.")
    while np.any(eeg_buffer == 0):
        eeg_data, _ = inlet.pull_chunk(timeout=1, max_samples=int(SHIFT_LENGTH * fs))
        ch_data = np.array(eeg_data)[:, INDEX_CHANNEL]  # Ensure it matches the buffer dimensions
        eeg_buffer, filter_state = utils.update_buffer(
            eeg_buffer, ch_data, notch=True, filter_state=filter_state
        )
    
    # # Compute the number of epochs in the buffer length
    # n_win_test = int(np.floor((BUFFER_LENGTH - EPOCH_LENGTH) / SHIFT_LENGTH + 1))
    # # bands will be ordered: [delta, theta, alpha, beta]
    # # Initialize the band power buffer for all channels
    # band_buffer = np.zeros((n_win_test, 4, len(INDEX_CHANNEL)))  # Shape: (n_win_test, bands, channels)
    band_buffer = np.zeros((BAND_BUFFER_LENGTH, 4, len(INDEX_CHANNEL)))
    try:
        while True:
            eeg_data, _ = inlet.pull_chunk(timeout=1, max_samples=int(SHIFT_LENGTH * fs))
            ch_data = np.array(eeg_data)[:, INDEX_CHANNEL]

            eeg_buffer, filter_state = utils.update_buffer(
                eeg_buffer, ch_data, notch=True, filter_state=filter_state
            )
            data_epoch = utils.get_last_epoch(eeg_buffer, EPOCH_LENGTH * fs)

            # FFT on one epoch across all channels
            band_powers = np.array([utils.compute_band_powers(data_epoch[:, ch].reshape(-1, 1), fs)
                        for ch in range(data_epoch.shape[1])])

            # Shift and update the band buffer
            band_buffer = np.roll(band_buffer, -1, axis=0)  # Shift to make space for new epoch
            band_buffer[-1, :, :] = band_powers  # Add the latest band powers

            if np.any(band_buffer == 0).any():
                continue # wait until there enough samples in the buffer

            # Aggregate across band buffer
            smooth_band_powers = np.mean(band_buffer, axis=0)  # Shape: (bands, channels)

            # TODO: is this correct?
            aggregated_alpha = np.mean(smooth_band_powers[Band.Alpha])
            aggregated_beta = np.mean(smooth_band_powers[Band.Beta])
            aggregated_theta = np.mean(smooth_band_powers[Band.Theta])

            valence = aggregated_theta / aggregated_alpha # anxiety protocol
            arousal = aggregated_beta / aggregated_alpha # rafa ramirez protocol
            # TODO: clamp the raw metrics to a wide range
            arousal_scaler.update(arousal)
            valence_scaler.update(valence)

            if not arousal_scaler.ready or not valence_scaler.ready:
                continue  # Wait for enough samples for scaling

            scaled_arousal = arousal_scaler.scale(arousal)
            scaled_valence = valence_scaler.scale(valence)
            controller.update_metrics(valence=scaled_valence, arousal=scaled_arousal)

            utils.live_plot(scaled_valence, scaled_arousal, title="Scaled")
            utils.live_plot(valence, arousal, title="Not Scaled")

    except KeyboardInterrupt:
        print("Closing!")