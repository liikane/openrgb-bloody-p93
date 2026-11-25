"""Synthetic, offline tests for the Windows notification policy."""
import unittest
from unittest.mock import patch

import core


class NotificationPolicyTests(unittest.TestCase):
    def test_requires_startup_baseline_and_does_not_replay(self):
        policy = core.NotificationPolicy()
        policy.set_rules({"app": core.EventKind.ALERT})
        old = core.ToastId("app", 1)
        with self.assertRaises(RuntimeError):
            policy.process_snapshot([old])
        policy.initialize([old])
        self.assertEqual(policy.process_snapshot([old]), [])
        self.assertEqual(policy.process_snapshot([]), [])
        self.assertEqual(policy.process_snapshot([old]), [])
        with self.assertRaises(RuntimeError):
            policy.initialize([])

    def test_allowlist_is_empty_and_never_replays_previous_toasts(self):
        policy = core.NotificationPolicy()
        policy.initialize([])
        old = core.ToastId("app", 1)
        self.assertEqual(policy.process_snapshot([old]), [])
        rules = {"app": core.EventKind.ERROR}
        policy.set_rules(rules)
        rules["app"] = core.EventKind.ALERT
        self.assertEqual(policy.process_snapshot([old]), [])
        self.assertEqual(policy.process_snapshot([old, core.ToastId("app", 2)]),
                         [core.NotificationEvent(core.EventKind.ERROR)])
        policy.set_rules({})
        self.assertEqual(policy.process_snapshot([core.ToastId("app", 3)]), [])

    def test_deduplicates_by_app_and_id_and_uses_configured_kind(self):
        policy = core.NotificationPolicy()
        policy.set_rules({"a": core.EventKind.SUCCESS, "b": core.EventKind.NOTICE})
        policy.initialize([])
        a, b = core.ToastId("a", 9), core.ToastId("b", 9)
        events = [core.NotificationEvent(core.EventKind.SUCCESS),
                  core.NotificationEvent(core.EventKind.NOTICE)]
        self.assertEqual(policy.process_snapshot([a, b, a]), events)
        self.assertEqual(policy.process_snapshot([a, b]), [])

    def test_schema_rejects_private_content_and_invalid_values(self):
        with self.assertRaises(TypeError):
            core.NotificationEvent(core.EventKind.NOTICE, title="private")
        with self.assertRaises(TypeError):
            core.ToastId("app", 1, body="private")
        for app, identifier in [("", 1), ("app", -1), ("app", 2**32), ("app", True)]:
            with self.subTest(app=app, identifier=identifier), self.assertRaises(ValueError):
                core.ToastId(app, identifier)
        with self.assertRaises(ValueError):
            core.NotificationEvent("NOTICE")
        policy = core.NotificationPolicy()
        with self.assertRaises(ValueError):
            policy.set_rules({"app": "ERROR"})
        with self.assertRaises(ValueError):
            policy.initialize([{"app_id": "app", "notification_id": 1, "body": "private"}])

    def test_limit_fails_closed_without_partial_state(self):
        policy = core.NotificationPolicy()
        policy.MAX_SEEN = 2
        policy.set_rules({"app": core.EventKind.ALERT})
        one, two, three = (core.ToastId("app", i) for i in range(3))
        policy.initialize([one])
        with self.assertRaises(RuntimeError):
            policy.process_snapshot([two, three])
        self.assertEqual(policy.process_snapshot([two]), [core.NotificationEvent(core.EventKind.ALERT)])


class P93SenderTests(unittest.TestCase):
    @patch.object(core.socket, "socket")
    def test_opt_in_and_exact_loopback_payloads(self, socket):
        sender = core.P93Sender()
        event = core.NotificationEvent(core.EventKind.ALERT)
        self.assertFalse(sender.send(event))
        socket.assert_not_called()
        sender.set_enabled(True)
        for kind in core.EventKind:
            self.assertTrue(sender.send(core.NotificationEvent(kind)))
            socket.return_value.__enter__.return_value.sendto.assert_called_with(
                ("P93:" + kind.value).encode("ascii"), ("127.0.0.1", 45893))
        sender.set_enabled(False)
        self.assertFalse(sender.send(event))
        self.assertEqual(socket.call_count, len(core.EventKind))
        with self.assertRaises(ValueError):
            sender.set_enabled("true")
        with self.assertRaises(ValueError):
            sender.send({"kind": "ALERT", "body": "private"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
