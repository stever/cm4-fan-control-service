# CM4 Fan Control Service

Fan control service for Raspberry Pi Compute Module 4.

## Configuration

```bash
vi .env
```

```
ELASTICSEARCH_HOST="https://10.43.143.94:9200"
ELASTICSEARCH_PASSWORD="<password>"
```

## Build

```bash
mkdir bin
make
./main
sudo ./main set 255 # max speed
sudo ./main set 128 # mid speed
```

## Python setup

```bash
sudo pip install gpiozero
sudo pip install RPi.GPIO
sudo pip install python-dotenv
sudo pip install psutil
```

## Service setup

```bash
sudo cp fancontrol.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fancontrol
sudo systemctl start fancontrol
sudo systemctl status fancontrol
```

## Additional service commands

```bash
sudo systemctl stop fancontrol # to stop the service
sudo systemctl restart fancontrol # to restart
sudo systemctl status fancontrol # to check status
```

## EMC2301

Software for controlling an EMC2301 via i2c and other standards.

For use with Raspbery Pi using Linux type operating systems.

Download files, navigate to downloaded directory, run `sudo make -j 8`.

Two commands are currently supported, `rpm` and `set`. `rpm` will print what the fan is doing to the terminal, `set` along with a value (0-255) will set the fan to that step value.

Examples:

`./main rpm` <<< Reads what the chip/fan is doing
```
USE_DEV_LIB 
Current environment: Raspbian
DEV I2C Device
DEV I2C Device
I2C ok !
End Res_value: 437
FAN_SPEED: 8998
---------------------
```
`./main set 255` <<< Sets the chip/fan to maximum
```
USE_DEV_LIB 
Current environment: Raspbian
DEV I2C Device
DEV I2C Device
I2C ok !
Setting fan to: 255
End Res_value: 508
FAN_SPEED: 7740
---------------------
```

This is nothing fancy. There is no GUI. There is no automatic temp-fan control. It is command line only to quickly read or set the fan speed of a raspberry pi, nothing else.

Have fun, I'm not responsible for what you do to your own stuff running this code. (But if something sets itself on fire, send me a video of it as it'll be epic.)

(May work with nvidia jetson as well as over SPI and/or GPIO, don't know, haven't tested it, but it seems the waveshare backend has support for it.)
