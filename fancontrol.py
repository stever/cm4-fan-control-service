import json
import os
import psutil
import requests
import socket
import subprocess
import sys

from datetime import datetime
from dotenv import load_dotenv
from gpiozero import CPUTemperature
from requests.auth import HTTPBasicAuth
from time import sleep, strftime, time

# Disable warning on HTTPS where SSL verification is off.
# NOTE: This is because Elastic cluster uses self-signed certificate.
requests.packages.urllib3.disable_warnings() 

# Config
path_home = '/home/ubuntu/'
path_proj = f'{path_home}cm4-fan-control-service/'
path_main = f'{path_proj}main'
path_dotenv = f'{path_proj}.env'
assert os.path.isfile(path_dotenv), '.env file is missing!'
load_dotenv(path_dotenv)
elastic_host = os.getenv('ELASTICSEARCH_HOST')
elastic_pass = os.getenv('ELASTICSEARCH_PASSWORD')
elastic_user = 'elastic'
fan_min_temp = 40.0 
fan_full_temp = 60.0
sleep_secs = 3

# Machine info
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
print(f'hostname: {hostname}')
print(f'local_ip: {local_ip}')


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
            return int(rpm)

    #raise RuntimeError('FAN_SPEED not found in command output')
    return 0 # There may be no fan available.


def get_desired_fan_speed(cpu_temp: float):

    # CPU temp below which fan will be deactivated.
    if cpu_temp < fan_min_temp:
        print('desired_fan_speed: 0%')
        return 0

    # CPU temp above which fan will be on maximum.
    if cpu_temp >= fan_full_temp:
        print('desired_fan_speed: 100%')
        return 255

    # Get percentage value of cpu_temp between min and full temps.
    t = cpu_temp - fan_min_temp
    m = fan_full_temp - fan_min_temp
    q = t / m
    p = q * 100
    print(f'desired_fan_speed: {p}%')

    # Valid fan speed value: 0-255.
    assert q <= 1
    return int(255 * q)


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
    desired_fan_speed = get_desired_fan_speed(cpu_temp)
    print(f'desired_fan_speed: {desired_fan_speed}')
    
    # Adjust fan speed according to temperature.
    set_fan_speed(desired_fan_speed)

    # CPU usage
    cpu_usage = psutil.cpu_percent()
    print(f'cpu_usage: {cpu_usage}%')

    # Memory usage
    mem_usage = psutil.virtual_memory().percent
    print(f'mem_usage: {mem_usage}%')

    # Disk usage
    disk_usage = psutil.disk_usage(os.sep).percent
    print(f'disk_usage: {disk_usage}%')

    try:
        payload = {
            'cpu_freq': cpu_freq,
            'cpu_temp': cpu_temp,
            'cpu_throttled': cpu_throttled,
            'cpu_usage': cpu_usage / 100,
            'disk_usage': disk_usage / 100,
            'fan_rpm': fan_rpm,
            'fan_speed': desired_fan_speed,
            'fan_full_temp': fan_full_temp,
            'fan_min_temp': fan_min_temp,
            'hostname': hostname,
            'local_ip': local_ip,
            'mem_usage': mem_usage / 100,
            'time': time()
        }

        url = f'{elastic_host}/fan_control/_doc/'
        headers = {'Content-Type': 'application/json', 'Accept-Charset': 'UTF-8'}
        data = json.dumps(payload)
        auth = HTTPBasicAuth(elastic_user, elastic_pass)
        verify = False

        #print(f'url: {url}')
        #print(f'data: {data}')

        response = requests.post(url, data=data, headers=headers, auth=auth, verify=verify)
        assert response.status_code == 201
   
    except:
        print("Unexpected error:", sys.exc_info()[0])

    sleep(sleep_secs)

