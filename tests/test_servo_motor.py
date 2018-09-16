import unittest

from cnc.actuators.servo_motor import ServoMotor
from unittest.mock import Mock


class TestServoMotor(unittest.TestCase):
    def test_set_duty_cycle(self):
        pwm = Mock()
        motor = ServoMotor(pwm, 10, 10, 3)
        motor._set_duty_cycle(7)
        pwm.add_pin.assert_called_once_with(10, 7)

    def test_set_speed(self):
        pwm = Mock()
        motor = ServoMotor(pwm, 10, 30, 10)
        motor._set_duty_cycle = Mock()
        motor.set(-.4)
        motor._set_duty_cycle.assert_called_once_with(26)

    def test_stop(self):
        pwm = Mock()
        motor = ServoMotor(pwm, 123, 30, 10)
        motor.stop()
        pwm.remove_pin.assert_called_once_with(123)


if __name__ == '__main__':
    unittest.main()
