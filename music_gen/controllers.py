import random
from re import A
import threading
import logging
from typing import Any, List, Tuple
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
from music_gen.generator import MetaGenerator
from music_gen.ableton_api import ClipAPI, ClipSlotAPI, DeviceAPI, SongAPI, TrackApi

IP_ADDR = "192.168.0.28"
PORT = 11000
logger = logging.getLogger(__name__)

class AbletonOSCController:
    """Main controller class that coordinates all APIs"""
    def __init__(self, send_port: int = PORT, ip: str = IP_ADDR):
        logger.info("Sending to Ableton at %s:%d", ip, send_port)
        self.client = udp_client.SimpleUDPClient(ip, send_port)
        self.song = SongAPI(self.client)
        self.clip_slot = ClipSlotAPI(self.client)
        self.clip = ClipAPI(self.client)
        self.device = DeviceAPI(self.client)
        self.track = TrackApi(self.client)

    def remove_and_add_notes(
        self, track_index: int, clip_index: int, midi_notes: list, start_bar_number: int, num_bars: int = 8):
        """Remove all notes from a clip and add new notes for a specified number of bars"""
        # Each note is (midi_note, start_time (in beats), duration, velocity, mute)
        self.clip.remove_notes(track_index, clip_index, start_bar_number, num_bars)
        # logger.debug("MIDI notes: %s", midi_notes)
        self.clip.add_notes(track_index, clip_index, midi_notes)

    def set_tracks_volume(self, volume: float) -> None:
        """Sets the volume of all tracks"""
        for i in range(3):
            self.track.set_volume(i, volume)

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
        self._start_beat_listener()
        self.controller.clip_slot.create_clip(0, 0, 16) # pad 1
        self.controller.clip_slot.create_clip(1, 0, 16) # pad 2
        self.controller.clip_slot.create_clip(2, 0, 16) # bass
        logger.debug("Setting up AbletonMetaController: create empty clips and start listening to beats")
        # self.controller.clip_slot.create_clip(3, 0, 16) # lead
    
    def update_valence(self, valence: float) -> None:
        """Updates valence and modulates params based on that"""
        logger.debug("Updating valence: %f", valence)
        self.valence = valence
        self._modulate_VALE(valence)
    
    def update_arousal(self, arousal: float) -> None:
        """Updates arousal and modulates params based on that"""
        logger.debug("Updating arousal: %f", arousal)
        self.arousal = arousal
        self._modulate_arousal(arousal)

    def _handle_beat(self, *args) -> None:
        """Handle incoming beat messages, sends to ableton new midi every 8 beats"""
        beat_number = args[1]
        logger.debug("Current beat: %d", beat_number)
        if beat_number == 22: # trigger on beat 14
            # create event from beat 8 to beat 16
            logger.info("Creating chord for beat 8")
            self.add_events_to_ableton(start_bar_num=8, num_bars=4)
        if beat_number == 14: # trigger on beat 0
            # create event from beat 0 to beat 8
            logger.info("Creating chord for beat 0")
            self.add_events_to_ableton(start_bar_num=0, num_bars=4)

    def add_events_to_ableton(self, start_bar_num: int, num_bars: int = 8) -> None:
        """Generates the next chord for Ableton, removes all existing notes before adding new ones"""
        logger.debug("Adding events to Ableton - bar num %d", start_bar_num)
        midi_events = self.generator.generate_next_events(self.valence, self.arousal)
        chord1 = midi_events[0]
        chord2 = midi_events[1]
        self.controller.remove_and_add_notes(0, 0, chord1.to_ableton_osc(start_time=start_bar_num), start_bar_num, num_bars)
        self.controller.remove_and_add_notes(0, 0, chord2.to_ableton_osc(start_time=start_bar_num + 4), start_bar_num + 4, num_bars)
        self.controller.remove_and_add_notes(1, 0, chord1.to_ableton_osc(start_time=start_bar_num), start_bar_num, num_bars)
        self.controller.remove_and_add_notes(1, 0, chord2.to_ableton_osc(start_time=start_bar_num + 4), start_bar_num + 4, num_bars)
        # bass, only the root note
        self.controller.remove_and_add_notes(2, 0, [int(chord1.root - 12), start_bar_num, 8, chord1.velocity, 0], start_bar_num, num_bars)

    def _modulate_arousal(self, arousal: float) -> None:
        bass_pulse = arousal * (0.7 - 0.5) + 0.5
        self.controller.device.set_parameter(2, 1, 14, bass_pulse)  # parameter 14 of ableton bass controlling lfo of autofilter
        self.controller.song.set_tempo(85 + arousal * 30)  # oscillates between 80 and 115
        self.controller.set_tracks_volume(0.6 + arousal * 0.25) 

    def _modulate_valence(self, valence: float) -> None:
        # TODO: maybe modulate saturator?
        pass

    def stop(self):
        """Stops the beat listener server thread"""
        if self.server_thread:
            self.server_thread.join(timeout=5)

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
