# esp32_python_eq3
Bluetooth bridge between EQ3 thermostat and WLAN network, using ESP32, micropython and mqtt.

# Idea
I used a lot of other solutions, but it seemed to be not stable for me, or hard to extend (for me :)).
In order to use the esp32 for EQ3 and Mijia temperature sensors (or even some BME280-like ones) I needed to get something done on my own.

So I decided to rewrite it in python (micropython) on esp32.

This is the result. It can mimic and substitute the esp32_mqtt_eq3 solution from softypit, as it accepts the same mqtt input and returns similar mqtt json output.

# Other interesting liks
https://github.com/softypit/esp32_mqtt_eq3
