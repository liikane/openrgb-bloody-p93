"""Pure protocol and multi-event lighting tests. Does not access HID."""
import unittest
from daemon import process_event
from protocol import (
    COLORS, decode_lighting_report, event_areas, idle_areas, report_for_areas,
    round_robin_index, EVENT_COLORS, AREA_COUNT
)

class Rhod600ProtocolTests(unittest.TestCase):
    def test_exact_reports_from_owner_capture(self):
        captures = [
            ("07 ff 70 31 11 11 03 00", (3,1,1,1,1,1)),
            ("07 ff 70 32 11 11 03 00", (3,2,1,1,1,1)),
            ("07 ff 70 33 11 11 03 00", (3,3,1,1,1,1)),
            ("07 ff 70 73 11 11 03 00", (7,3,1,1,1,1)),
            ("07 ff 70 63 11 11 03 00", (6,3,1,1,1,1)),
            ("07 ff 70 53 11 11 03 00", (5,3,1,1,1,1)),
            ("07 ff 70 61 60 60 03 00", (6,1,6,0,6,0)),
        ]
        for dump, areas in captures:
            with self.subTest(dump=dump):
                report = bytes.fromhex(dump)
                self.assertEqual(decode_lighting_report(report), areas)
                self.assertEqual(report_for_areas(areas), report)

    def test_bounds_no_unknown_commands(self):
        for bad in ((1,2), (1,2,3,4,5,8), (-1,2,3,4,5,6),
                    (1,2,3,4,5,True), (1,2,3,4,5,5.0)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                report_for_areas(bad)
        for bad in (bytes.fromhex("07 ff 20 00 01 03 00 00"),
                    bytes.fromhex("07 ff 70 11 11 11 02 00"), b""):
            with self.assertRaises(ValueError):
                decode_lighting_report(bad)

    def test_visible_event_palettes(self):
        for name, pair in EVENT_COLORS.items():
            for phase in range(2):
                colors = event_areas(name, phase)
                self.assertEqual(len(colors), AREA_COUNT)
                self.assertTrue(all(x in pair for x in colors))
                self.assertNotIn(COLORS["OFF"], colors)
                self.assertEqual(decode_lighting_report(report_for_areas(colors)), colors)
            self.assertNotEqual(event_areas(name, 0), event_areas(name, 1))
        self.assertEqual(event_areas("ERROR", 0), (1,4,1,4,1,4))
        self.assertEqual(event_areas("SUCCESS", 1), (7,2,7,2,7,2))

    def test_pending_queue_and_ack(self):
        q = []
        q = process_event(q, "ERROR")
        q = process_event(q, "SUCCESS")
        self.assertEqual(q, ["ERROR", "SUCCESS"])
        q = process_event(q, "UNEXPECTED")
        self.assertEqual(q, ["ERROR", "SUCCESS"])
        q = process_event(q, "ACK")
        self.assertEqual(q, [])
        for i in range(20):
            q=process_event(q, "ALERT" if i%2 else "NOTICE")
        self.assertEqual(len(q),16)
        self.assertEqual(q[0],"NOTICE")
        self.assertEqual(process_event(q, "STOP"), [])

    def test_idle_always_lit(self):
        for step in range(24):
            areas=idle_areas(step)
            self.assertEqual(len(set(areas)), 6)
            self.assertNotIn(0, areas)
            self.assertEqual(idle_areas(step+6), areas)
        self.assertEqual([round_robin_index(i,2) for i in (0,3,4,7,8)], [0,0,1,1,0])

if __name__=="__main__":
    unittest.main(verbosity=2)
