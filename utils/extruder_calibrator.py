import argparse

from cnc.hal_raspberry import rpgpio
from cnc.actuators.extruder import Extruder
from cnc.config import EXTRUDER_CONFIG
from threading import Thread


gpio = rpgpio.GPIO()
RANGE = 10  # number of seconds max to run one step of calibration
INCREMENT = 1.0


duty_cycle_range = (0, 100)


def prompt_duty_cycle():
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
        prompt = prompt_duty_cycle()
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
            next_range = (duty_cycle_range[0] + delta, duty_cycle_range[1])
        else:
            next_range = (duty_cycle_range[0], duty_cycle_range[1] + delta)
        extruder._motor._duty_cycle_mid = (next_range[0] + next_range[1]) / 2.0
        extruder._motor._duty_cycle_delta = (next_range[1] - next_range[0]) / 2.0

def calibrate(pin):
    extruder = Extruder(gpio, pin, RANGE, duty_cycle_range, 1)

    # calibrate for reverse direction (min duty cycle)
    print('calibrating min duty cycle')
    calibrate_direction(extruder, reverse=True)

    # calibrate for forward direction (max duty cycle)
    print('calibrating max duty cycle')
    calibrate_direction(extruder, reverse=False)

    print('final duty cycle range: ({:0.4f}, {:0.4f})'.format(duty_cycle_range[0], duty_cycle_range[1]))


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
