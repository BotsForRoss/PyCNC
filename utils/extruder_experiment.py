import argparse
import time

from cnc.hal_raspberry import rpgpio
from cnc.actuators.servo_motor import ServoMotor
from cnc.config import EXTRUDER_CONFIG


gpio = rpgpio.GPIO()
pwm = rpgpio.DMAPWM()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='try a duty cycle for a servo motor')
    parser.add_argument('--pin', type=int, help='GPIO pin of servo motor')
    parser.add_argument('--id', type=int, default=0, help='ID of extruder')
    parser.add_argument('duty', type=float, help='duty cycle 0 to 100')
    args = parser.parse_args()

    if args.pin:
        pin = args.pin
    else:
        pin = EXTRUDER_CONFIG[args.id]['pin']

    motor = ServoMotor(pwm, pin, (0, 100))

    try:
        motor._set_duty_cycle(args.duty)
        time.sleep(10)
    except KeyboardInterrupt:
        pass

    motor.stop()
    
    pwm.remove_all()
    gpio.clear(pin)

