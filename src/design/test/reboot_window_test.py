# encoding= utf-8
# __author__= gary
import unittest
import reboot_test_window


class RebootWindowTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_check(self):
        self.assertTrue(reboot_test_window.check_device_in_adb('192.192.255.38:5555'))


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(RebootWindowTest("check_adb_test"))
