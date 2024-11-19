import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt
import time

class MockEEGProcessor:
    def __init__(self, sampling_rate=250):  # 15000 samples / 60 seconds = 250 Hz
        self.sampling_rate = sampling_rate
        self.buffer_size = sampling_rate  # 1 second buffer
        self.channels = ['TP9', 'AF7', 'AF8', 'TP10']
        self.buffers = {ch: [] for ch in self.channels}
        
        # Create filters
        self.alpha_b, self.alpha_a = self.create_bandpass_filter(8, 13)
        self.beta_b, self.beta_a = self.create_bandpass_filter(13, 30)
    
    def create_bandpass_filter(self, lowcut, highcut, order=4):
        nyquist = 0.5 * self.sampling_rate
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(order, [low, high], btype='band')
        return b, a
    
    def process_sample(self, sample_dict):
        # Add new samples to buffers
        for ch in self.channels:
            self.buffers[ch].append(sample_dict[ch])
            # Keep buffer at fixed size
            if len(self.buffers[ch]) > self.buffer_size:
                self.buffers[ch].pop(0)
    
    def calculate_band_power(self, data, b, a):
        if len(data) < self.buffer_size:
            return 0
        # Apply bandpass filter
        filtered = filtfilt(b, a, data)
        # Calculate power (mean squared amplitude)
        power = np.mean(filtered ** 2)
        return power
    
    def get_band_powers(self):
        powers = {
            'alpha': {},
            'beta': {}
        }
        
        for ch in self.channels:
            if len(self.buffers[ch]) == self.buffer_size:
                data = np.array(self.buffers[ch])
                powers['alpha'][ch] = self.calculate_band_power(data, self.alpha_b, self.alpha_a)
                powers['beta'][ch] = self.calculate_band_power(data, self.beta_b, self.beta_a)
        
        return powers

def simulate_realtime_processing(csv_file, speed_factor=1.0):
    """
    Simulate real-time processing of EEG data
    speed_factor: 1.0 means real-time, 2.0 means 2x faster, etc.
    """
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Initialize EEG processor
    processor = MockEEGProcessor()
    
    # Get initial timestamp
    start_time = time.time()
    first_eeg_timestamp = df['timestamps'].iloc[0]
    
    for idx, row in df.iterrows():
        # Calculate delay for real-time simulation
        current_eeg_timestamp = row['timestamps']
        elapsed_eeg_time = current_eeg_timestamp - first_eeg_timestamp
        target_real_time = elapsed_eeg_time / speed_factor
        
        # Wait until the appropriate time
        current_elapsed = time.time() - start_time
        if current_elapsed < target_real_time:
            time.sleep(target_real_time - current_elapsed)
        
        # Process the new sample
        sample = {ch: row[ch] for ch in processor.channels}
        processor.process_sample(sample)
        
        # Calculate and print band powers
        if idx % 25 == 0:  # Print every 25 samples (10 times per second at 250 Hz)
            powers = processor.get_band_powers()
            print(f"\nTimestamp: {current_eeg_timestamp:.3f}")
            print("Alpha powers:", {ch: f"{p:.2f}" for ch, p in powers['alpha'].items()})
            print("Beta powers:", {ch: f"{p:.2f}" for ch, p in powers['beta'].items()})

# Usage example
if __name__ == "__main__":
    csv_file = "recording_2024-11-05-14.33.15.csv"  # Replace with your CSV file path
    simulate_realtime_processing(csv_file, speed_factor=1.0)