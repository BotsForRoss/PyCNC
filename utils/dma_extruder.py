import sys
import time

from cnc.config import EXTRUDER_CONFIG
from cnc.hal_raspberry import rpgpio


pin = 23
duty_cycle = float(sys.argv[1])

gpio = rpgpio.GPIO()
pwm = rpgpio.DMAPWM()
watchdog = rpgpio.DMAWatchdog()

gpio.init(pin, rpgpio.GPIO.MODE_OUTPUT)
gpio.clear(pin)
watchdog.start()

pwm.add_pin(pin, duty_cycle)
time.sleep(3)

# for i in range(100):
#   print(i)
#   pwm.add_pin(pin, i)
#   time.sleep(1)

pwm.remove_pin(pin)
gpio.clear(pin)
watchdog.stop()

