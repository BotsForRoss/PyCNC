class ServoMotor(object):
    """
    Control a servo motor using DMA.
    This class could be used for any servo, but we use this one: https://www.adafruit.com/product/154
    """

    def __init__(self, pwm, pin, duty_cycle_stop, duty_cycle_range):
        """
        Arguments:
            pwm {DMAPWM} -- a DMAPWM object
            pin {int} -- the GPIO pin to control this servo
            duty_cycle_stop {float} -- the percent duty cycle to hold the motor at its neutral speed (stopped) or angle
            duty_cycle_range {float} -- the percent duty cycle added to duty_cycle_stop to reach max speed or angle
        """
        self._pwm = pwm
        self._pin = pin
        self._duty_cycle_mid = duty_cycle_stop
        self._duty_cycle_delta = duty_cycle_range

    def _set_duty_cycle(self, duty_cycle):
        """
        Arguments:
            duty_cycle {float} -- PWM duty cycle from 0 to 100
        """
        self._pwm.add_pin(self._pin, duty_cycle)

    def set(self, value):
        """
        Set the servo motor. This may set the speed or angle depending on the servo motor.

        Arguments:
            value {float} -- a value from -1 to 1. A value of -1 will set the motor to its minimum duty cycle, and 1
                will set to the maximum duty cycle.
        """
        duty_cycle = self._duty_cycle_mid + self._duty_cycle_delta * value
        self._set_duty_cycle(duty_cycle)

    def stop(self):
        """
        Remove the servo's pin from DMAPWM. This is not the same as setting the value to zero.
        """
        self._pwm.remove_pin(self._pin)
