"""
https://github.com/ideoforms/AbletonOSC
"""

import threading
import time
from typing import Any, List, Tuple
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from music_gen.chord_generator import ChordProgressionGenerator
from music_gen import helpers


class OSCBase:
    """Base class for OSC communication"""

    def __init__(self, client: udp_client.SimpleUDPClient):
        self.client = client

    def send_message(self, address: str, params: Any) -> None:
        """Send an OSC message with optional delay"""
        self.client.send_message(address, params)
        time.sleep(0.01)  # Prevent message flooding


class ClipAPI(OSCBase):
    """Controls clip operations and properties"""

    def fire_clip(self, track_id: int, clip_id: int) -> None:
        self.send_message("/live/clip/fire", [track_id, clip_id])

    def stop_clip(self, track_id: int, clip_id: int) -> None:
        self.send_message("/live/clip/stop", [track_id, clip_id])

    def remove_notes(self, track_id: int, clip_id: int, bar_number:int) -> None:
        # TODO: add the option to remove notes between a time range given bar number param
        self.send_message("/live/clip/remove/notes", [track_id, clip_id])

    # def add_notes(
    #     self,
    #     track_id: int,
    #     clip_id: int,
    #     notes: List[Tuple[int, float, float, int, int]],
    #     bar_number:int
    # ) -> None:
    #     """
    #     Add MIDI notes to clip
    #     Args:
    #         track_id: Track index
    #         clip_id: Clip index
    #         notes: List of tuples (pitch, start_time, duration, velocity, mute)
    #     """
    #     for note in notes:
    #         # TODO: add the option to add notes between a time range given bar number param
    #         self.send_message("/live/clip/add/notes", [track_id, clip_id] + list(note))


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
    def __init__(self, send_port: int = 11000, ip: str = "192.168.16.70"):
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
        # self.clip.add_notes(track_index, clip_index, midi_notes)

    # def remove_and_add_notes(
    #     self, track_index: int, clip_index: int, midi_notes: List[Tuple], bar_number:int):
    #     self.clip.remove_notes(track_index, clip_index, bar_number)
    #     self.clip.add_notes(track_index, clip_index, midi_notes, bar_number)


class AbletonMetaController:
    """
    Piano is on track 1, zero index; Arpeggiator is on track 2; Bass is on track 3
    """
    def __init__(self):
        self.controller = AbletonOSCController()
        self.generator = ChordProgressionGenerator()
        self.valence = None
        self.arousal = None
        self.server_thread = None

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
        self.modulate_global(self.valence, self.arousal)

    def _handle_beat(self, *args) -> None:
        """Handle incoming beat messages"""
        beat_number = args[0]
        print(f"Current beat: {beat_number}")
        # if beat_number == 1:
        #     self.add_chord_to_ableton(self.arousal, self.valence, bar_number=8) # add bar number parameter to decide when in the clip to generate the chord
        # if beat_number == 9:
        #     self.add_chord_to_ableton(self.arousal, self.valence, bar_number=1)

    # def add_chord_to_ableton(self, valence: float, arousal: float, bar_number:int) -> None:
    #     # TODO: use bar number to remove and add notes in the right time range, that is when the other chord is playing
    #     chord_event, root_midi_note = self.generator.generate_next_chord(valence, arousal)
    #     ableton_notes = helpers.chord_event_to_midi_tuples(chord_event)
    #     # remove all notes from clip and add new ones
    #     self.controller.remove_and_add_notes(
    #         0, 0, ableton_notes, bar_number
    #     )  # piano track 1, zero index
    #     self.controller.remove_and_add_notes(
    #         1, 0, ableton_notes, bar_number,
    #     )  # arpeggiator track 2

    def modulate_piano(self, valence: float, arousal: float) -> None:
        growl = arousal * (127 - 1) + 1  # Scale arousal (0-1) to MIDI range (1-127)
        force = valence * (127 - 1) + 1  # Scale valence (0-1) to MIDI range (1-127)
        self.controller.device.set_parameter(0, 0, 1, growl)
        self.controller.device.set_parameter(0, 0, 2, force)

    def modulate_arpeggiator(self, valence: float, arousal: float) -> None:
        arp_rate = arousal * (10 - 5) + 5  # Scale arousal (0-1) to range 5-10
        self.controller.device.set_parameter(1, 0, 5, arp_rate) # parameter 5 of ableton arpeggiator controlling rate
        shape = valence # ableton params is between 0 and 1 and so is valence
        self.controller.device.set_parameter(1, 1, 4, shape) # parameter 4 of ableton wavetable controlling shapes

    def modulate_global(self, valence: float, arousal: float) -> None:
        self.controller.song.set_tempo(100 + (arousal - 0.5) * 20)  # BPM oscillates between 90 and 110 based on arousal
        # TODO map global volume

    def _start_beat_listener(self, receive_port: int = 11001):
        """Start the OSC server to listen for beats"""
        def start_server(ip="0.0.0.0", port=receive_port):
            dispatcher = Dispatcher()
            dispatcher.map("/live/song/get/beat", self._handle_beat)
            server = BlockingOSCUDPServer((ip, port), dispatcher)
            server.serve_forever()
            print(f"Listening for beats on {ip}:{port}")

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
        self.controller.song.start_listen_to_beats()

        # TODO: add a stop function to stop everything

    # def modulate_bass(self, valence: float, arousal: float) -> None:
    #     drive = compute_weighted_average(
    #         valence, arousal, weight_valence=0.3, weight_arousal=0.7
    #     )
    #     self.controller.device.set_parameter(2, 0, 5, drive)