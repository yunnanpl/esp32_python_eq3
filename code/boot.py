# -*- coding: ascii -*-
# -### boot.py

#-###
#-###
# -### imports, also CONFIG and settings
#
import gc
gc.enable()
gc.threshold(30000) # ??? was 40000, was 10000
import micropython
micropython.opt_level(3)
micropython.alloc_emergency_exception_buf(2) # was 100
#import uasyncio as asyncio #moved to main
#import _thread #moved to main
import network
import ntptime
import time
import ubluetooth
import simple2 as umqtt
import os
from secret_cfg import *
# speedup/slow down for energy saving :)
import machine
machine.freq(CONFIG['freq'])
#

#-###
#-### CONFIG compatibility
# moving variable to list of permanent variables, in order to query ntp sometimes
# and not to change CONFIG
try:
    CONFIG2['mqtt_thermo_src'] = CONFIG2['mqtt_temp_src']
except:
    pass

try:
    CONFIG2['ntp_host'] = CONFIG['ntp_host']
except:
    pass

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
    station.connect(CONFIG['wifi_name'], "".join([chr(x) for x in CONFIG['wifi_pass']]))
except:
    pass

#-###
#-###
# -### waiting for connection
while station.isconnected() == False:
    # print('LOG waiting for connection')
    time.sleep(0.5)  # sleep or pass
    # if not conencted in 15 sec, then restart
    if time.ticks_ms() > 15000:
        print('- no WIFI -> reset')
        machine.reset()

#-###
#-###
# -### getting ntp time
try:
    ntptime.host = CONFIG2['ntp_host']
    ntptime.settime()
except:
    ### v52_04 if no server available, set no time, in case if no internet
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
    mqtth = umqtt.MQTTClient(CONFIG2['mqtt_usr'], CONFIG2['mqtt_srv'], user=CONFIG2['mqtt_usr'], password=CONFIG2['mqtt_pass'], port=1883)
    #mqtth.keepalive = 180
    mqtth.keepalive = 90
    while mqtth.connect() == 1:
        time.sleep(0.5)
        # if not conencted in 20 sec, then restart
        if time.ticks_ms() > 20000:
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
# ble.config(mtu=128)
device_name = 'ESP32_' + str(station.ifconfig()[0].split('.')[3])
ble.config(gap_name=device_name)

# -### clean up the memory and stuff
CONFIG = ''
del CONFIG
# a lot of garbage expected :D

print('= ip', str( station.ifconfig()[0] ) )
print('= time', ntptime.time() )
print('= mqtt ping', str(time.ticks_ms() - mqtth.last_cpacket) )
print('+ booted')

del micropython
gc.collect()
# -### BOOTED
# -### end
