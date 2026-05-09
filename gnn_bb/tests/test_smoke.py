import unittest


def add(a, b):
    """Simple example function used by the test cases below."""
    return a + b


class SmokeTest(unittest.TestCase):
    def test_adds_two_numbers(self):
        self.assertEqual(add(2, 3), 5)

    def test_add_supports_negative_numbers(self):
        self.assertEqual(add(-2, 3), 1)


if __name__ == "__main__":
    unittest.main()
