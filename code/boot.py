#-### boot.py

# Done by Dr.JJ
# https://github.com/yunnanpl/esp32_python_eq3

#-###
#-###
#-### imports, also config and settings
from secret_cfg import *
# speedup/slow down for energy saving :)
import machine
machine.freq( config['freq'] )
#from machine import Pin, DAC, PWM, ADC, SoftI2C
#from machine import Pin
import network
import ntptime
import time
from micropython import const
import ubluetooth
import gc
import _thread
import socket
#import umqtt
import robust2 as umqtt
from collections import OrderedDict
import re

gc.enable()

#-###
#-###
#-### activate ble
ble = ubluetooth.BLE()
if ble.active() == False:
    ble.active( True )

#-###
#-###
#-### create timers
timer_scan = machine.Timer(0)
timer_work = machine.Timer(1)
timer_clean = machine.Timer(2)

#-###
#-###
#-### conenct to network
station = network.WLAN(network.STA_IF)
station.active(True)
#station.connect( config['wifi_name'], binascii.a2b_base64( config['wifi_pass'] ) )
station.connect( config['wifi_name'], "".join( [ chr(x) for x in config['wifi_pass'] ] ) )

#-###
#-###
#-### waiting for connection
while station.isconnected() == False:
  #print('LOG waiting for connection')
  time.sleep(1) # sleep or pass

#-###
#-###
#-### getting ntp time
ntptime.host = config['ntp_host']
ntptime.settime()
#print('LOG NTP time set')

import webrepl
webrepl.start()

#-###
#-###
#-### clean up the memory and stuff
config = ''
del config
# a lot of garbage expected :D
gc.collect()

#-### BOOTED
#-### end
