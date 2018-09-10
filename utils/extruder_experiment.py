import argparse
import time

from cnc.hal_raspberry import rpgpio
from cnc.actuators.servo_motor import ServoMotor
from cnc.config import EXTRUDER_CONFIG


gpio = rpgpio.GPIO()
pwm = rpgpio.DMAPWM()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='try a duty cycle for a servo motor')
    parser.add_argument('-p', '--pin', type=int, help='GPIO pin of servo motor')
    parser.add_argument('--id', type=int, default=0, help='ID of extruder')
    parser.add_argument('-d', '--duty', type=float, default=0, help='duty cycle 0 to 100')
    parser.add_argument('-t', '--time', type=float, help='How long to run the motor. Will run interactively if not '
        'specified.')
    args = parser.parse_args()

    if args.pin:
        pin = args.pin
    else:
        pin = EXTRUDER_CONFIG[args.id]['pin']
    duty = args.duty

    motor = ServoMotor(pwm, pin, 0, 0)

    try:
        if args.time:
            motor._set_duty_cycle(duty)
            time.sleep(args.time)
        else:
            print('Setting extruder on pin {}'.format(pin))
            print('Enter a duty cycle from 0 to 100')
            print('Quit with ^D or ^C')
            while True:
                motor._set_duty_cycle(duty)
                duty = float(input('> '))
                motor.stop()
                time.sleep(.1)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        motor.stop()
    
        pwm.remove_all()
        gpio.clear(pin)

