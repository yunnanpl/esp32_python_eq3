#-####
#-####
#-####

def ffind_handle(VWORK_LIST, handle: int) -> str:
    # get addr of the handle
    # cleaner 50_17
    try:
        return [kkk[0] for kkk in VWORK_LIST.items() if kkk[1][2]==handle][0]
    except:
        return '' # needed ?

def ffind_status(VWORK_LIST, status: int = 7) -> str:
    # get addr of the connected state
    # cleaner 50_17
    try:
        return [kkk[0] for kkk in VWORK_LIST.items() if kkk[1][3]==status][0]
    except:
        return '' # needed ?

def fdecode_addr(addr: bytes) -> str:
    # get str addr from hex mac
    result = []
    for iii in addr:
        result.append('{:0>2}'.format(str(hex(iii).split('x')[1])))
    return str((':').join(result)).upper()


def fcode_addr(addr: str) -> bytes:
    # encrypt the str addr into connectable hex mac
    result = []
    for iii in addr.split(":"):
        result.append(int(str(iii), 16))
    return bytes(result)

#### should be cleanly added here

def faddwork() -> None:
    # function for adding work
    # should check where to add the work, and if this or similar work exists
    # if the work makes sense
    # in the future maybe this should be handled by the TRV object...
    pass
    return

# v53_19 moved
def freset(time, machine, VWORK_LIST):
    ### v52_08 reset function wrap
    ### TODO, add some functions like time save, job save, etc.
    #fff1 = open('temp.txt', 'w')
    #fff1.close()
    fff2 = open('temp.txt', 'w')
    fff2.write( str(VWORK_LIST) )
    fff2.close()
    #del fff
    time.sleep(0.2)
    #await fff.write("PASS = \'1234\'\n")
    machine.reset()

# v53_19 moved
def fdisconnect(ble, handle = 0) -> None:
    # disconnect and clean up, with all error catching etc
    try:
        ble.gap_disconnect(handle)
    except:
        # problem...
        return 1
    return

# v53_19 moved
def fstopscan(ble) -> None:
    try:
        ble.gap_scan(None)
        #sleep(0.1) # no sleep as it is used in time critical functions
        return
    except:
        pass
        return


#-####
#-####
#-####

def fdisc(mqtth, VWORK_LIST, CONFIG2) -> None:
    ###
    #print('= send mqtt autodiscovery')
    #gc.collect()
    #fpostpone()
    ### home assistant auto discovery
    ### discovery topic should be retained
    #print("publishing mqtt autodiscovery")
    ###
    ### loop through all trusted devices
    for hhh in VWORK_LIST:
        #time.sleep(0.1) # was 0.5
        #mac = str(hhh[9:17].replace(":", ""))
        mac = str(hhh.replace(":", "")[6:12])
        mac_type = str(hhh.replace(":", "")[0:6])
        ###
        if mac_type == '4C65A8' or mac_type == 'A4C138':
            #html_in += str(vvv) + "\n"
            ###
            #mac = str(hhh[9:17].replace(":", ""))
            ###
            topict = f'homeassistant/sensor/temp_{mac}_temp/config'
            devid = '"device": { "identifiers": [ "temp_' + mac + '_id" ], "name":"temp_' + mac + '_dev", "model":"JJ ESP32 Temp", "sw_version":"' + CONFIG2['__version__'] + '" }'
            devicet = '{"device_class": "temperature", "name": "Mijia ' + mac + ' Temperature", \
"state_topic": "' + CONFIG2["mqtt_thermo"] + mac + '/radout/status", "unit_of_measurement": "°C", "value_template": "{{ value_json.temp }}", \
"unique_id": "temp_' + mac + '_T", ' + devid + ' }'
            mqtth.publish(topict, bytes(devicet, 'ascii'), True)
            ###
            topich = f'homeassistant/sensor/temp_{mac}_hum/config'
            deviceh = '{"device_class": "humidity", "name": "Mijia ' + mac + ' Humidity", \
"state_topic": "' + CONFIG2["mqtt_thermo"] + mac + '/radout/status", "unit_of_measurement": "%", "value_template": "{{ value_json.hum }}", \
"unique_id": "temp_' + mac + '_H", '+ devid +' }'
            mqtth.publish(topich, bytes(deviceh, 'ascii'), True)
        ###
        # /hass/climate/climate3/radin/trv 00:1A:22:0E:C9:45 manual
        # /hass/climate/climate1/radout/status {"trv":"00:1A:22:0E:F6:F5","temp":"19.0","mode":"manual"}
        if mac_type == '001A22':
            ###
            #  "~": "homeassistant/light/kitchen",
            # each eq3 has to have its own mqtt
            topicc = f'homeassistant/climate/clim_{mac}_eq3/config'
            if CONFIG2['mqtt_thermo_src'] != "":
                currtemp = '"curr_temp_t": "' + CONFIG2['mqtt_thermo_src'] + '/radout/status", "curr_temp_tpl": "{{value_json.temp}}", '
            else:
                currtemp = ""
            devid = '"device": { "identifiers": [ "clim_' + mac + '_id" ], "name": "clim_eq3_' + mac + '_dev", "model":"JJ ESP32 Clim EQ3", "sw_version":"' + CONFIG2['__version__'] + '" }'
            ### ver 51_29, min 4.5->OFF, 30.0->ON, recommended by wieluk-github 
            devicec = '{ "name": "clim_eq3_' + mac + '", "unique_id": "clim_' + mac + '_thermostat_id", "modes": [ "heat" ], ' + devid + ', \
"mode_cmd_t": "' + CONFIG2['mqtt_eq3'] + mac + '/radin/mode2", "mode_stat_t": "' + CONFIG2['mqtt_eq3'] + mac + '/radout/status", \
"mode_stat_tpl": "{{value_json.mode2}}", "temp_cmd_t": "' + CONFIG2['mqtt_eq3'] + mac + '/radin/temp", \
"temp_stat_t": "' + CONFIG2['mqtt_eq3'] + mac + '/radout/status", "temp_stat_tpl": "{{value_json.temp}}", \
' + currtemp + ' "min_temp": "4.5", "max_temp": "30.0", "temp_step": "0.5", \
"hold_state_template": "{{value_json.mode}}", "hold_state_topic": "' + CONFIG2['mqtt_eq3'] + mac + '/radout/status", \
"hold_command_topic": "' + CONFIG2['mqtt_eq3'] + mac + '/radin/mode", "hold_modes": [ "auto", "manual", "boost", "away" ] }'
            mqtth.publish(topicc, bytes(devicec, 'ascii'), True)
            ### battery and valve open sensors
            topicc = f'homeassistant/sensor/clim_{mac}_eq3_valve/config'
            devicec = '{ "name": "clim_eq3_' + mac + ' Valve", "unique_id": "clim_' + mac + '_valve_id" , ' + devid + ', \
"state_topic": "' + CONFIG2['mqtt_eq3'] + mac + '/radout/status", "value_template": "{{ value_json.valve }}" }'                     
            mqtth.publish(topicc, bytes(devicec, 'ascii'), True)
            ###
            topicc = f'homeassistant/sensor/clim_{mac}_eq3_battery/config'
            devicec = '{ "name": "clim_eq3_' + mac + ' Battery", "unique_id": "clim_' + mac + '_battery_id", ' + devid + ', "device_class": "battery", \
"state_topic": "' + CONFIG2['mqtt_eq3'] + mac + '/radout/status", "value_template": "{{ value_json.battery }}" }'                     
            mqtth.publish(topicc, bytes(devicec, 'ascii'), True)
            ###    
            #del devicec
            # add True at the end to retain or retain=True
        if mac_type[0:4] == 'FFFF':
            #topicp = f'homeassistant/sensor/presence_{mac}_eq3/config'
            topicp = f'homeassistant/device_tracker/presence_{mac}_eq3/config'
            devid = '"device": { "identifiers": [ "tracker_' + mac + '_id" ], "name": "tracker_' + mac + '_dev", "model":"JJ ESP32 Tracker", "sw_version":"' + CONFIG2['__version__'] + '" }'
            devicep = '{"name": "Tracker ' + mac + '", "state_topic": "' + CONFIG2["mqtt_presence"] + mac + '/radout/status", ' + devid + ', \
"expire_after": "240", "consider_home": "180", "unique_id": "tracker_' + mac + '", "source_type": "bluetooth" }'
            mqtth.publish(topicp, bytes(devicep, 'ascii'), True)
            #
            #del devicep
        ###
        ### here additional devices for publishing can be added
    ### v52_01 - cleaning
    #gc.collect()
    return

#####

