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
 - previous
   - whatever
