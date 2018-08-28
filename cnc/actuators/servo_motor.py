class ServoMotor(object):
    """
    Control a servo motor using DMA and track the approximate position
    This class could be used for any servo, but we use this one: https://www.adafruit.com/product/154
    """

    # These values are based off of this guide:
    # https://learn.sparkfun.com/tutorials/pi-servo-hat-hookup-guide#software---python
    _DUTY_CYCLE_STOP = .305  # the duty cycle needed to hold the motor still
    _DUTY_CYCLE_RANGE = .101  # what to add/subtract from _DUTY_CYCLE_STOP to get full forward/reverse

    def __init__(self, pwm, pin):
        """
        Arguments:
            pwm {DMAPWM} -- a DMAPWM object
            pin {int} -- the GPIO pin to control this servo
        """
        self._pwm = pwm
        self._pin = pin

    def _set_duty_cycle(self, duty_cycle):
        """
        Arguments:
            duty_cycle {float} -- PWM duty cycle from 0 to 1
        """
        self._pwm.add_pin(self._pin, duty_cycle)

    def set_speed(self, speed):
        """
        Set the speed of the servo motor

        Arguments:
            speed {float} -- a speed from -1 to 1 relative to the full speed of the servo motor
        """
        duty_cycle = self._DUTY_CYCLE_STOP + self._DUTY_CYCLE_RANGE * speed
        self._set_duty_cycle(duty_cycle)

    def stop(self):
        """
        Remove the servo's pin from DMAPWM. This is not the same as setting the speed to zero.
        """
        self._pwm.remove_pin(self._pin)
