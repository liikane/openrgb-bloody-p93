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
        self.assertEqual(m.VALID_EVENTS, {"ALERT", "ERROR", "NOTICE", "SUCCESS", "STOP", "ACK"})

    def test_one_event_fans_out_to_p93_and_optional_keyboard(self):
        from unittest.mock import patch
        destinations = []
        class DummySocket:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def sendto(self, content, dest):
                destinations.append((content, dest))
        with patch.object(m.socket, "socket", return_value=DummySocket()):
            m.send_local("ALERT")
        self.assertEqual(destinations, [
            (b"P93:ALERT", ("127.0.0.1", 45893)),
            (b"RHOD600:ALERT", ("127.0.0.1", 45894)),
        ])
        with patch.object(m.socket, "socket", return_value=DummySocket()):
            m.send_local("ACK")
        self.assertEqual(destinations[-2:], [
            (b"P93:ACK", ("127.0.0.1", 45893)),
            (b"RHOD600:ACK", ("127.0.0.1", 45894)),
        ])

    def test_expected_windows_events_only(self):
        self.assertEqual({(channel, eid) for channel, eid, _ in m.SYSTEM_EVENTS},
                         {("Microsoft-Windows-Windows Defender/Operational", 1116),
                          ("Microsoft-Windows-Windows Defender/Operational", 1117),
                          ("Microsoft-Windows-WindowsUpdateClient/Operational", 19),
                          ("Microsoft-Windows-WindowsUpdateClient/Operational", 20)})


if __name__ == "__main__":
    unittest.main(verbosity=2)
