"""
https://github.com/ideoforms/AbletonOSC
"""

import threading
import time
import logging
from typing import Any, List, Tuple
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from music_gen.generator import MetaGenerator

logger = logging.getLogger(__name__)

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
        """ [track_id, clip_id] + [start_pitch, pitch_span, start_time, time_span] """
        self.send_message("/live/clip/remove/notes", [track_id, clip_id] + [0, 127, bar_number, 8])

    def add_notes(
        self,
        track_id: int,
        clip_id: int,
        notes: List[Tuple[int, float, float, int, int]], 
        # note_format = (midi_note, start_time, duration, velocity, mute)
    ) -> None:
        """
        Add MIDI notes to clip
        Args:
            track_id: Track index
            clip_id: Clip index
            notes: ChordEvent.to_ableton_osc() format
        """
        self.send_message("/live/clip/add/notes", [track_id, clip_id] + notes)

class ClipSlotAPI(OSCBase):
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
    def start_playback(self) -> None:
        self.send_message("/live/clip/fire", [0, 0])  # track 0, slot 0
        self.send_message("/live/clip/fire", [1, 0])  # track 1, slot 0

    def start_listen_to_beats(self) -> None:
        self.send_message("/live/song/start_listen/beat", [])

    def set_tempo(self, bpm: float) -> None:
        self.send_message("/live/song/set/tempo", bpm)


class DeviceAPI(OSCBase):
    def set_parameter(
        self, track_index: int, device_index: int, parameter_index: int, value: float
    ) -> None:
        self.send_message(
            "/live/device/set/parameter/value",
            [track_index, device_index, parameter_index, value],
        )

class TrackApi(OSCBase):
    def set_volume(self, track_index: int, volume: float) -> None:
        self.send_message("/live/track/set/volume", [track_index, volume])
    def set_send(self, track_index: int, send_index: int, value: float) -> None:
        self.send_message("/live/track/set/send", [track_index, send_index, value])

class AbletonOSCController:
    """Main controller class that coordinates all APIs"""
    def __init__(self, send_port: int = 11000, ip: str = "192.168.0.25"):
        logger.info("Sending to Ableton at %s:%d", ip, send_port)
        self.client = udp_client.SimpleUDPClient(ip, send_port)
        self.song = SongAPI(self.client)
        self.clip_slot = ClipSlotAPI(self.client)
        self.clip = ClipAPI(self.client)
        self.device = DeviceAPI(self.client)
        self.track = TrackApi(self.client)

    def remove_and_add_notes(
        self, track_index: int, clip_index: int, midi_notes: list, bar_number:int):
        """Remove all notes from a clip and add new notes"""
        # Each note is (midi_note, start_time (in beats), duration, velocity, mute)
        self.clip.remove_notes(track_index, clip_index, bar_number)
        self.clip.add_notes(track_index, clip_index, midi_notes)

    def set_saturator_send(self, value) -> None:
        """Sets send amount of saturator of all tracks"""
        self.track.set_send(0, 2, value) 
        self.track.set_send(1, 2, value) 
        self.track.set_send(2, 2, value) 

    def set_tracks_volume(self, volume: float) -> None:
        """Set volume of all tracks, oscillates between 0.5 and .9"""
        self.track.set_volume(0, volume)
        self.track.set_volume(1, volume)
        self.track.set_volume(2, volume)


class AbletonMetaController:
    """
    Piano is on track 1 (mids), zero index; Arpeggiator is on track 2 (high); Bass is on track 3 (bass)
    """
    def __init__(self):
        self.controller = AbletonOSCController()
        self.generator = MetaGenerator()
        self.valence = 0.5
        self.arousal = 0.5
        self.server_thread = None

    def setup(self):
        """Starts the beat listener and creates midi clips of length 16 bars in the first 3 tracks"""
        logger.info("Setting up AbletonMetaController")
        self._start_beat_listener()
        self.controller.clip_slot.create_clip(0, 0, 16) # piano
        self.controller.clip_slot.create_clip(1, 0, 16) # arpeggiator
        self.controller.clip_slot.create_clip(2, 0, 16) # bass

    def update_metrics(self, valence, arousal):
        """Updates valence and arousal and modulates params based on those"""
        logger.debug("Updating metrics: valence=%f, arousal=%f", valence, arousal)
        self.valence = valence
        self.arousal = arousal
        # self.modulate_piano(self.valence, self.arousal)
        self._modulate_arpeggiator(self.valence, self.arousal)
        self._modulate_bass(self.valence, self.arousal)
        self._modulate_global(self.valence, self.arousal)

    def _handle_beat(self, *args) -> None:
        """Handle incoming beat messages, sends to ableton new midi every 8 beats"""
        beat_number = args[1]
        logger.debug("Current beat: %d", beat_number)
        if beat_number == 22: # when beat is 7 a chord is created for beat 8 onwards
            logger.info("Creating chord for beat 8")
            self.add_events_to_ableton(start_bar_num=8)
        if beat_number == 14: # when beat is 15 a chord is created for beat 0 onwards
            logger.info("Creating chord for beat 0")
            self.add_events_to_ableton(start_bar_num=0)

    def add_events_to_ableton(self, start_bar_num:int) -> None:
        """Generates the next chord for Ableton, removes all existing notes before adding new ones"""
        logger.info("Adding events to Ableton starting at bar %d", start_bar_num)
        chord_event, arp_event = self.generator.generate_next_event(self.valence, self.arousal)
        # piano
        self.controller.remove_and_add_notes(0, 0, chord_event.to_ableton_osc(start_time=start_bar_num), start_bar_num)
        # bass, only the root note
        self.controller.remove_and_add_notes(2, 0, [int(chord_event.root-12), start_bar_num, chord_event.duration, chord_event.velocity, 0], start_bar_num)
         # arpeggiator
        self.controller.remove_and_add_notes(1, 0, arp_event.to_ableton_osc(start_time=start_bar_num), start_bar_num)

    # def _modulate_piano(self, valence: float, arousal: float) -> None:
    #     growl = arousal * (127 - 1) + 1  # Scale arousal (0-1) to MIDI range (1-127)
    #     force = valence * (127 - 1) + 1  # Scale valence (0-1) to MIDI range (1-127)
    #     self.controller.device.set_parameter(0, 0, 1, growl)
    #     self.controller.device.set_parameter(0, 0, 2, force)

    def _modulate_bass(self, valence: float, arousal: float) -> None:
        bass_pulse = arousal * (0.8 - 0.6) + 0.6  # Scale arousal (0-1) to range 0.6-0.8
        self.controller.device.set_parameter(2, 1, 14, bass_pulse)  # parameter 14 of ableton bass controlling lfo of autofilter

    def _modulate_arpeggiator(self, valence: float, arousal: float) -> None:
        shape = valence # ableton params is between 0 and 1 and so is valence
        self.controller.device.set_parameter(1, 1, 4, shape) # parameter 4 of ableton wavetable controlling shapes

    def _modulate_global(self, valence: float, arousal: float) -> None:
        self.controller.song.set_tempo(50 + arousal * 90)  # oscillates between 50 and 130
        self.controller.set_tracks_volume(0.5 + valence * 0.4)  # oscillates between 0.5 and .9
        self.controller.set_saturator_send(1-valence) # inverse valence

    def _start_beat_listener(self, receive_port: int = 11001):
        def start_server(ip="0.0.0.0", port=receive_port):
            dispatcher = Dispatcher()
            dispatcher.map("/live/song/get/beat", self._handle_beat)
            server = BlockingOSCUDPServer((ip, port), dispatcher)
            logger.info("Listening for beats on %s:%d", ip, port)
            server.serve_forever()

        # Start server in background thread
        self.server_thread = threading.Thread(target=start_server)
        self.server_thread.daemon = True
        self.server_thread.start()

        # Sends OSC messages to start listening for beats
        self.controller.song.start_listen_to_beats()

        # TODO: add a stop function to stop everything
        