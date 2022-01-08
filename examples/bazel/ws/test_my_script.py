import sys
from time import sleep
import unittest


class MyTest(unittest.TestCase):
    SLEEP_LENGTH = 1

    def test_logins_or_something(self):
        sleep(int(self.SLEEP_LENGTH))
        self.assertEqual(True, True)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        MyTest.SLEEP_LENGTH = sys.argv.pop()
    unittest.main()
