import time

from cnc.actuators.servo_motor import ServoMotor
from cnc.config import MAX_VELOCITY_MM_PER_MIN_E
from threading import Timer


class Extruder(object):
    """
    An extruder controlled by a servo motor.

    This tracks the position of the extruder to keep it from hitting limits. It is all time-based and not precise!
    """
    def __init__(self, pwm, pin, range, initial_pos=0.0):
        """
        Arguments:
            pwm {DMAPWM} -- a DMAPWM object
            pin {int} -- the GPIO pin to control the extuder's servo
            range {float} -- the range of the extruder in mm

        Keyword Arguments:
            initial_pos {float} -- how many mm are already extruded on init (default {0.0})
        """
        self._motor = ServoMotor(pwm, pin)
        self._range = range
        self._last_stopped_pos = initial_pos
        self._timer = None
        self._speed = None  # in mm/second
        self._set_time = None

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

    def set_position(self, position, speed=MAX_VELOCITY_MM_PER_MIN_E / 60.0, wait=False):
        """
        Command the extruder to go to an approximate position.
        The extruder's GPIO pin must already be initialized.

        Arguments:
            position {float} -- how far from the fully un-extruded position the extruder should reach, in mm

        Keyword Arguments:
            speed {float} -- The speed to travel at, in mm/s (default: {max speed})
            wait {bool} -- True iff this function should block until the motor stops (default: {False})
        """
        # Limit the position to a valid range
        if position < 0:
            position = 0
        elif position > self._range:
            position = self._range

        # If the extruder is already moving, stop it
        if self._timer:
            self._timer.cancel()
            self._stop()

        if speed == 0:
            return

        # Calculate the speed and duration of movement
        delta = self._last_stopped_pos - position
        if delta < 0:
            speed = -speed
        self._speed = speed
        duration = delta / speed

        # Set the speed and set a timer for when to stop
        self._motor.set_speed(self._speed / (MAX_VELOCITY_MM_PER_MIN_E * 60.0))
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
