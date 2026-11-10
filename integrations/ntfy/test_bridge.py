"""Unit tests for ntfy classification, deduplication and Windows-event policy."""
import importlib.util
import logging
import pathlib
import queue
import threading
import time
import unittest

file = pathlib.Path(__file__).with_name("bridge.py")
spec = importlib.util.spec_from_file_location("true_mouse_art_bridge", file)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class NtfyBridgeTests(unittest.TestCase):
    def test_ntfy_classifier(self):
        examples = [
            ({"event": "keepalive"}, None),
            ({"event": "message", "priority": 1}, None),
            ({"event": "message", "priority": 3}, "NOTICE"),
            ({"event": "message", "priority": 5}, "ALERT"),
            ({"event": "message", "tags": ["warning"]}, "ALERT"),
            ({"event": "message", "tags": ["success"]}, "SUCCESS"),
            ({"event": "message", "tags": ["error"]}, "ERROR"),
            ({"event": "message", "title": "Töö valmis"}, "SUCCESS"),
            ({"event": "message", "title": "Error: build failed"}, "ERROR"),
            ({"event": "message", "title": "Report", "message": "private error data"}, "NOTICE"),
        ]
        for item, expected in examples:
            with self.subTest(item=item):
                self.assertEqual(m.classify_ntfy(item), expected)

    def test_stream_and_poll_deduplicate(self):
        events = queue.Queue()
        src = m.NtfySource({"server": "https://example.invalid", "topic": "testtopicaaaa", "token": ""},
                           events, threading.Event(), logging.getLogger("test"))
        t = int(time.time())
        msg = {"event": "message", "id": "msg123", "time": t, "tags": ["warning"]}
        src.handle_message(msg, "ntfy-stream")
        src.handle_message(msg, "ntfy-poll")
        self.assertEqual(events.qsize(), 1)
        self.assertEqual(events.get_nowait(), ("ALERT", "ntfy-stream"))
        self.assertEqual(src.since, str(t))
        src.handle_message({"event": "message", "id": "old", "time": t-360, "priority": 5}, "ntfy-poll")
        self.assertTrue(events.empty(), "Old cached messages should not trigger lights")

    def test_no_unexpected_event_output(self):
        self.assertEqual(m.VALID_EVENTS, {"ALERT", "ERROR", "NOTICE", "SUCCESS", "STOP"})

    def test_expected_windows_events_only(self):
        self.assertEqual({(channel, eid) for channel, eid, _ in m.SYSTEM_EVENTS},
                         {("Microsoft-Windows-Windows Defender/Operational", 1116),
                          ("Microsoft-Windows-Windows Defender/Operational", 1117),
                          ("Microsoft-Windows-WindowsUpdateClient/Operational", 19),
                          ("Microsoft-Windows-WindowsUpdateClient/Operational", 20)})


if __name__ == "__main__":
    unittest.main(verbosity=2)
