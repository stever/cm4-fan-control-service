import os
import subprocess

from datetime import datetime
from gpiozero import CPUTemperature
from time import sleep, strftime, time

home = '/home/ubuntu/'
proj = f'{home}cm4-fan-control-service/'
main = f'{proj}main'
csv = f'{home}fancontrol.csv'

os.system(f'{main} set 128')

# TODO: Adjust fan speed according to temperature.
# TODO: Add fan RPM to log.
# TODO: Add CPU frequency to log.
# TODO: Add whether the CPU is throttled to log.
# TODO: Send the data to Elasticsearch instead of local log file?

cpu = CPUTemperature()
print(cpu.temperature)

result = subprocess.run(['vcgencmd', 'measure_clock', 'arm'], stdout=subprocess.PIPE)
print(result.stdout.decode("utf-8").rstrip())

result = subprocess.run(['vcgencmd', 'measure_temp'], stdout=subprocess.PIPE)
print(result.stdout.decode("utf-8").rstrip())

result = subprocess.run(['vcgencmd', 'get_throttled'], stdout=subprocess.PIPE)
print(result.stdout.decode("utf-8").rstrip())

#with open(csv, 'a') as log:
#    while True:
#        cpu = CPUTemperature()
#        temp = str(cpu.temperature)
#        time = strftime("%Y-%m-%d %H:%M:%S")
#        log.write(f'{time},{temp}\n')
#        sleep(1)

