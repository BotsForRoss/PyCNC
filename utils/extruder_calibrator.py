import argparse

from cnc.hal_raspberry import rpgpio
from cnc.actuators.extruder import Extruder
from cnc.config import EXTRUDER_CONFIG
from threading import Thread


gpio = rpgpio.GPIO()
RANGE = 10  # number of seconds max to run one step of calibration


def prompt_duty_cycle(duty_cycle_range):
    stop = input('duty cycle: ({:0.4f}, {:0.4f}). Moving?'.format(duty_cycle_range[0], duty_cycle_range[1]))
    print('\r')
    return stop == 'y'


def calibrate(pin):
    extruder = Extruder(gpio, pin, RANGE, (0, 1), 1)

    # calibrate for reverse direction (min duty cycle)
    while extruder._duty_cycle_range[0] < extruder._duty_cycle_range[1]:
        extruder._stop()
        extruder._last_stopped_pos = RANGE
        extruder.set_position(0, 1)
        if prompt_duty_cycle(extruder._duty_cycle_range):
            break
        extruder._duty_cycle_range[0] += .01

    # calibrate for forward direction (max duty cycle)
    while extruder._duty_cycle_range[1] > extruder._duty_cycle_range[0]:
        extruder._stop()
        extruder._last_stopped_pos = 0
        extruder.set_position(RANGE, 1)
        if prompt_duty_cycle(extruder._duty_cycle_range):
            break
        extruder._duty_cycle_range[1] -= .01

    print('final duty cycle range: ({}, {})'.format(extruder._duty_cycle_range[0], extruder._duty_cycle_range[1]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='calibrate a servo motor')
    parser.add_argument('--pin', type=int, help='GPIO pin of servo motor')
    parser.add_argument('--id', type=int, default=0, help='ID of extruder')
    args = parser.parse_args()

    if args.pin:
        pin = args.pin
    else:
        pin = EXTRUDER_CONFIG[args.id]['pin']

    calibrate(pin)
