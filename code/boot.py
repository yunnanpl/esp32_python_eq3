# -### boot.py

# Done by Dr.JJ
# https://github.com/yunnanpl/esp32_python_eq3

#-###
#-###
# -### imports, also config and settings
#
import uasyncio as asyncio
import _thread
import network
import ntptime
import time
import ubluetooth
import gc
import simple2 as umqtt
#import robust2 as umqtt
#from collections import OrderedDict
import os
from secret_cfg import *
# speedup/slow down for energy saving :)
import machine
machine.freq(config['freq'])
#
# import re
# import robust2 as umqtt
# import socket
# not necessary
# from micropython import const
#
# other modules
# from machine import Pin, DAC, PWM, ADC, SoftI2C
# from machine import Pin
# import umqtt
# import math

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
#timer_schedule = machine.Timer(0)
timer_work = machine.Timer(0)
timer_check = machine.Timer(1)

#-###
#-###
# -### conenct to network
try:
    station = network.WLAN(network.STA_IF)
    station.active(True)
    # station.connect( config['wifi_name'], binascii.a2b_base64( config['wifi_pass'] ) )
    # config['wifi_name'] = "asdasd"
    station.connect(config['wifi_name'], "".join([chr(x) for x in config['wifi_pass']]))
except:
    pass

#-###
#-###
# -### waiting for connection
while station.isconnected() == False:
    # print('LOG waiting for connection')
    time.sleep(0.5)  # sleep or pass
    # if not conencted in 10 sec, then restart
    if time.ticks_ms() > 10000:
        print('- no WIFI -> reset')
        machine.reset()

#-###
#-###
# -### getting ntp time
try:
    # moving variable to list of permanent variables, in order to query ntp sometimes
    # and not to change config
    config2['ntp_host'] = config['ntp_host']
    ntptime.host = config2['ntp_host']
    ntptime.settime()
except:
    pass
# print('LOG NTP time set')

try:
    # if webrepl_cfg file exists then start webrepl
    # if not, then pass
    os.stat('webrepl_cfg.py')
    import webrepl
    webrepl.start()
except:
    pass

try:
    mqtth = umqtt.MQTTClient(config2['mqtt_usr'], config2['mqtt_srv'], user=config2['mqtt_usr'], password=config2['mqtt_pass'], port=1883)
    mqtth.keepalive = 180
    while mqtth.connect() == 1:
        time.sleep(0.5)
        # if not conencted in 15 sec, then restart
        if time.ticks_ms() > 15000:
            print('- no MQTT -> reset')
            machine.reset()
    mqtth.ping()
    mqtth.set_callback(fmqtt_irq)
    # keepalive describes the connection lifetime, 0 means not defined
    #mqtth.keepalive = 1
except:
    pass

#-###
#-### some other settings

# ble.config(rxbuf=256)
ble.config(rxbuf=512)
ble.config(mtu=515)
# ble.config(gap_name=b'ESP32_5')
#ble.config( gap_name='ESP32_'+str(ble.config('mac')[1][5]))
device_name = 'ESP32_' + str(station.ifconfig()[0].split('.')[3])
ble.config(gap_name=device_name)

# -### clean up the memory and stuff
config = ''
del config
# a lot of garbage expected :D

print('- ip', str( station.ifconfig()[0] ) )
print('- time', ntptime.time() )
print('- mqtt ping', str(time.ticks_ms() - mqtth.last_cpacket) )
print('= booted')

gc.collect()
# -### BOOTED
# -### end
