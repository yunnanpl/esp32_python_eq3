# Features
   + controlling and querying of EQ3 devices
     - temperature can be set and queried
     - modes are not yet available (battery also not)
   + readout of Mijia thermometers
   + communication as MQTT (partial compatibilty to esp32_mqtt_eq3 from softypit)
   + basic webpage interface
     + running on async instead of sockets now
   + added basic OTA !!!
     + files can be uploaded and removed from ESP through the page
     + works for any text file, does not work for binary files yet...
   + removed necessity of webrepl to save memory
     + webrepl can be switched on and off through the webpage
   + improved web/sessions - more responsive
   + improved links (upload and reset requires confirmation)
   + added more clear descriptions
   + precompiled the external libraries to save memory and space (simple2.py)

# Changes
 - aefe81f65f3c2fef65815d7d30bba139bcde0b8d
   - significant code rewrite (cleaning pending)
   - automatic time NTP querying
   - automatic MQTT autodiscovery for Home Assistant
     - for thermostats (climate entity)
     - for thermometers (sensor entity)
   - work list for each device separately
   - use of multiple paralel BLE connections, for speed and stability
   - whitelist for EQ3, thermometers-sensors
   - automatic querying of EQ3 (and thermometers, if available)
   - async webpage for more stability
   - watchdog for rebooting just in case
   - BUG: when the contacted device was not available, then the system stuck in a loop (as it retried the connection all the time)
     - now there are 3 retries in a row, and then it moves to the next work
   - BUG: there was a 1 second slot, in which the old work was done, and new work could be added, and quickly deleted by the previous deletion request
     - this cannot happen now, as there is a work list
   - BUG: whitelisted devices could not be removed from GUI
     - now possible
   - BUG Theoretical: If the connections will be so fast, and amount of the EQ3s larger than 6-7, then all BLE connections will be saturated, and it is not known what will happen
     - now, if 4 simultanuous connections are opened, then ESP32 is waiting for done connections to be closed, before opening new
   - BUG: Thermometer readout timer was reset so often, that the real readout never happened (as it was always "just done")
     - fixed
   - BUG: NTP and Autodiscovery were done every few minutes, as the work timer was not set correctly (NTP every 24 hours, Autodiscovery every 6 hours)
     - fixed
   - ISSUE: worklist could consist of multiple equal commands, which makes no sense
     - now if equal command exists in the list, it is dropped, except this, no other commands are dropped
   - ISSUE: flooding web connections could comsume all the RAM and lead to reboot
     - now it should not happen, as the device will respond "flood" or not respond at all if free RAM amount is critically low, but it will try to stay alive
   - ISSUE: it is more an issue, as scanning could be interrupted by any BLE connection request, and scanning did not start when BLE connection was open
     - this led to an issue, where the scanning was very short, or did not took place for a few minutes in a row
     - now, the scanning reserves 1/2 of the full requested scan time, so in worst case it takes half of time, or in best complete time
   - ISSUE: it was hard to controll the ESP32/EQ3 externally, as the MQTT addresses were not known
     - now in the Info page there is a list of the devices, current work/status and a list of MQTT addresses to control the system externally (not through Home Assistant)
 - previous
   - whatever
