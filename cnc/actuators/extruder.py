import time

from threading import Thread


_PERIOD = 1/50.0  # seconds


class Extruder(object):
    """
    An extruder controlled by a servo motor.

    This tracks the position of the extruder to keep it from hitting limits. It is all time-based and not precise!
    """

    def __init__(self, gpio, pin, range, duty_cycle_range, max_speed, initial_pos=0.0):
        """
        Arguments:
            gpio {rpgpio.GPIO} -- a GPIO object to set and clear pins
            pin {int} -- the GPIO pin to control the extuder's servo
            range {float} -- the range of the extruder in mm
            duty_cycle_range {(float, float)} --  the minimum and maximum duty cycle to operate the servo motor
            max_speed {float} -- the max speed of the extruder in mm/s

        Keyword Arguments:
            initial_pos {float} -- how many mm are already extruded on init (default {0.0})
        """
        self._gpio = gpio

        # config
        self._pin = pin
        self._range = range
        self._duty_cycle_range = duty_cycle_range
        self._max_speed = max_speed

        # state
        self._last_stopped_pos = initial_pos
        self._thread = None
        self._speed = None  # in mm/second
        self._set_time = None
        self._cancel = False

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
        """
        Run the extruder for some time and set the last stopped position when stopped

        Arguments:
            speed {float} -- the speed to run at, in mm/s (negative means reverse)
            duration {float} -- how long to run, in seconds

        Raises:
            ValueError -- if the magnitude of speed is greater than the max speed for this extruder
        """
        if abs(speed) > self._max_speed:
            raise ValueError('extruder too fast ({} mm/s)'.format(speed))

        duty_cycle_mid = (self._duty_cycle_range[0] + self._duty_cycle_range[1]) / 2.0
        duty_cycle_diff = self._duty_cycle_range[1] - self._duty_cycle_range[0]
        duty_cycle = duty_cycle_mid + duty_cycle_diff * (speed / self._max_speed) / 2.0

        self._run_at_duty_cycle(duty_cycle, duration)

    def _run_at_duty_cycle(self, duty_cycle, duration):
        """
        Run the extruder for some time and set the last stopped position when stopped

        Arguments:
            duty_cycle {float} -- the duty cycle to run the servo motor at (from 0 to 1). Note that the servo motor
                does not operate in the full range of duty cycles. This range must be calibrated.
            duration {float} -- how long to run, in seconds.
        """
        on_time = duty_cycle * _PERIOD
        off_time = _PERIOD - on_time

        iterations = int(duration / _PERIOD)
        for _ in range(iterations):
            if self._cancel:
                break
            self._gpio.set(self._pin)
            time.sleep(on_time)
            self._gpio.clear(self._pin)
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

    def set_position(self, position, speed, wait=False):
        """
        Command the extruder to go to an approximate position.
        The extruder's GPIO pin must already be initialized.

        Arguments:
            position {float} -- how far from the fully un-extruded position the extruder should reach, in mm

        Keyword Arguments:
            speed {float} -- The speed to travel at, in mm/s (default: {max speed})
            wait {bool} -- True iff this function should block until the motor stops (default: {False})

        Raises:
            ValueError -- if the set position is out of the range of the extruder
        """
        # Limit the position to a valid range
        if position < 0 or position > self._range:
            raise ValueError('extruder position out of bounds')

        # If the extruder is already moving, stop it
        if self._thread:
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

    def get_max_speed(self):
        """
        Get the max speed of the extruder

        Returns:
            float -- the max speed in mm/s
        """

        return self._max_speed
