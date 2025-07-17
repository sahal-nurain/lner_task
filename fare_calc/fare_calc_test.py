# test_fare_calculator.py
import unittest
from fare_calc import calculate_fare

class TestCalculateFare(unittest.TestCase):

    def test_standard_economy(self):
        self.assertAlmostEqual(calculate_fare("standard", "economy", 100), 50.0)

    def test_first_class_business(self):
        self.assertAlmostEqual(calculate_fare("first_class", "business", 200), 300.0)

    def test_invalid_ticket_type(self):
        with self.assertRaises(ValueError) as context:
            calculate_fare("vip", "economy", 100)
        self.assertIn("Invalid ticket_type", str(context.exception))

    def test_invalid_travel_class(self):
        with self.assertRaises(ValueError) as context:
            calculate_fare("standard", "luxury", 100)
        self.assertIn("Invalid travel_class", str(context.exception))

    def test_invalid_distance(self):
        with self.assertRaises(ValueError) as context:
            calculate_fare("standard", "economy", 0)
        self.assertIn("Invalid distance", str(context.exception))
    def test_fail_on_wrong_fare(self):
        # Intentionally using wrong expected value to trigger a failure
        self.assertEqual(calculate_fare("standard", "economy", 100), 42.0)

if __name__ == "__main__":
    unittest.main()
