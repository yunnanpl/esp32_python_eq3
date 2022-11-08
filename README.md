# esp32_python_eq3
Bluetooth bridge between eqiva EQ3 thermostat and WLAN network, using ESP32, micropython and mqtt.

 - INSTRUCTION https://github.com/yunnanpl/esp32_python_eq3/blob/master/INSTRUCTION.md
 - CHANGELOG https://github.com/yunnanpl/esp32_python_eq3/blob/master/CHANGELOG.md

 - https://www.eq-3.de/produkte/eqiva/detail/bluetooth-smart-heizkoerperthermostat.html

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
The aim is stability.
Test system is 4 ESP32 controlling 9 EQ3 (around 2 EQ3 for each ESP32 and reading out 2 thermometers).
Anything can happen: Battery on EQ3 runs out. BLE packets get corrupted, etc... WLAN breaks, MQTT server dies, bad work is sent... DOS happens...
I tried to pick up all imaginable errors. I do up to 700 queries daily (every 2-3 minutes), and send 10-50 commands.
At best, the device should never loose work, even if it is forced sometimes to reboot.

Tests with newest version... 
 - 48h, 1400 queries, 30 commands for each of EQ3, configuration as written above -> no issues
 - further testing

It seems that RSSI above -90 leads to issues with connection. It will connect, but after a few tries.
Below -90 it works without any issues.

## Features (and anti-features)
 - NEW basic webpage added
 - NO AP configuration (only config file)
 - robust WIFI, survives disconnections, reconnects, etc.
 - robust BLE, survives bad addresses, bad messages, disconnections, etc. Has automatic connections cleaning.
 - robust MQTT, survives disconnections, automatically resubscribes, etc.
   - more robust mqtt, as there were issues that mqtt-robust lib, have not noticed that it was not subscribed
 - has "unique" worklist
   - if the same message will be sent 5 times, it will be processed once
   - if there is a not-yet-processed work in the list for setting temp, then another work for the same device overwrites previous command
 - is persistent, if the device is known, but does not respond in 10-20 sec slot, then work is put at the end, and new work is done 
   
## Plan
 - add basic AP for configuration
 - add other temperature sensors like Mijia, BME280, etc.
 - add PID regulator for automatic temperature regulation
   - in case of real temperature input
 - add other basic info, like battery, mode, etc.
 - add offset setting, both in eq3 and "external" through esp32
 - think about adding support for the new firmware version of eq3 (later :D)
   - maybe not so tragic at all, it has to do with the new pairing
   - https://github.com/rytilahti/python-eq3bt/issues/41
   - and micropython ble seems to support pairing already
   - https://github.com/micropython/micropython/pull/6651
 - maybe - add temperature history and eq3 setting history graph

# References

 - mqtt - most robust library chosen
   - https://github.com/fizista/micropython-umqtt.simple2 with https://github.com/fizista/micropython-umqtt.robust2
   - not clear if necessary

# Other interesting liks
 - https://github.com/softypit/esp32_mqtt_eq3
 - https://github.com/rytilahti/python-eq3bt
 - https://github.com/bimbar/bluepy_devices
