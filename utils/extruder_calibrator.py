import argparse

from cnc.hal_raspberry import rpgpio
from cnc.actuators.extruder import Extruder
from cnc.config import EXTRUDER_CONFIG
from threading import Thread


gpio = rpgpio.GPIO()
RANGE = 10  # number of seconds max to run one step of calibration
INCREMENT = .01


def prompt_duty_cycle(duty_cycle_range):
    return input('duty cycle: ({:0.4f}, {:0.4f}). Continue, (s)top, (r)everse, (i)ncrease delta, or (d)ecrease delta.'
        .format(duty_cycle_range[0], duty_cycle_range[1]))


def calibrate_direction(extruder, reverse=False):
    if reverse:
        start = RANGE
        end = 0
        delta = INCREMENT
    else:
        start = 0
        end = RANGE
        delta = -INCREMENT

    while True:
        # set extruder to move full speed in one direction using the current range
        extruder._stop()
        extruder._last_stopped_pos = start
        extruder.set_position(end, 1)

        # process input
        prompt = prompt_duty_cycle(extruder._duty_cycle_range)
        if prompt == 's':  # stop
            extruder._stop()
            break
        elif prompt == 'r':  # reverse
            temp = start
            start = end
            end = temp
            delta = -delta
        elif prompt == 'i':  # increase delta
            delta *= 10
            print('delta: {}'.format(delta))
        elif prompt == 'd':  # decrease delta
            delta *= .1
            print('delta: {}'.format(delta))

        # set next duty cycle range
        if reverse:
            extruder._duty_cycle_range = (extruder._duty_cycle_range[0], extruder._duty_cycle_range[1] + delta)
        else:
            extruder._duty_cycle_range = (extruder._duty_cycle_range[0] + delta, extruder._duty_cycle_range[1])

def calibrate(pin):
    extruder = Extruder(gpio, pin, RANGE, (0, 1), 1)

    # calibrate for reverse direction (min duty cycle)
    calibrate_direction(extruder, reverse=True)

    # calibrate for forward direction (max duty cycle)
    calibrate_direction(extruder, reverse=False)

    print('final duty cycle range: ({:0.4f}, {:0.4f})'.format(extruder._duty_cycle_range[0], extruder._duty_cycle_range[1]))


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
