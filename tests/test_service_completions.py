import unittest
from pathlib import Path

from bots.bot3_distribution.handlers import handle_distribute
from signal_platform.models import SignalGrade
from signal_platform.services.signal_service import SignalService


class ServiceCompletionsTests(unittest.TestCase):
    def test_signal_service_grade_signal(self):
        self.assertEqual(SignalService.grade_signal(0.90, 75.0), SignalGrade.A_PLUS)
        self.assertEqual(SignalService.grade_signal(0.62, 20.0), SignalGrade.B)

    def test_bot3_handler_invalid_signal(self):
        self.assertEqual(handle_distribute(db=None, signal=None), "Invalid or missing signal")

    def test_schema_contains_all_platform_tables(self):
        schema = (Path(__file__).resolve().parent.parent / "database" / "schema.sql").read_text()
        self.assertIn("CREATE TABLE IF NOT EXISTS users", schema)
        self.assertIn("CREATE TABLE IF NOT EXISTS signal_records", schema)
        self.assertIn("CREATE TABLE IF NOT EXISTS signal_deliveries", schema)
        self.assertIn("CREATE TABLE IF NOT EXISTS performance_snapshots", schema)
        self.assertIn("CREATE TABLE IF NOT EXISTS audit_logs", schema)


if __name__ == "__main__":
    unittest.main()

