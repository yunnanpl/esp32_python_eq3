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
   
# References

 - mqtt - most robust library chosen
   - https://github.com/fizista/micropython-umqtt.simple2 with https://github.com/fizista/micropython-umqtt.robust2
   - not clear if necessary

# Other interesting liks
https://github.com/softypit/esp32_mqtt_eq3
