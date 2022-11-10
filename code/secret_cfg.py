# -*- coding: latin-1 -*-
#-### secret_cfg.py

#-### variables / configuration

#-###
#-###
#-### there variables are used only during boot, then, removed from memory
CONFIG = {}
CONFIG['freq'] = 240000000
#CONFIG['freq'] = 160000000
#-### pass is convoluted with [ ord(x) for x in list(pass) ]
CONFIG['wifi_pass'] = [112, 97, 115, 115]
CONFIG['wifi_name'] = 'wifiname'
CONFIG['ntp_host'] = 'ntp_server'
#
CONFIG2 = {}
CONFIG2['mqtt_eq3_in'] = '/hass/climate/climate/radin/trv'
CONFIG2['mqtt_eq3_out'] = '/hass/climate/climate/radout/status'
CONFIG2['mqtt_mijia_out'] = '/hass/climate/thermo/status'

CONFIG2['mqtt_eq3'] = 'esp/climate/'
CONFIG2['mqtt_thermo'] = 'esp/thermo/'
# source of real temperature, some other mqtt thermometer or something
CONFIG2['mqtt_thermo_src'] = ''
CONFIG2['mqtt_presence'] = 'esp/presence/'

CONFIG2['mqtt_srv'] = 'mqtt_srv'
CONFIG2['mqtt_usr'] = 'mqtt_usr'
CONFIG2['mqtt_pass'] = 'mqtt_pass'

#-### if keep loop is set to 0, then loops die
#-### if you want to kill loops/threads, set this to 0
#-### good for debugging and responsiver webrepl
CONFIG2['loop'] = 1

#-### done here