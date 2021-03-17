# esp32_python_eq3
Bluetooth bridge between EQ3 thermostat and WLAN network, using ESP32, micropython and mqtt.

# Idea
I used a lot of other solutions, but it seemed to be not stable for me, or hard to extend (for me :)).
In order to use the esp32 for EQ3 and Mijia temperature sensors (or even some BME280-like ones) I needed to get something done on my own.

So I decided to rewrite it in python (micropython) on esp32.

This is the result. It can mimic and substitute the esp32_mqtt_eq3 solution from softypit, as it accepts the same mqtt input and returns similar mqtt json output.

# Status

It works quite stable. More stable for me than esp32_mqtt_eq3 solution.
I added also work list (so multpiple work can be added, and it will be done one after another).
This solution reads data from Mijia sensors. Plan is to add BME280 and other "local" sensors.
It also does BLE scans, and can report bluetooth devices in the area (for presence testing etc.).

Communication is done by MQTT, and the syntax is near to identical to esp32_mqtt_eq3 so it can be substituted.
The syntax is still simpler than esp32_mqtt_eq3.

Serial or WebREPL can be used. THere are some useful functions on the device.

## Tests
After 10 days, 4 ESP32 are running stable. No signal or command lost (none noticed).

## Shell
It is possible to connect to shell of MicroPython for some extra functionality.
For this, it is reasonable to setup and use WebREPL, to issue commands and upgrade scripts remotely.
http://micropython.org/webrepl/

There are internal functions:
 - fprint()
   - to cleanly print all visible clients (if not visible, removed after 2 hours)
 - fclean()
   - triggers cleaning
 - fble_scan()
   - triggers BLE scan, if triggered from console, it is longer than automatic one
 - (time.ticks_ms()/1000/60/60/24)
   - prints uptime in days
   - this will be cleaned up
and variables:
 - vglob
   - global work settings
   - if status is 8, then waiting, otherwise working
 - vglob_list
   - variable with list of visible clients
   - this can be printed nicely with fprint()
 - vwork
   - work list, it is usually empty

## Features (and anti-features)
 - NO webpage
 - NO AP configuration (only config file)
 - robust WIFI, survives disconnections, reconnects, etc.
 - robust BLE, survives bad addresses, bad messages, disconnections, etc. Has automatic connections cleaning.
 - robust MQTT, survives disconnections, automatically resubscribes, etc.
 - has "unique" worklist
   - if the same message will be sent 5 times, it will be processed once
   - if there is a not-yet-processed work in the list for setting temp, then another work for the same device overwrites previous command
 - is persistent, if the device is known, but does not respond in 10-20 sec slot, then work is put at the end, and new work is done 
   
## Plan
 - add basic AP for configuration
 - add basic status and control webpage
 - add other temperature sensors like Mijia, BME280, etc.
 - add PID regulator for automatic temperature regulation
   - in case of real temperature input
 - add automatic integration in home assistant (yes, I am using hass :D).
 - add other basic info, like battery, mode, etc.
 - add offset setting, both in eq3 and "external" through esp32
 - think about adding support for the new firmware version of eq3 (later :D)
   - maybe not so tragic at all, it has to do with the new pairing
   - https://github.com/rytilahti/python-eq3bt/issues/41
   - and micropython ble seems to support pairing already
   - https://github.com/micropython/micropython/pull/6651
 - add white-list and black-list to enforce or ignore some devices
 - maybe - add temperature history and eq3 setting history graph

# References

 - mqtt - most robust library chosen
   - https://github.com/fizista/micropython-umqtt.simple2 with https://github.com/fizista/micropython-umqtt.robust2
   - not clear if necessary

# Other interesting liks
https://github.com/softypit/esp32_mqtt_eq3
