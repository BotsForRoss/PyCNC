import unittest

from cnc.actuators import ServoMotor, Gimbal, GimbalMotor
from unittest.mock import Mock, patch, call
from threading import Timer


class TestGimbalMotor(unittest.TestCase):
    def setUp(self):
        self.servo = Mock(spec=ServoMotor)
        self.gimbal_motor = GimbalMotor(self.servo, range=180.0)

    @patch.object(Timer, 'join')
    def test_set_angle(self, mock_join):
        # test a simple set_angle
        self.gimbal_motor.set_angle(45.0)
        self.servo.set.assert_called_once_with(.5)
        self.servo.set.reset_mock()

        # test that set_angle waits for the previous call to finish
        self.gimbal_motor.set_angle(-45.0)
        self.servo.set.assert_called_once_with(-.5)
        mock_join.assert_called_once_with()
        self.servo.set.reset_mock()
        mock_join.reset_mock()

        # test an interrupt
        self.gimbal_motor.set_angle(0, interrupt=True)
        self.servo.set.assert_called_once_with(0)
        mock_join.assert_not_called()
        self.servo.set.reset_mock()
        mock_join.reset_mock()

        # test wait
        self.gimbal_motor.set_angle(90.0, wait=True, interrupt=True)
        self.servo.set.assert_called_once_with(1.0)
        mock_join.assert_called_once_with()

        # test out of range
        with self.assertRaises(ValueError):
            self.gimbal_motor.set_angle(90.1)

    @patch.object(GimbalMotor, 'join')
    def test_get_angle(self, mock_join):
        self.gimbal_motor.set_angle(45.0)
        angle = self.gimbal_motor.get_angle()
        mock_join.assert_called_once_with()
        self.assertEqual(angle, 45.0)

    @patch.object(Timer, 'join')
    def test_join(self, mock_join):
        self.gimbal_motor.join()
        mock_join.assert_not_called()
        self.gimbal_motor.set_angle(45.0)
        self.gimbal_motor.join()
        mock_join.assert_called_once_with()

    def test_release(self):
        self.gimbal_motor.release()
        self.servo.stop.assert_called_once_with()


class TestGimbal(unittest.TestCase):
    def setUp(self):
        self.motor_a = Mock(spec=GimbalMotor)
        self.motor_b = Mock(spec=GimbalMotor)
        self.gimbal = Gimbal(self.motor_a, self.motor_b)

    @patch.object(Gimbal, 'join')
    def test_set_position(self, mock_join):
        self.gimbal.set_position(1, 2)
        self.motor_a.set_angle.assert_called_once_with(1)
        self.motor_b.set_angle.assert_called_once_with(2)
        mock_join.assert_called_once_with()

    @patch.object(Gimbal, 'join')
    def test_set_position_wait(self, mock_join):
        self.gimbal.set_position(3, 4, wait=True)
        self.motor_a.set_angle.assert_called_once_with(3)
        self.motor_b.set_angle.assert_called_once_with(4)
        mock_join.assert_has_calls([call(), call()])

    @patch.object(Gimbal, 'join')
    def test_set_position_interrupt(self, mock_join):
        self.gimbal.set_position(5, 6, interrupt=True)
        self.motor_a.set_angle.assert_called_once_with(5)
        self.motor_b.set_angle.assert_called_once_with(6)
        mock_join.assert_not_called()

    def test_set_position_wrong_num(self):
        with self.assertRaises(ValueError):
            self.gimbal.set_position(1, 2, 3)
        with self.assertRaises(ValueError):
            self.gimbal.set_position(1)

    def test_get_position(self):
        self.motor_a.get_angle.return_value = 123
        self.motor_b.get_angle.return_value = 456
        alpha, beta = self.gimbal.get_position()
        self.assertEqual(alpha, 123)
        self.assertEqual(beta, 456)

    def test_release(self):
        self.gimbal.release()
        self.motor_a.release.assert_called_once_with()
        self.motor_b.release.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
