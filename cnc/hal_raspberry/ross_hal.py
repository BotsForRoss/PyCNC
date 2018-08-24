"""
ross_hal implements the `hal` module with 6 servo motor paint extruders
"""
import logging
import cnc.hal_raspberry.hal as hal

from cnc.hal_raspberry import rpgpio
from cnc.config import *

# inherit a few things from hal_raspberry.hal
US_IN_SECONDS = hal.US_IN_SECONDS
gpio = hal.gpio
dma = hal.dma
pwm = hal.pwm
watchdog = hal.watchdog
STEP_PIN_MASK_X = hal.STEP_PIN_MASK_X
STEP_PIN_MASK_Y = hal.STEP_PIN_MASK_Y
STEP_PIN_MASK_Z = hal.STEP_PIN_MASK_Z

def init():
    """ Initialize GPIO pins and machine itself.
    """
    gpio.init(STEPPER_STEP_PIN_X, rpgpio.GPIO.MODE_OUTPUT)
    gpio.init(STEPPER_STEP_PIN_Y, rpgpio.GPIO.MODE_OUTPUT)
    gpio.init(STEPPER_STEP_PIN_Z, rpgpio.GPIO.MODE_OUTPUT)
    gpio.init(STEPPER_DIR_PIN_X, rpgpio.GPIO.MODE_OUTPUT)
    gpio.init(STEPPER_DIR_PIN_Y, rpgpio.GPIO.MODE_OUTPUT)
    gpio.init(STEPPER_DIR_PIN_Z, rpgpio.GPIO.MODE_OUTPUT)

    # TODO are these limit switches and are they configured like this?
    gpio.init(ENDSTOP_PIN_X, rpgpio.GPIO.MODE_INPUT_PULLUP)
    gpio.init(ENDSTOP_PIN_Y, rpgpio.GPIO.MODE_INPUT_PULLUP)
    gpio.init(ENDSTOP_PIN_Z, rpgpio.GPIO.MODE_INPUT_PULLUP)

    gpio.init(STEPPERS_ENABLE_PIN, rpgpio.GPIO.MODE_OUTPUT)
    gpio.init(EXTRUDER_1_PWM_PIN, rpgpio.GPIO.MODE_OUTPUT)
    gpio.init(EXTRUDER_2_PWM_PIN, rpgpio.GPIO.MODE_OUTPUT)
    gpio.init(EXTRUDER_3_PWM_PIN, rpgpio.GPIO.MODE_OUTPUT)
    gpio.init(EXTRUDER_4_PWM_PIN, rpgpio.GPIO.MODE_OUTPUT)
    gpio.init(EXTRUDER_5_PWM_PIN, rpgpio.GPIO.MODE_OUTPUT)
    gpio.init(EXTRUDER_6_PWM_PIN, rpgpio.GPIO.MODE_OUTPUT)
    gpio.clear(STEPPERS_ENABLE_PIN)
    gpio.clear(EXTRUDER_1_PWM_PIN)
    gpio.clear(EXTRUDER_2_PWM_PIN)
    gpio.clear(EXTRUDER_3_PWM_PIN)
    gpio.clear(EXTRUDER_4_PWM_PIN)
    gpio.clear(EXTRUDER_5_PWM_PIN)
    gpio.clear(EXTRUDER_6_PWM_PIN)
    watchdog.start()


def spindle_control(percent):
    """ Spindle control implementation.
    :param percent: Spindle speed in percent 0..100. 0 turns spindle off.
    """
    raise NotImplementedError('Spindle missing')


def fan_control(on_off):
    """
    Cooling fan control.
    :param on_off: boolean value if fan is enabled.
    """
    raise NotImplementedError('Fan missing')


def extruder_heater_control(percent):
    """ Extruder heater control.
    :param percent: heater power in percent 0..100. 0 turns heater off.
    """
    raise NotImplementedError('Extruder heater missing')


def bed_heater_control(percent):
    """ Hot bed heater control.
    :param percent: heater power in percent 0..100. 0 turns heater off.
    """
    raise NotImplementedError('Bed heater missing')


def get_extruder_temperature():
    """ Measure extruder temperature.
    Can raise OSError or IOError on any issue with sensor.
    :return: temperature in Celsius.
    """
    raise NotImplementedError('Extruder temperature missing')


def get_bed_temperature():
    """ Measure bed temperature.
    Can raise OSError or IOError on any issue with sensor.
    :return: temperature in Celsius.
    """
    raise NotImplementedError('Bed temperature missing')


def disable_steppers():
    """ Disable all steppers until any movement occurs.
    """
    hal.disable_steppers()


def calibrate(x, y, z):
    """ Move head to home position till end stop switch will be triggered.
    Do not return till all procedures are completed.
    :param x: boolean, True to calibrate X axis.
    :param y: boolean, True to calibrate Y axis.
    :param z: boolean, True to calibrate Z axis.
    :return: boolean, True if all specified end stops were triggered.
    """
    return hal.calibrate(x, y, z)


def move(generator):
    """ Move head to according pulses in PulseGenerator.
    :param generator: PulseGenerator object
    """
    raise NotImplementedError()  # TODO implement


def join():
    """ Wait till motors work.
    """
    return hal.join()


def deinit():
    """ De-initialise hal, stop any hardware.
    """
    join()
    disable_steppers()
    pwm.remove_all()
    gpio.clear(EXTRUDER_1_PWM_PIN)
    gpio.clear(EXTRUDER_2_PWM_PIN)
    gpio.clear(EXTRUDER_3_PWM_PIN)
    gpio.clear(EXTRUDER_4_PWM_PIN)
    gpio.clear(EXTRUDER_5_PWM_PIN)
    gpio.clear(EXTRUDER_6_PWM_PIN)
    watchdog.stop()


def watchdog_feed():
    """ Feed hardware watchdog. This method should be called at least
    once in 15 seconds. Also, this method can do no operation in hal
    implementation and there will not be emergency stop for heaters.
    """
    return hal.watchdog_feed()
