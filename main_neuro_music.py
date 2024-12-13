import logging
import numpy as np
from pylsl import StreamInlet, resolve_byprop
from music_gen.controllers import AbletonMetaController
from emotion_detection import utils

class Band:
    Delta = 0
    Theta = 1
    Alpha = 2
    Beta = 3

# Length of the EEG data buffer (in seconds)
BUFFER_LENGTH = 4

# Length of the epochs used to compute the FFT (in seconds)
EPOCH_LENGTH = 2

# Amount of overlap between two consecutive epochs (in seconds)
OVERLAP_LENGTH = 1.5

# Amount to 'shift' the start of each next consecutive epoch
SHIFT_LENGTH = EPOCH_LENGTH - OVERLAP_LENGTH

BAND_BUFFER_LENGTH = 10

# All the 4 electrodes
INDEX_CHANNEL = [0, 1, 2, 3]

if __name__ == "__main__":

    # Configure the global logger
    logging.basicConfig(
        filename='system.log',
        filemode='w',  # This will overwrite the log file on each run
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'  # More compact time format
    )
    logger = logging.getLogger(__name__)

    logger.info("Starting the magic")

    # Search for active LSL streams
    streams = resolve_byprop('type', 'EEG', timeout=2)
    if len(streams) == 0:
        logger.error('Cannot find EEG stream.')
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
    fs = int(info.nominal_srate())
    logger.info("FFT will be computed on %d second epoch in the buffer with an overlap of %f seconds", EPOCH_LENGTH, OVERLAP_LENGTH)

    # Initialize buffers for all channels
    eeg_buffer, filter_state = utils.initialize_buffer(fs, BUFFER_LENGTH, INDEX_CHANNEL)

    # Wait until the buffer is fully populated
    logger.info("Reading your brain waves until buffer and scalers are ready.")
    eeg_buffer, filter_state = utils.populate_initial_buffer(inlet, eeg_buffer, filter_state, SHIFT_LENGTH, fs, INDEX_CHANNEL)

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
            # aggregate across channels
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

            # utils.live_plot(scaled_valence, scaled_arousal, title="Scaled")
            # utils.live_plot(valence, arousal, title="Not Scaled")

    except KeyboardInterrupt:
        logger.info("Closing application")
        controller.stop()
