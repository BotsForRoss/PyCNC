import unittest

from cnc.actuators.extruder import Extruder
from cnc.actuators.servo_motor import ServoMotor
from unittest.mock import patch, Mock


EXTRUDER_ERROR_TOLERANCE = 2  # mm


class TestExtruder(unittest.TestCase):
    @patch('cnc.actuators.extruder.ServoMotor')
    def setUp(self, mock_motor_init):
        self.motor = Mock(spec=ServoMotor)
        mock_motor_init.return_value = self.motor

        self.extruder = Extruder(None, 123, 50, (20, 40), 100)

    def test_set_position(self):
        self.extruder.set_position(10, 100, wait=True)
        pos = self.extruder.get_position()
        self.assertLess(abs(pos - 10), EXTRUDER_ERROR_TOLERANCE)
        self.motor.set_speed.assert_called_once_with(1)
        self.motor.stop.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()