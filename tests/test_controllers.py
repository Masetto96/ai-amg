import pytest
from unittest.mock import Mock, call
from pythonosc import udp_client
from music_gen.controllers import (
    OSCBase, ClipAPI, ClipSlotAPI, SongAPI, DeviceAPI,
    TrackApi, AbletonOSCController, AbletonMetaController
)

@pytest.fixture
def mock_client():
    return Mock(spec=udp_client.SimpleUDPClient)

@pytest.fixture
def osc_base(mock_client):
    return OSCBase(mock_client)

@pytest.fixture
def clip_api(mock_client):
    return ClipAPI(mock_client)

@pytest.fixture
def clip_slot_api(mock_client):
    return ClipSlotAPI(mock_client)

@pytest.fixture
def song_api(mock_client):
    return SongAPI(mock_client)

@pytest.fixture
def device_api(mock_client):
    return DeviceAPI(mock_client)

@pytest.fixture
def track_api(mock_client):
    return TrackApi(mock_client)

@pytest.fixture
def ableton_controller(mock_client):
    controller = AbletonOSCController(send_port=11000, ip="127.0.0.1")
    controller.client = mock_client
    controller.clip = ClipAPI(mock_client)
    controller.track = TrackApi(mock_client)
    return controller

@pytest.fixture
def meta_controller(mock_client):
    controller = AbletonMetaController()
    controller.controller = AbletonOSCController(send_port=11000, ip="127.0.0.1")
    controller.controller.client = mock_client
    controller.controller.clip_slot = ClipSlotAPI(mock_client)
    controller.controller.clip = ClipAPI(mock_client)
    controller.controller.track = TrackApi(mock_client)
    controller.controller.song = SongAPI(mock_client)
    controller.generator = Mock()
    controller.generator.generate_next_event.return_value = (Mock(), Mock())
    return controller

def test_osc_base_send_message(osc_base, mock_client):
    osc_base.send_message("/test/address", [1, 2, 3])
    mock_client.send_message.assert_called_once_with("/test/address", [1, 2, 3])

def test_clip_api_fire_clip(clip_api, mock_client):
    clip_api.fire_clip(1, 2)
    mock_client.send_message.assert_called_once_with("/live/clip/fire", [1, 2])

def test_clip_api_stop_clip(clip_api, mock_client):
    clip_api.stop_clip(1, 2)
    mock_client.send_message.assert_called_once_with("/live/clip/stop", [1, 2])

def test_clip_api_remove_notes(clip_api, mock_client):
    clip_api.remove_notes(1, 2, 4)
    mock_client.send_message.assert_called_once_with("/live/clip/remove/notes", [1, 2, 0, 127, 4, 8])

def test_clip_api_add_notes(clip_api, mock_client):
    notes = [(60, 0.0, 1.0, 100, 0)]
    clip_api.add_notes(1, 2, notes)
    mock_client.send_message.assert_called_once_with("/live/clip/add/notes", [1, 2] + notes)

def test_clip_slot_api_create_clip(clip_slot_api, mock_client):
    clip_slot_api.create_clip(1, 2, 4)
    mock_client.send_message.assert_called_once_with("/live/clip_slot/create_clip", [1, 2, 4])

def test_clip_slot_api_delete_clip(clip_slot_api, mock_client):
    clip_slot_api.delete_clip(1, 2)
    mock_client.send_message.assert_called_once_with("/live/clip_slot/delete_clip", [1, 2])

def test_clip_slot_api_duplicate_clip(clip_slot_api, mock_client):
    clip_slot_api.duplicate_clip(1, 2, 3, 4)
    mock_client.send_message.assert_called_once_with("/live/clip_slot/duplicate_clip", [1, 2, 3, 4])

def test_song_api_start_playback(song_api, mock_client):
    song_api.start_playback()
    expected_calls = [
        call("/live/clip/fire", [0, 0]),
        call("/live/clip/fire", [1, 0])
    ]
    assert mock_client.send_message.call_args_list == expected_calls

def test_song_api_start_listen_to_beats(song_api, mock_client):
    song_api.start_listen_to_beats()
    mock_client.send_message.assert_called_once_with("/live/song/start_listen/beat", [])

def test_song_api_set_tempo(song_api, mock_client):
    song_api.set_tempo(120.5)
    mock_client.send_message.assert_called_once_with("/live/song/set/tempo", 120.5)

def test_device_api_set_parameter(device_api, mock_client):
    device_api.set_parameter(1, 2, 3, 0.5)
    mock_client.send_message.assert_called_once_with("/live/device/set/parameter/value", [1, 2, 3, 0.5])

def test_track_api_set_volume(track_api, mock_client):
    track_api.set_volume(1, 0.8)
    mock_client.send_message.assert_called_once_with("/live/track/set/volume", [1, 0.8])

def test_track_api_set_send(track_api, mock_client):
    track_api.set_send(1, 2, 0.7)
    mock_client.send_message.assert_called_once_with("/live/track/set/send", [1, 2, 0.7])

def test_ableton_controller_remove_and_add_notes(ableton_controller, mock_client):
    notes = [(60, 0.0, 1.0, 100, 0)]
    ableton_controller.remove_and_add_notes(1, 2, notes, 4)
    mock_client.send_message.assert_any_call("/live/clip/remove/notes", [1, 2, 0, 127, 4, 8])
    mock_client.send_message.assert_any_call("/live/clip/add/notes", [1, 2] + notes)

def test_ableton_controller_set_saturator_send(ableton_controller, mock_client):
    ableton_controller.set_saturator_send(0.5)
    expected_calls = [
        call("/live/track/set/send", [0, 2, 0.5]),
        call("/live/track/set/send", [1, 2, 0.5]),
        call("/live/track/set/send", [3, 2, 0.5])
    ]
    assert mock_client.send_message.call_args_list == expected_calls

def test_ableton_controller_set_tracks_volume(ableton_controller, mock_client, monkeypatch):
    monkeypatch.setattr('random.uniform', lambda *args: 0.05)
    ableton_controller.set_tracks_volume(0.7)
    expected_calls = [
        call("/live/track/set/volume", [0, 0.7]),
        call("/live/track/set/volume", [1, 0.7]),
        call("/live/track/set/volume", [2, 0.75]),
        call("/live/track/set/volume", [3, 0.75])
    ]
    assert mock_client.send_message.call_args_list == expected_calls

def test_meta_controller_setup(meta_controller):
    meta_controller.controller.clip_slot.create_clip = Mock()
    meta_controller.controller.song.start_listen_to_beats = Mock()
    meta_controller.setup()
    meta_controller.controller.clip_slot.create_clip.assert_has_calls([
        call(0, 0, 16),
        call(1, 0, 16),
        call(2, 0, 16),
        call(3, 0, 16)
    ])
    meta_controller.controller.song.start_listen_to_beats.assert_called_once()

def test_meta_controller_update_metrics(meta_controller):
    meta_controller.update_metrics(0.6, 0.7)
    assert meta_controller.valence == 0.6
    assert meta_controller.arousal == 0.7

def test_meta_controller_add_events_to_ableton(meta_controller):
    chord_event_mock = Mock()
    chord_event_mock.to_ableton_osc.return_value = [(60, 0.0, 1.0, 100, 0)]
    chord_event_mock.root = 72
    chord_event_mock.duration = 8
    chord_event_mock.velocity = 100
    arp_event_mock = Mock()
    arp_event_mock.to_ableton_osc.return_value = [(61, 0.0, 1.0, 100, 0)]
    meta_controller.generator.generate_next_event.return_value = (chord_event_mock, arp_event_mock)
    meta_controller.controller.remove_and_add_notes = Mock()
    meta_controller.add_events_to_ableton(0)
    meta_controller.controller.remove_and_add_notes.assert_any_call(0, 0, [(60, 0.0, 1.0, 100, 0)], 0)
    meta_controller.controller.remove_and_add_notes.assert_any_call(1, 0, [(61, 0.0, 1.0, 100, 0)], 0)
    meta_controller.controller.remove_and_add_notes.assert_any_call(2, 0, [60, 0, 8, 100, 0], 0)
    meta_controller.controller.remove_and_add_notes.assert_any_call(3, 0, [(60, 0.0, 1.0, 100, 0)], 0)

def test_meta_controller_stop(meta_controller):
    meta_controller.server_thread = Mock()
    meta_controller.stop()
    meta_controller.server_thread.join.assert_called_once_with(timeout=5)
