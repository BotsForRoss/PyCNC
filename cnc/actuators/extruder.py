import time

from cnc.actuators.servo_motor import ServoMotor
from threading import Timer

class Extruder(object):
    """
    An extruder controlled by a servo motor.

    This tracks the position of the extruder to keep it from hitting limits. It is all time-based and not precise!
    """

    def __init__(self, pwm, pin, range, duty_cycle_range, max_speed, initial_pos=0.0):
        """
        Arguments:
            pwm {rpgpio.DMAPWM} -- a PWM object to add and remove pins
            pin {int} -- the GPIO pin to control the extuder's servo
            range {float} -- the range of the extruder in mm
            duty_cycle_range {(float, float)} --  the minimum and maximum duty cycle to operate the servo motor
                (from 0 to 100)
            max_speed {float} -- the max speed of the extruder in mm/s

        Keyword Arguments:
            initial_pos {float} -- how many mm are already extruded on init (default {0.0})
        """
        self._motor = ServoMotor(pwm, pin, duty_cycle_range)
        self._range = range
        self._last_stopped_pos = initial_pos
        self._timer = None
        self._speed = None  # in mm/second
        self._set_time = None
        self._max_speed = max_speed

    def _stop(self):
        """
        Stop the servo motor and update the position
        """
        self._motor.stop()
        self._last_stopped_pos = self.get_position()
        self._timer = None

    def get_position(self):
        """
        Get the current position of the extruder

        Returns:
            float -- how far from the extruder is from the fully un-extruded position, in mm
        """
        if self._timer:
            distance_moved = self._speed * (time.time() - self._set_time)
            return self._last_stopped_pos + distance_moved
        return self._last_stopped_pos

    def set_position(self, position, speed, wait=False):
        """
        Command the extruder to go to an approximate position.
        The extruder's GPIO pin must already be initialized.
        The position will be clamped into a valid range.

        Arguments:
            position {float} -- how far from the fully un-extruded position the extruder should reach, in mm

        Keyword Arguments:
            speed {float} -- The speed to travel at, in mm/s (default: {max speed})
            wait {bool} -- True iff this function should block until the motor stops (default: {False})

        Raises:
            ValueError -- if the magnitude of speed is greater than the max speed for this extruder
        """
        # Limit the position to a valid range
        if position < 0:
            position = 0
        if position > self._range:
            position = self._range

        # If the extruder is already moving, stop it
        if self._timer:
            self._timer.cancel()
            self._stop()

        if speed == 0:
            return

        # Calculate the speed and duration of movement
        delta = position - self._last_stopped_pos
        if delta < 0:
            speed = -speed
        self._speed = speed
        duration = delta / speed

        # Set the speed and set a timer for when to stop
        self._motor.set_speed(self._speed / self._max_speed)
        self._set_time = time.time()
        self._timer = Timer(duration, self._stop)
        self._timer.start()

        # Optionally wait for the motor to stop
        if wait:
            self._timer.join()

    def join(self):
        """
        Wait for the extruder to stop, if it is moving
        """
        if self._timer:
            self._timer.join()

    def get_max_speed(self):
        """
        Get the max speed of the extruder

        Returns:
            float -- the max speed in mm/s
        """

        return self._max_speed
