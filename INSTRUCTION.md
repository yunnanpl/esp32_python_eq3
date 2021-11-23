# Installation
No compilation is needed, just flash micropython and upload the files as described below.

 - first download micropython binary from here https://micropython.org/download/
 - very probably you need the common esp32 binary (https://micropython.org/download/esp32/)
 - IMPORTANT: fill out the secret_cfg.py file
 - flash it with your favourite flasher using serial connection, or usb-serial connection (if available)
   - for example with esptool - following the instruction on the micropython download page
 - now, you need to upload the files (4 files) from the code directory
   - It can be done with webrepl or ampy
   - webrepl does not require any special installation, but it need to be activated on micropython (through serial connection)
   - ampy requires that you have python installed, and can be installed with pip

## Usage
 - install, as described above
 - go to "List of devices"
 - add interesting devices to the list of this esp32
 - DONE

Now, the devices will be queried automatically. Furthermore, the MQTT autodiscovery for HomeAssistant will be
published, so that you should see new "climate" entities in the list.
You can control the temperature using the Home Assistant interface.

Furthermore, in the "Info" part in the ESP32 interface, you will see the MQTT addresses
for each EQ3. Just send the number with requested temperature to the "temp" MQTT address manually, and it is done.

Whitelisted supported thermometers will be queried automatically and MQTT autodiscovery will be published too (as sensor).

If MQTT autodiscovery will be not published, you can reboot device, or press "Publish MQTT autodiscovery".

## Updates
Updates can be uploaded OTA (over the air), so the device does not have to be physically connected to the PC for the update.
If the main.py fails, then it can be always updated with webrepl.
The only danger is while updating the boot.py or secret_cfg.py, as if there is an error, the webrepl will not start... then the update has to be done with a cable. Still, I try not to upload not working releases ;D
The OTA is available under the http://mydevice/ota link.

## Shell
It is possible to connect to shell of MicroPython for some extra functionality.
For this, it is reasonable to setup and use WebREPL, to issue commands and upgrade scripts remotely.
http://micropython.org/webrepl/

There are internal functions (not really necessary, as there is a webpage now):
  - it is not really important or interesting how the functions work...