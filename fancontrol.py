import os
import subprocess

from datetime import datetime
from dotenv import load_dotenv
from gpiozero import CPUTemperature
from time import sleep, strftime, time

load_dotenv()

# Config
elastic_host = os.getenv('ELASTICSEARCH_HOST')
elastic_pass = os.getenv('ELASTICSEARCH_PASSWORD')
fan_min_temp = 40.0 
fan_full_temp = 50.0
path_home = '/home/ubuntu/'
path_proj = f'{path_home}cm4-fan-control-service/'
path_main = f'{path_proj}main'


def get_fan_rpm():
    # Example output:
    # USE_DEV_LIB 
    # Current environment: Ubuntu
    # DEV I2C Device
    # DEV I2C Device
    # I2C ok !
    # End Res_value: 923
    # FAN_SPEED: 4260
    # ---------------------
    output = subprocess.run([path_main, 'rpm'], stdout=subprocess.PIPE)
    output = output.stdout.decode('utf-8').rstrip()
    lines = output.split('\n')
    for line in lines:
        if line.startswith('FAN_SPEED: '):
            rpm = line[len('FAN_SPEED: '):]
            return rpm

    raise RuntimeError('FAN_SPEED not found in command output')


def get_desired_fan_speed(cpu_temp: float):

    # CPU temp below which fan will be deactivated.
    if cpu_temp < fan_min_temp:
        return 0

    # CPU temp above which fan will be on maximum.
    if cpu_temp >= fan_full_temp:
        return 255

    # Get percentage value of cpu_temp between min and full temps.
    t = cpu_temp - fan_min_temp
    m = fan_full_temp - fan_min_temp
    q = t / m
    p = q * 100
    print(f'desired_fan_speed: {p}%')

    # Valid fan speed value: 0-255.
    assert q <= 1
    return 255 * q


def set_fan_speed(fan_speed: int):
    assert fan_speed >= 0
    assert fan_speed <= 255
    #os.system(f'{path_main} set {fan_speed}')
    #output = subprocess.run([path_main, 'set', str(fan_speed)], stdout=subprocess.PIPE)
    #output = output.stdout.decode('utf-8').rstrip()
    subprocess.run([path_main, 'set', str(fan_speed)], stdout=subprocess.PIPE)


while True:
    
    # CPU frequency
    output = subprocess.run(['vcgencmd', 'measure_clock', 'arm'], stdout=subprocess.PIPE)
    cpu_freq = output.stdout.decode('utf-8').rstrip()
    assert cpu_freq.startswith('frequency')
    cpu_freq = cpu_freq[len('frequency'):]
    print(f'cpu_freq: {cpu_freq}')

    # CPU temperature - method 1
    cpu = CPUTemperature()
    cpu_temp_alt = cpu.temperature
    cpu_temp_alt = float(cpu_temp_alt)
    print(f'cpu_temp_alt: {cpu_temp_alt}')

    # CPU temperature - method 2
    output = subprocess.run(['vcgencmd', 'measure_temp'], stdout=subprocess.PIPE)
    cpu_temp = output.stdout.decode('utf-8').rstrip()
    assert cpu_temp.startswith('temp=')
    cpu_temp = cpu_temp[len('temp='):]
    assert cpu_temp.endswith('\'C')
    cpu_temp = cpu_temp[:len('\'C')]
    cpu_temp = float(cpu_temp)
    print(f'cpu_temp: {cpu_temp}')

    # Is the CPU is throttled? 0x0 means not throttled. TODO: What value for throttled?
    output = subprocess.run(['vcgencmd', 'get_throttled'], stdout=subprocess.PIPE)
    cpu_throttled = output.stdout.decode('utf-8').rstrip()
    assert cpu_throttled.startswith('throttled=')
    cpu_throttled = cpu_throttled[len('throttled='):]
    print(f'cpu_throttled: {cpu_throttled}')

    # Fan RPM
    fan_rpm = get_fan_rpm()
    print(f'fan_rpm: {fan_rpm}')
   
    # Fan speed
    fan_speed = get_desired_fan_speed(cpu_temp)
    
    # Adjust fan speed according to temperature.
    set_fan_speed(fan_speed)
    
    # TODO: Send the data to Elasticsearch
    #   TODO: Add CPU frequency to log.
    #   TODO: Add whether the CPU is throttled to log.
    #   TODO: Add fan RPM to log.

    sleep(1)

