import time
import RPi.GPIO as GPIO

from cnc.config import MAX_VELOCITY_MM_PER_MIN_E
from threading import Thread


# These values are based off of this guide:
# https://learn.sparkfun.com/tutorials/pi-servo-hat-hookup-guide#software---python
_DUTY_CYCLE_STOP = .305  # the duty cycle needed to hold the motor still
_DUTY_CYCLE_RANGE = .101  # what to add/subtract from _DUTY_CYCLE_STOP to get full forward/reverse
_PERIOD = 1/50.0  # seconds


class Extruder(object):
    """
    An extruder controlled by a servo motor.

    This tracks the position of the extruder to keep it from hitting limits. It is all time-based and not precise!
    """

    def __init__(self, pin, range, initial_pos=0.0):
        """
        Arguments:
            pin {int} -- the GPIO pin to control the extuder's servo
            range {float} -- the range of the extruder in mm

        Keyword Arguments:
            initial_pos {float} -- how many mm are already extruded on init (default {0.0})
        """
        self._pin = pin
        self._range = range
        self._last_stopped_pos = initial_pos
        self._thread = None
        self._speed = None  # in mm/second
        self._set_time = None
        self._cancel = False

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)

    def _stop(self):
        """
        Stop the servo motor and update the position
        """
        if self._thread:
            self._cancel = True
            self._thread.join()
            self._cancel = False
            self._thread = None

    def _run(self, speed, duration):
        max_speed = MAX_VELOCITY_MM_PER_MIN_E / 60.0
        if abs(speed) > max_speed:
            raise ValueError('extruder too fast ({} mm/s)'.format(speed))

        duty_cycle = _DUTY_CYCLE_STOP + _DUTY_CYCLE_RANGE * (speed / max_speed)

        on_time = duty_cycle * _PERIOD
        off_time = _PERIOD - on_time

        iterations = int(duration / _PERIOD)
        for _ in range(iterations):
            if self._cancel:
                break
            GPIO.output(self._pin, GPIO.HIGH)
            time.sleep(on_time)
            GPIO.output(self._pin, GPIO.LOW)
            time.sleep(off_time)

        self._last_stopped_pos = self.get_position()

    def get_position(self):
        """
        Get the current position of the extruder

        Returns:
            float -- how far from the extruder is from the fully un-extruded position, in mm
        """
        if self._thread:
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
        if self._thread:
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
        self._set_time = time.time()
        self._thread = Thread(target=self._run, args=(self._speed, duration))
        self._thread.start()

        # Optionally wait for the motor to stop
        if wait:
            self._thread.join()

    def join(self):
        """
        Wait for the extruder to stop, if it is moving
        """
        if self._thread:
            self._thread.join()

    @staticmethod
    def cleanup():
        """
        Clean up ALL RPi.GPIO
        """
        GPIO.cleanup()
