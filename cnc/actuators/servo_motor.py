class ServoMotor(object):
    """
    Control a servo motor using DMA and track the approximate position
    This class could be used for any servo, but we use this one: https://www.adafruit.com/product/154
    """

    def __init__(self, pwm, pin, duty_cycle_range):
        """
        Arguments:
            pwm {DMAPWM} -- a DMAPWM object
            pin {int} -- the GPIO pin to control this servo
            duty_cycle_range {(float, float)} -- the min and max duty cycle to operate this motor (from 0 to 100)
        """
        self._pwm = pwm
        self._pin = pin
        self._duty_cycle_mid = (duty_cycle_range[0] + duty_cycle_range[1]) / 2.0
        self._duty_cycle_delta = (duty_cycle_range[1] - duty_cycle_range[0]) / 2.0

    def _set_duty_cycle(self, duty_cycle):
        """
        Arguments:
            duty_cycle {float} -- PWM duty cycle from 0 to 100
        """
        self._pwm.add_pin(self._pin, duty_cycle)

    def set_speed(self, speed):
        """
        Set the speed of the servo motor

        Arguments:
            speed {float} -- a speed from -1 to 1 relative to the full speed of the servo motor
        """
        duty_cycle = self._duty_cycle_mid + self._duty_cycle_delta * speed
        self._set_duty_cycle(duty_cycle)

    def stop(self):
        """
        Remove the servo's pin from DMAPWM. This is not the same as setting the speed to zero.
        """
        self._pwm.remove_pin(self._pin)
