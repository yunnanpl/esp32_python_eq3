#-### secret_cfg.py

#-### variables / configuration

#-###
#-###
#-### there variables are used only during boot, then, removed from memory
config = {}
config['freq'] = 240000000
#config['freq'] = 160000000
#-### pass is convoluted with [ ord(x) for x in list(pass) ]
config['wifi_pass'] = [112, 97, 115, 115]
config['wifi_name'] = 'wifiname'
config['ntp_host'] = 'ntp_server'
#
config2 = {}
config2['mqtt_eq3_in'] = '/hass/climate/climate/radin/trv'
config2['mqtt_eq3_out'] = '/hass/climate/climate/radout/status'
config2['mqtt_mijia_out'] = '/hass/climate/thermo/status'

config2['mqtt_eq3'] = 'esp/climate/'
config2['mqtt_temp'] = 'esp/thermo/'
# source of real temperature, some other mqtt thermometer or something
config2['mqtt_temp_src'] = ''

config2['mqtt_srv'] = 'mqtt_srv'
config2['mqtt_usr'] = 'mqtt_usr'
config2['mqtt_pass'] = 'mqtt_pass'

#-### if keep loop is set to 0, then loops die
#-### if you want to kill loops/threads, set this to 0
#-### good for debugging and responsiver webrepl
config2['loop'] = 1

#-### done here