# -### boot.py

# Done by Dr.JJ
# https://github.com/yunnanpl/esp32_python_eq3

#-###
#-###
# -### imports, also config and settings
import os
# substitute with bytes((x for x in a if x >= 0x20 and x < 127))
#import re
from collections import OrderedDict
#import robust2 as umqtt
import simple2 as umqtt
import socket
import _thread
import gc
import ubluetooth
# not necessary
#from micropython import const
import time
import ntptime
import network
from secret_cfg import *
# speedup/slow down for energy saving :)
import machine
machine.freq(config['freq'])
#from machine import Pin, DAC, PWM, ADC, SoftI2C
#from machine import Pin
#import umqtt
#import math

gc.enable()

#-###
#-###
# -### activate ble
ble = ubluetooth.BLE()
if ble.active() == False:
    ble.active(True)

#-###
#-###
# -### create timers
timer_schedule = machine.Timer(0)
timer_work = machine.Timer(1)
timer_clean = machine.Timer(2)

#-###
#-###
# -### conenct to network
station = network.WLAN(network.STA_IF)
station.active(True)
#station.connect( config['wifi_name'], binascii.a2b_base64( config['wifi_pass'] ) )
station.connect(config['wifi_name'], "".join([chr(x) for x in config['wifi_pass']]))

#-###
#-###
# -### waiting for connection
while station.isconnected() == False:
    #print('LOG waiting for connection')
    time.sleep(1)  # sleep or pass

#-###
#-###
# -### getting ntp time
ntptime.host = config['ntp_host']
ntptime.settime()
#print('LOG NTP time set')

try:
    os.stat('webrepl_cfg.py')
    import webrepl
    webrepl.start()
except:
    pass

#-###
#-###
# -### clean up the memory and stuff
config = ''
del config
# a lot of garbage expected :D
gc.collect()

# -### BOOTED
# -### end
