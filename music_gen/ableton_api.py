"""
https://github.com/ideoforms/AbletonOSC
"""

import time
from typing import Any, List, Tuple
from pythonosc import udp_client


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

    def remove_notes(self, track_id: int, clip_id: int, start_bar_number: int, time_span: int) -> None:
        """[track_id, clip_id] + [start_pitch, pitch_span, start_time, time_span]"""
        self.send_message(
            "/live/clip/remove/notes", [track_id, clip_id] + [0, 127, start_bar_number, time_span]
        )

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
    def create_clip(self, track_index: int, clip_index: int, length_in_bars: int) -> None:
        self.send_message("/live/clip_slot/create_clip", [track_index, clip_index, length_in_bars])

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
    def set_parameter(self, track_index: int, device_index: int, parameter_index: int, value: float) -> None:
        self.send_message(
            "/live/device/set/parameter/value",
            [track_index, device_index, parameter_index, value],
        )


class TrackApi(OSCBase):
    def set_volume(self, track_index: int, volume: float) -> None:
        self.send_message("/live/track/set/volume", [track_index, volume])

    def set_send(self, track_index: int, send_index: int, value: float) -> None:
        self.send_message("/live/track/set/send", [track_index, send_index, value])
