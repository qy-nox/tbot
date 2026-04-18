import unittest
from unittest.mock import patch

import requests


class RuntimeRecoveryToolsTests(unittest.TestCase):
    def test_fix_port_skips_non_tbot_pid_without_force(self):
        from scripts import fix_port

        with patch("scripts.fix_port._is_port_available", return_value=False):
            with patch("scripts.fix_port._port_owner_pids", return_value=[9999]):
                with patch("scripts.fix_port._belongs_to_tbot", return_value=False):
                    with patch("scripts.fix_port.os.kill") as kill_mock:
                        released = fix_port.release_port("0.0.0.0", 8000, wait_seconds=0.1, force=False)
        self.assertFalse(released)
        kill_mock.assert_not_called()

    def test_notifier_uses_configured_timeout_and_exponential_backoff(self):
        from notifications.telegram_notifier import TelegramNotifier

        with patch.multiple(
            "notifications.telegram_notifier.Settings",
            TELEGRAM_CHAT_ID="12345",
            TELEGRAM_BROADCAST_CHANNELS=[],
            TELEGRAM_RETRY_ATTEMPTS=3,
            TELEGRAM_RETRY_BACKOFF_SECONDS=0.2,
            TELEGRAM_RETRY_MAX_BACKOFF_SECONDS=0.5,
            TELEGRAM_CONNECT_TIMEOUT_SECONDS=1.0,
            TELEGRAM_READ_TIMEOUT_SECONDS=2.0,
        ):
            notifier = TelegramNotifier(token="12345:abcdefgh", chat_id="12345")
            self.assertEqual(notifier.request_timeout, (1.0, 2.0))
            with patch(
                "notifications.telegram_notifier.requests.post",
                side_effect=requests.ConnectTimeout("Timed out"),
            ) as post_mock:
                with patch("notifications.telegram_notifier.time.sleep") as sleep_mock:
                    self.assertFalse(notifier.send_message("hello"))

        self.assertEqual(post_mock.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep_mock.call_args_list], [0.2, 0.4])

    def test_diagnose_group_check_flags_placeholder_ids(self):
        from scripts import diagnose

        messages = diagnose._check_groups("12345:abcdefgh", ["-1001234567890"])
        self.assertEqual(messages, ["GROUP_PLACEHOLDER: -1001234567890"])


if __name__ == "__main__":
    unittest.main()
