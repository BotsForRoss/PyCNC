"""
ross_hal implements the `hal` module with stepper motors that take actual steps -- not pulses.
"""
from cnc.hal_raspberry import rpgpio
from cnc.ross_config import *

gpio = rpgpio.GPIO()
dma = rpgpio.DMAGPIO()
pwm = rpgpio.DMAPWM()
watchdog = rpgpio.DMAWatchdog()

def init():
    """ Initialize GPIO pins and machine itself.
    """
    # set all the stepper motor pins to output mode
    stepper_pins = [
        STEPPER_X_1, STEPPER_X_2, STEPPER_X_3, STEPPER_X_4,
        STEPPER_Y_LEFT_1, STEPPER_Y_LEFT_2, STEPPER_Y_LEFT_3, STEPPER_Y_LEFT_4,
        STEPPER_Y_RIGHT_1, STEPPER_Y_RIGHT_2, STEPPER_Y_RIGHT_3, STEPPER_Y_RIGHT_4,
        STEPPER_Z_1, STEPPER_Z_2, STEPPER_Z_3, STEPPER_Z_4
    ]
    for pin in stepper_pins:
        gpio.init(pin, rpgpio.GPIO.MODE_OUTPUT)

    watchdog.start()


def spindle_control(percent):
    """ Spindle control implementation.
    :param percent: Spindle speed in percent 0..100. 0 turns spindle off.
    """
    raise NotImplementedError()


def fan_control(on_off):
    """
    Cooling fan control.
    :param on_off: boolean value if fan is enabled.
    """
    raise NotImplementedError()


def extruder_heater_control(percent):
    """ Extruder heater control.
    :param percent: heater power in percent 0..100. 0 turns heater off.
    """
    raise NotImplementedError()


def bed_heater_control(percent):
    """ Hot bed heater control.
    :param percent: heater power in percent 0..100. 0 turns heater off.
    """
    raise NotImplementedError()


def get_extruder_temperature():
    """ Measure extruder temperature.
    Can raise OSError or IOError on any issue with sensor.
    :return: temperature in Celsius.
    """
    raise NotImplementedError()


def get_bed_temperature():
    """ Measure bed temperature.
    Can raise OSError or IOError on any issue with sensor.
    :return: temperature in Celsius.
    """
    raise NotImplementedError()


def disable_steppers():
    """ Disable all steppers until any movement occurs.
    """
    raise NotImplementedError()


def calibrate(x, y, z):
    """ Move head to home position till end stop switch will be triggered.
    Do not return till all procedures are completed.
    :param x: boolean, True to calibrate X axis.
    :param y: boolean, True to calibrate Y axis.
    :param z: boolean, True to calibrate Z axis.
    :return: boolean, True if all specified end stops were triggered.
    """
    raise NotImplementedError()


def move(generator):
    """ Move head to according pulses in PulseGenerator.
    :param generator: PulseGenerator object
    """
    raise NotImplementedError()


def join():
    """ Wait till motors work.
    """
    raise NotImplementedError()


def deinit():
    """ De-initialise hal, stop any hardware.
    """
    raise NotImplementedError()


def watchdog_feed():
    """ Feed hardware watchdog. This method should be called at least
    once in 15 seconds. Also, this method can do no operation in hal
    implementation and there will not be emergency stop for heaters.
    """
    raise NotImplementedError()
