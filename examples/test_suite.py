"""
Aggregated test discovery for all AI-Native Engineering examples.
Enables `python3 -m unittest discover -s examples -p "test_*.py" -v` to run all suites seamlessly.
"""

import os
import sys
import unittest


def load_tests(loader, standard_tests, pattern):
    suite = unittest.TestSuite()
    examples_dir = os.path.dirname(os.path.abspath(__file__))

    # Discover and add test suites from each sub-example directory
    for item in sorted(os.listdir(examples_dir)):
        sub_dir = os.path.join(examples_dir, item)
        if os.path.isdir(sub_dir) and not item.startswith(".") and not item.startswith("__"):
            if sub_dir not in sys.path:
                sys.path.insert(0, sub_dir)
            discovered = loader.discover(sub_dir, pattern="test_*.py", top_level_dir=sub_dir)
            suite.addTests(discovered)

    return suite


if __name__ == "__main__":
    unittest.main()
