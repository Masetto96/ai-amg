import time
import random
import json
import mido
import threading
from pythonosc import dispatcher, osc_server

# Global parameters (initial values)
valence = 0.5
arousal = 0.5

def update_valence_handler(unused_addr, val):
    global valence
    valence = val
    print(f"Updated Valence: {valence}")

def update_arousal_handler(unused_addr, ar):
    global arousal
    arousal = ar
    print(f"Updated Arousal: {arousal}")


# OSC handler to update continuous values
def osc_handler(address, *args):
    global valence, arousal
    # Assuming OSC messages are sent as: /emotion valence arousal
    if address == "/emotion" and len(args) >= 2:
        valence, arousal = args[:2]
        # Optionally, add smoothing here
        print(f"Received OSC: Valence={valence}, Arousal={arousal}")

disp = dispatcher.Dispatcher()
disp.map("/x", update_valence_handler)
disp.map("/y", update_arousal_handler)

# disp.map("/emotion", osc_handler)

server = osc_server.ThreadingOSCUDPServer(("192.168.0.27", 5005), disp)
print("OSC server running on", server.server_address)
osc_thread = threading.Thread(target=server.serve_forever)
osc_thread.daemon = True
osc_thread.start()

# Set up Virtual MIDI Output
available_ports = mido.get_output_names()
print("Opening MIDI:", available_ports[1])
midi_out = mido.open_output(available_ports[1])
# midi_out = mido.open_output("python")

# Mapping functions for tempo and dynamics
def map_arousal_to_tempo(arousal):
    return 60 + (arousal * 80)  # BPM between 60 and 140

def map_arousal_to_velocity(arousal):
    return int(40 + (arousal * 50))  # MIDI velocity from 40 to 90

with open('music_gen/vamps.json', 'r') as f:
    MODES_DATA = json.load(f)


def update_harmonic_mode(valence):
    if 0.83 <= valence <= 1.00:
        mode_name = "lydian"
    elif 0.78 <= valence < 0.83:
        mode_name = "ionian"
    elif 0.64 <= valence < 0.78:
        mode_name = "mixolydian"
    elif 0.32 <= valence < 0.64:
        mode_name = "dorian"
    elif 0.16 <= valence < 0.32:
        mode_name = "aeolian"
    elif 0.00 <= valence < 0.16:
        mode_name = "phrygian"
    else:
        raise ValueError(f"Valence out of range: {valence}")
    
    return mode_name, MODES_DATA[mode_name]

# Sequencer configuration
bars_per_mode = 4
steps_per_bar = 8  # Assuming 16th notes for the sequencer grid

def sequencer_loop():
    global valence, arousal
    bar_counter = 0
    current_mode_name, current_mode_data = update_harmonic_mode(valence)
    
    while True:
        # Every new chord progression cycle, update the harmonic mode based on valence
        if bar_counter % bars_per_mode == 0:
            current_mode_name, current_mode_data = update_harmonic_mode(valence)
            print(f"[*] Updated Harmonic Mode to {current_mode_name} given valence {valence}")
        
        # For each bar, cycle through the chords in the mode's implementation.
        # If there are fewer chords than bars in the progression, cycle them.
        chord_index = bar_counter % len(current_mode_data["implementation"])
        current_chord = current_mode_data["implementation"][chord_index]
        print(f"Bar {bar_counter+1}: Using chord {current_chord}")

        # Determine current tempo and timing based on arousal
        tempo = map_arousal_to_tempo(arousal)
        interval = (60 / tempo) / 2  # Duration for an 8th note
        
        # For each step in the bar
        for step in range(steps_per_bar):
            # Use arousal to probabilistically decide note triggering (rhythmic roughness)
            if random.random() < arousal:
                # Instead of a continuous pitch, choose a note from the current chord
                note = random.choice(current_chord)
                velocity = map_arousal_to_velocity(arousal)
                msg_on = mido.Message('note_on', note=note, velocity=velocity)
                midi_out.send(msg_on)
                print(f"ON: note={note}, velocity={velocity}")

                # Schedule note off after a fraction of the interval
                time.sleep(interval * 0.9)
                msg_off = mido.Message('note_off', note=note, velocity=0)
                midi_out.send(msg_off)
            else:
                time.sleep(interval)
        bar_counter += 1

if __name__ == "__main__":
    try:
        sequencer_loop()
    except KeyboardInterrupt:
        print("Shutting down...")
        server.shutdown()
        midi_out.close()