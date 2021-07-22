import os
import time

from datetime import datetime

home = '/home/ubuntu/'
proj = f'{home}git/cm4-fan-control-service/'
main = f'{proj}main'
csv = f'{home}fancontrol.csv'

os.system(f'{main} set 128')

while True:
    with open(csv, 'a') as f:
        f.write('The current timestamp is: ' + str(datetime.now()) + '\n')
        f.close()

    time.sleep(10)

