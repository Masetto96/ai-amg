"""
https://github.com/ideoforms/AbletonOSC
"""

import threading
import socket
import sys
import time
import random
from pythonosc import udp_client
from music_gen.helpers import chord_to_midi, transpose_midi_chords

from music_gen.chord_generator import ChordProgressionGenerator
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from typing import List, Tuple, Optional, Any, Callable

class OSCBase:
    """Base class for OSC communication"""

    def __init__(self, client: udp_client.SimpleUDPClient):
        self.client = client

    def send_message(self, address: str, params: Any) -> None:
        """Send an OSC message with optional delay to prevent flooding"""
        self.client.send_message(address, params)
        time.sleep(0.01)  # Prevent message flooding


class ClipAPI(OSCBase):
    """Controls clip operations and properties"""

    def fire_clip(self, track_id: int, clip_id: int) -> None:
        self.send_message("/live/clip/fire", [track_id, clip_id])

    def stop_clip(self, track_id: int, clip_id: int) -> None:
        self.send_message("/live/clip/stop", [track_id, clip_id])

    def remove_notes(self, track_id: int, clip_id: int) -> None:
        self.send_message("/live/clip/remove/notes", [track_id, clip_id])

    def add_notes(
        self,
        track_id: int,
        clip_id: int,
        notes: List[Tuple[int, float, float, int, int]],
    ) -> None:
        """
        Add MIDI notes to clip

        Args:
            track_id: Track index
            clip_id: Clip index
            notes: List of tuples (pitch, start_time, duration, velocity, mute)
        """
        for note in notes:
            self.send_message("/live/clip/add/notes", [track_id, clip_id] + list(note))


class ClipSlotAPI(OSCBase):
    """Controls clip slot operations"""

    def create_clip(
        self, track_index: int, clip_index: int, length_in_bars: int
    ) -> None:
        self.send_message(
            "/live/clip_slot/create_clip", [track_index, clip_index, length_in_bars]
        )

    def delete_clip(self, track_index: int, clip_index: int) -> None:
        self.send_message("/live/clip_slot/delete_clip", [track_index, clip_index])

    def duplicate_clip(
        self,
        track_index: int,
        clip_index: int,
        target_track_index: int,
        target_clip_index: int,
    ) -> None:
        self.send_message(
            "/live/clip_slot/duplicate_clip",
            [track_index, clip_index, target_track_index, target_clip_index],
        )


class SongAPI(OSCBase):
    """Controls global song parameters and playback"""

    def start_playback(self) -> None:
        self.send_message("/live/clip/fire", [0, 0])  # track 0, slot 0
        self.send_message("/live/clip/fire", [1, 0])  # track 1, slot 0

    def start_listen_to_beats(self) -> None:
        self.send_message("/live/song/start_listen/beat", [])

    def set_tempo(self, bpm: float) -> None:
        self.send_message("/live/song/set/tempo", bpm)


class DeviceAPI(OSCBase):
    """Controls device parameters"""

    def set_parameter(
        self, track_index: int, device_index: int, parameter_index: int, value: float
    ) -> None:
        self.send_message(
            "/live/device/set/parameter/value",
            [track_index, device_index, parameter_index, value],
        )


class AbletonOSCController:
    """Main controller class that coordinates all APIs"""
    def __init__(self, send_port: int = 11000, ip: str = "192.168.0.25"):
        self.client = udp_client.SimpleUDPClient(ip, send_port)

        # Initialize API components
        self.song = SongAPI(self.client)
        self.clip_slot = ClipSlotAPI(self.client)
        self.clip = ClipAPI(self.client)
        self.device = DeviceAPI(self.client)

    def create_midi_clip(
        self,
        track_index: int,
        clip_index: int,
        length_in_bars: int,
        midi_notes: List[Tuple],
    ) -> None:
        """Create a MIDI clip and add notes to it"""
        self.clip_slot.create_clip(track_index, clip_index, length_in_bars)
        self.clip.add_notes(track_index, clip_index, midi_notes)

    def remove_and_add_notes(
        self, track_index: int, clip_index: int, midi_notes: List[Tuple]
    ):
        self.clip.remove_notes(track_index, clip_index)
        self.clip.add_notes(track_index, clip_index, midi_notes)


class AbletonMetaController:
    """
    Piano is on track 1, zero index; Arpeggiator is on track 2; Bass is on track 3
    """

    def __init__(self):
        self.controller = AbletonOSCController()
        self.generator = ChordProgressionGenerator()
        self.valence = None
        self.arousal = None

    def setup(self):
        self._start_beat_listener()
        self.controller.create_midi_clip(0, 0, 16, [])
        self.controller.create_midi_clip(1, 0, 16, [])

    def update_metrics(self, valence, arousal):
        """Update the alpha and theta metrics dynamically."""
        self.valence = valence
        self.arousal = arousal
        self.modulate_piano(self.valence, self.arousal)
        self.modulate_arpeggiator(self.valence, self.arousal)

    def _handle_beat(self, address: str, *args) -> None:
        """Handle incoming beat messages"""
        beat_number = args[0]
        print(f"Current beat: {beat_number}")
        if beat_number == 16:
            # TODO: is it maybe a better idea to generate at the beat 1?
            # Actually the best would be to generate it in advance, put in the clip and then play it at beat 1 or something?
            print("Beat 16 reached - generating new progression")
            # Generates and adds a new progression
            self.add_progression_to_ableton(self.arousal, self.valence)  

    def add_progression_to_ableton(self, valence: float, arousal: float) -> None:
        progression = self.generator.generate_progression(valence, arousal)
        midi_chords, _ = chord_to_midi(progression)
        midi_chords = transpose_midi_chords(midi_chords, -12)
        # remove all notes from clip and add new ones
        self.controller.remove_and_add_notes(
            0, 0, midi_chords
        )  # piano track 1, zero index
        self.controller.remove_and_add_notes(
            1, 0, midi_chords
        )  # arpeggiator track 2
        self.controller.remove_and_add_notes(2, 0, midi_chords)  # noise track 3
    def modulate_piano(self, valence: float, arousal: float) -> None:
        growl = ((arousal + 1) / 2) * (127 - 1) + 1
        force = ((valence + 1) / 2) * (127 - 1) + 1
        self.controller.device.set_parameter(0, 0, 1, growl)
        self.controller.device.set_parameter(0, 0, 2, force)

    def modulate_arpeggiator(self, valence: float, arousal: float) -> None:
        arp_rate = ((arousal + 1) / 2) * (10 - 5) + 5 # in the range 5-10
        self.controller.device.set_parameter(1, 0, 5, arp_rate) # parameter 5 of ableton arpeggiator controlling rate
        shape = max(0, min((valence + 1) / 2, 1)) # in the range 0-1
        self.controller.device.set_parameter(1, 1, 4, shape) # parameter 4 of ableton wavetable controlling shapes


    def _start_beat_listener(self, receive_port: int = 11001):
        """Start the OSC server to listen for beats"""
        def start_server(ip="0.0.0.0", port=receive_port):
            dispatcher = Dispatcher()
            dispatcher.map("/live/song/get/beat", self._handle_beat)
            server = BlockingOSCUDPServer((ip, port), dispatcher)
            print(f"Listening for beats on {ip}:{port}")
            server.serve_forever()
            # sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # server.socket = sock
            # server.socket.bind((ip, port))

            # try:

            # except OSError as e:
            #     print(f"Error: Could not start beat listener. Port {port} might be in use. -- {e}")
            #     print("Try running: taskkill /F /IM python.exe")
            #     sys.exit(1)

        # Start server in background thread
        self.server_thread = threading.Thread(target=start_server)
        self.server_thread.daemon = True
        self.server_thread.start()

        # Start listening for beats
        print("Starting beat listener...")
        self.controller.song.start_listen_to_beats()

        # TODO: add a stop function to stop everything











    # def modulate_drum(self, valence: float, arousal: float) -> None:
    #     filter_freq = compute_weighted_average(valence, arousal, output_range=(60, 140))
    #     self.controller.device.set_parameter(3, 0, 5, filter_freq)

    # def modulate_bass(self, valence: float, arousal: float) -> None:
    #     drive = compute_weighted_average(
    #         valence, arousal, weight_valence=0.3, weight_arousal=0.7
    #     )
    #     self.controller.device.set_parameter(2, 0, 5, drive)