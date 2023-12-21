# -*- coding: ascii -*-
# -### main.py
"""
This is main code part.

TODO
add presence sensor based on ble trackers
add other temperature sensors
"""

CONFIG2['__author__'] = "Dr.JJ"
CONFIG2['__version__'] = '54_09' #2023 12 20
CONFIG2['debug'] = 0

# send print to dev null if not debug, verbose
def print2(*args, **kwargs):
    ### substitute print
    fullstr = " ".join(map(str,args))
    if CONFIG2['debug'] == 1:
        print( "= " + fullstr, **kwargs )
    # else print nothing, to dev null
    #else:
    #    pass
    loglenght = 5
    #
    if CONFIG2['debug'] == 10:
        global ERRORLOG
        ERRORLOG = ERRORLOG[0:loglenght]
        if fullstr.strip() == str(ERRORLOG[0].split(":")[1]).strip():
            ERRORLOG[0] = str(int(time.time())) + ': ' + str(fullstr)
        else:
            ERRORLOG.insert( 0, str(int(time.time())) + ': ' + str(fullstr) )
    return

# ### define global variables
VGLOB = {}
#
### v52_40 works best with micropython 1.19 and 1.20
# version details: ascii, ram clean, shorter delays, stability, fix ble-wifi-mqtt
#
VGLOB['status'] = 8  # 8=disconnected
#VGLOB['timescan'] = time.time()
VGLOB['timeup'] = time.time()
VGLOB['timelast'] = time.time()
VGLOB['timework'] = time.time()
#VGLOB['timecheck'] = time.time()
VGLOB['timentp'] = 0
VGLOB['timedisc'] = 0
VGLOB['flood'] = 0
ERRORLOG = [str(int(time.time())) + ": BOOT"]
##

# this does not change much if 2 or 3, but it gives more time to connect
VGLOB['delaywork'] = 2.5 # in seconds, delay for switching to next device
# it is possible to make query more often, but good RSSI is important for fast responses
##
VGLOB['delayquery'] = 55 # in seconds, delay between automated queries, for thermostates and thermometers
##
VGLOB['delaycheck'] = 60 # in seconds, check for scan, connections - ble, mqtt and wifi

# -#### global variables
VSCAN_LIST = {}
VWORK_LIST = {}
VMQTT_SUB_LIST = []
VMQTT_SUB_LIST.append( CONFIG2['mqtt_eq3_in'] )

try:
    # load white list
    fff = open('wl.txt', 'r')
    vwork_temp = str( fff.read() )
    vwork_temp = eval( vwork_temp )
    for jjj, val in vwork_temp.items():
        VWORK_LIST[jjj] = [val[0], time.time() + 30, None, 8, [], None]
        #mac = str( jjj[9:17].replace(":", "") )
        mac = str(jjj.replace(":", "")[6:12])
        VMQTT_SUB_LIST.append(f'{CONFIG2['mqtt_eq3']}{mac}/radin/mode')
        VMQTT_SUB_LIST.append(f'{CONFIG2['mqtt_eq3']}{mac}/radin/temp')
    fff.close()
    # load saved work list
    fff = open('temp.txt', 'r')
    vwork_temp = str( fff.read() )
    if len( vwork_temp ) > 10:
        vwork_temp = eval( vwork_temp )
        for jjj, val in vwork_temp.items():
            VWORK_LIST[jjj][4] = val[4]
    fff.close()
    ## cleanup temp.txt
    fff = open('temp.txt', 'w')
    fff.close()
    #
    del vwork_temp, jjj, fff, val, mac
    print2("BOOT config loaded")
    #gc.collect()
except Exception as e:
    print2('BOOT load fff failed, setting default, this is ok ', e)
    # if the above fails for whatever reason, start with clean white list
    VWORK_LIST['00:00:00:00:00:00'] = [None, time.time() + 30, None, 8, [], None]
    print2("BOOT empty config created")

#-####
#-####
#-#### import and extra functions

# this is not needed in boot
# moved from boot v52_51
import uasyncio as asyncio
import _thread
# separated some functions v53_01
from main2 import fdecode_addr, fcode_addr, ffind_handle, ffind_status, fdisc, fstopscan, fdisconnect, freset

#-####
#-####
# -#### handy functions

def fnow(nowtime: int = 0, ttt: str = "s", time=time) -> str:
    # typing time.time in default value does not work
    if nowtime == 0:
        nowtime = time.time()
    #
    localtime = time.gmtime(int(nowtime) + 3600)  # +1H
    # return(cet)
    if ttt == "m":
        return "{0:04d}-{1:02d}-{2:02d}".format(*localtime) + " {3:02d}:{4:02d}".format(*localtime)
    if ttt == "h":
        return "{0:04d}-{1:02d}-{2:02d}".format(*localtime) + " {3:02d}".format(*localtime)
    if ttt == "d":
        return "{0:04d}-{1:02d}-{2:02d}".format(*localtime)
    else:
        return "{0:04d}-{1:02d}-{2:02d}".format(*localtime) + " {3:02d}:{4:02d}:{5:02d}".format(*localtime)

### start scanning, was 15 sec, is 10, now 20
def fscan(duration: int = 0) -> None:
    gc.collect()
    #global VGLOB # v53_18 not needed
    global VWORK_LIST
    print2('scan start')
    #VGLOB['timescan'] = time.time()
    VWORK_LIST['00:00:00:00:00:00'][1] = time.time()
    if len( VWORK_LIST['00:00:00:00:00:00'][4] ) > 0:
        # usually started from list, but in case of the first or manual scan catch error
        VWORK_LIST['00:00:00:00:00:00'][4].pop(0)
    ###
    try:
        #fpostpone(5) #maybe not necessary 50_11
        if int(duration) == 0:
            # infinite scan
            ble.gap_scan(0, 100000, 30000, 1)
        elif int(duration) == -1:
            # scan stop
            ble.gap_scan(0)
        elif int(duration) > 25:
            ble.gap_scan(int(duration) * 1000, 100000, 30000, 1)
        else:
            ble.gap_scan(int(duration) * 1000, 80000, 40000, 1)
    except Exception as e:
        print2('scan already running ', e)
        return
    ### v52_07 this part moved after scan test
    ### delay other devices, for the a nice scan
    ### ERRORs, but solved with time.time
    for ffaddr in list(VWORK_LIST):
        ### v52_02 update only times which are due, do not set back the timer
        if ffaddr != '00:00:00:00:00:00' and VWORK_LIST[ffaddr][1] < time.time():
            ### postpone all work, but not set back time
            ### v52_10 was 10, but changed to 5 as scan is startet almost in every idle moment
            #pass
            VWORK_LIST[ffaddr][1] = time.time() + 5
    ###
    gc.collect()
    return

### time=time, ntptime=ntptime
def fntp() -> None:
    print2('set time ntp')
    VGLOB['timentp'] = time.time()
    try:
        ntptime.settime()
        ### v52_11 add file timestamp
        fff = open('temp.txt', 'w')
        fff.close()
        #del fff
    except:
        pass
    return

#
def fpostpone(postpone: int = 0) -> None:
    VGLOB['timework'] = time.time() + ( postpone )
    #VGLOB['timescan'] = time.time() + ( postpone )
    VGLOB['timedisc'] = time.time() + ( postpone )
    return

#-####
#-####
# -#### load white lists
####
# definition of VWORK_LIST
# [ last_work, last_check, handle, status, work, work done - for devices sending a lot of ble ]

#-####
#-####
# -#### main ble writer

def fble_write(addr: str, data1: str, data2: str='') -> None:
    #gc.collect()
    # ### main loop
    # ### try connection 20 times, if succesful stop the loop
    print2("fblew work")
    mac_type = str(addr.replace(":", "")[0:6])
    #
    if (mac_type == '4C65A8' or mac_type == 'A4C138') and data1 == 'gettemp':
        data1 = 0x10
        data2 = b'\x01\x00'
    elif mac_type == '001A22' and data1 == 'settemp' and (str(data2).split('.')[0]).isdigit():
        data1 = 0x0411
        ### ver 51_29, set max temp to 30.0 as it may be ON setting 
        if float(data2) > 30.0:
            data2 = 30.0
        ### ver 51_29, set min temp to 4.5 as it switches the EQ3 into OFF setting, recommended by wieluk-github
        if float(data2) < 4.5:
            data2 = 4.5
        data2 = '\x41' + chr(int(round(2 * float(data2))))
    elif mac_type == '001A22' and data1 == 'manual':
        data1 = 0x0411
        data2 = '\x40\x40'
    # ### if no issue with above
    # ### and variables cleaned, try to write
    try:
        fhandle = VWORK_LIST[addr][2]
        #ble.gattc_write(VGLOB['handle'], data1, data2, 1)
        ### BLE WRITE
        ble.gattc_write(fhandle, data1, data2, 1)
        print2('fblew write')
    except Exception as e:
        print2('fblew exc write:', e)
    #
    # ### if loop ended or break then try to disconnect, set status to disconnected
    try:
        # if run as thread, then stop thread
        _thread.exit()
        #pass
    except Exception as e:
        # if this fails, there is no reason to panic, function not in thread
        print2('fblew close thread:', e)
    gc.collect()
    return

#-####
#-####
# -#### main function to handle irqs from mqtt


def fble_irq(event, data) -> None:
    #gc.collect()
    # interrupt triggered by ble
    # usually only if connection is processed
    global VWORK_LIST
    global VSCAN_LIST
    global VGLOB
    # ### get event variable and publish global so other threads react as needed
    VGLOB['status'] = event
    #print2( "f ble irq", event)
    ### v53_31 not needed here
    #try:
    #    wdt.feed()
    #except Exception as e:
    #    print2('fbleirq wdt error, maybe not yet initialised ', e)
    # do not print scans, event 5
    #if event not in [5, 6, 18]:  # 17
    #    print2('fbleirq ', event, ', ', list(data))
    ### SET current time for this run
    ftimenow = time.time()
    # ###
    if event == 5: # _IRQ_SCAN_RESULT
        # ### scan results, and publish gathered addresses in VSCAN_LIST
        addr_type, addr, adv_type, rssi, adv_data = data
        # skip nonrequested responses
        if adv_type == 0:
            return
        # ignore randomised addr
        if addr_type == 1:
            return
        # ignore detections with very low signal, -92 is enough, below -94 strong delays with connection
        ### v51_30, lowering to 91 from 92, as the new antena improves the signal enough
        if int(rssi) < -91:
            return
        # special case for presence sensors with FF:FF addresses
        addrd = str(fdecode_addr(addr))
        mac = str(addrd.replace(":", "")[6:12])
        mac_type = str(addrd.replace(":", "")[0:6])
        #print2('fbleirq ', addrd, addr_type, adv_type, adv_data_dec)
        ###
        ### this has to before rewriting last seen time
        if addrd in VWORK_LIST and addrd in VSCAN_LIST:
            if mac_type[0:4] == 'FFFF' and time.time() > VSCAN_LIST[addrd][3] + 5:
                #print2('fbleirq ', addrd, bytes(adv_data))
                #msg_out = '{"id":"' + mac + '","name":"tracker' + mac + '","location":"'+ str(CONFIG2['mqtt_usr']) +'","timestamp":' + str(time.time()) + '}'
                msg_out = '{"payload":"' + str(CONFIG2['mqtt_usr']) + '", "location":"'+ str(CONFIG2['mqtt_usr']) +'" }'
                topic_out = CONFIG2['mqtt_presence'] + mac + '/radout/status'
                mqtth.publish(topic_out, bytes(msg_out, 'ascii'))
        #        #VSCAN_LIST[addrd][3] = time.time()
        ###
        if mac_type[0:4] == 'FFFF' and adv_type == 0:
            adv_type = 4
            # this has to be like this, to pass through the cleaner later
            adv_data = b'__Tracker'
            #adv_data_dec = 'Tracker'
        ### only full detections, with names, so adv_type == 4
        # v52_33 opt code
        adv_data_dec = bytes(x for x in bytes(adv_data)[2:22].split(b'\xff')[0] if x >= 0x20 and x < 127).decode("ascii").strip()
        if adv_type == 4:
            #print2( str(bytes(adv_data)[2:24].split(b'\xff')[0] ) )
            VSCAN_LIST[addrd] = [bytes(addr), rssi, adv_data_dec, time.time()]
        ### here actions for addresses in the list
        #if addr_decode[0:8] == '4C:65:A8' or addr_decode == 'A4:C1:38':
        # clean after each new result
    elif event == 6:  # _IRQ_SCAN_DONE
        #vwebpage = fwebpage()
        # ### scan done and cleanup, reseting variables as needed
        # 31 added
        VGLOB['status'] = 8
        #VGLOB['result'] = 0
        # new
        gc.collect()
        print2('fbleirq scan done')
    elif event == 7:  # _IRQ_PERIPHERAL_CONNECT
        # ### connected 7
        handle, addr_type, addr = data
        addrd = fdecode_addr(addr)
        #del data
        #del addr_type
        #del addr
        #print2( addrd )
        # do not change the time with connect, but time changes only if irq successful
        #VWORK_LIST[ addrd ][1] = time.time()
        VWORK_LIST[addrd][1] = time.time()
        VWORK_LIST[addrd][2] = handle
        VWORK_LIST[addrd][3] = event
        print2('fbleirq connected')
    elif event == 8:  # _IRQ_PERIPHERAL_DISCONNECT
        # ### disconnected 8, do actions
        gc.collect()
        handle, addr_type, addr = data
        addrd = fdecode_addr(addr)
        #del data
        #del handle
        #del addr_type
        #del addr
        ### v52_05 do not set time here
        #VWORK_LIST[addrd][1] = time.time()
        VWORK_LIST[addrd][2] = None  # this is handle
        VWORK_LIST[addrd][3] = event
        ### v52_14 save the temp value, not a good idea
        ### v52_28 -check
        #print2( str( eval( VWORK_LIST[addrd][5] )['temp'] ) )
        ### v53_11 - added delay for worker and OFF info
        try:
            #print2( str( eval( VWORK_LIST[addrd][5] )['temp'] ) )
            if str( eval( VWORK_LIST[addrd][5] )['temp'] ) == '4.5':
                #print2( 'delaying check while thermostat is OFF' )
                VWORK_LIST[addrd][1] = time.time() + ( 2 * VGLOB['delayquery'] )
                VWORK_LIST[addrd][5] = 'OFF'
            else:
                VWORK_LIST[addrd][5] = None
        except:
            VWORK_LIST[addrd][5] = None #
            pass
        #VWORK_LIST[addrd][1] = time.time()
        #VWORK_LIST[addrd][5] = None
        # written, so remove from work list
        #VGLOB['addr'] = ''
        VGLOB['timelast'] = time.time()
        #VGLOB['work'] = ''
        #gc.collect()
    elif event == 17:  # 17 _IRQ_GATTC_WRITE_DONE
        # ### write to device
        handle, value_handle, status = data
        addrd = ffind_handle(VWORK_LIST, handle)
        #del data
        #del handle
        #del value_handle
        #del status
        # update work times, but do not remove work list (until response)
        ### v52_05 do not set time here
        #VWORK_LIST[addrd][1] = time.time()
        VWORK_LIST[addrd][3] = event
        ###
        #VGLOB['handle'] = handle
        #VGLOB['result'] = 4
    elif event == 18:  # _IRQ_GATTC_NOTIFY
        # ### getting ble notification irq
        handle, value_handle, notify_data = data
        addrd = ffind_handle(VWORK_LIST, handle)
        #
        #del data
        #del handle
        #del value_handle
        #
        VWORK_LIST[addrd][1] = time.time()
        VWORK_LIST[addrd][3] = event
        # written, so remove from work list
        #VWORK_LIST[addrd][4] = None
        if len( VWORK_LIST[addrd][4] ) > 0:
            VWORK_LIST[addrd][4].pop(0) # pop first value from the list, if written correctly
        #VWORK_LIST[ addrd ][5] = notify_data
        ###
        msg_out = None
        ###
        ###
        #VGLOB['data'] = notify_data
        #VGLOB['addr'] = addrd
        #mac = str(addrd[9:17].replace(":", ""))
        mac = str(addrd.replace(":", "")[6:12])
        mac_type = str(addrd.replace(":", "")[0:6])
        ###
        # new
        #type( VWORK_LIST[fworkout][5] ) == int:
        #if (mac_type == '4C65A8' or mac_type == 'A4C138') and VWORK_LIST[addrd][5] == None:
        ### v53_23 added type, as last value can be a number
        if (mac_type == '4C65A8' or mac_type == 'A4C138') and type( VWORK_LIST[addrd][5] ) is int:
            # ### only if result 3 = if notify succesful, then publish
            # ### create mqtt
            datas = str(bytes(notify_data), 'ascii').strip('\x00').strip().replace(' ', '=').split('=')
            msg_out = '{"trv":"' + addrd + '","temp":"' + str(datas[1]) + '","hum":"' + str(datas[3]) + '"}'
            #topic_out = CONFIG2['mqtt_temp_out']
            #topic_out = 'esp/sensor/sensor' + str(addrd[9:17].replace(":", "")) + '/state'
            topic_out = CONFIG2['mqtt_thermo'] + mac + '/radout/status'
            # CONFIG2['mqtt_thermo']
            # send only once
            VWORK_LIST[addrd][5] = 1
        ###
        elif mac_type == '001A22':
            # ### create mqtt
            datas = list(bytearray(notify_data))
            # PRINT THIS FOR BLE DEBUG
            batt_out = 100
            if int(datas[2]) > 70:
                batt_out = 0
            msg_out = '{"trv":"' + addrd + '","temp":"' + str(float(datas[5]) / 2) + '","valve":"' + str(int(datas[3])) + '","battery":"' + str(batt_out) + '","mode":"manual","mode2":"heat"}'
            #topic_out = CONFIG2['mqtt_eq3_out']
            topic_out = CONFIG2['mqtt_eq3'] + mac + '/radout/status'
            #mqtth.publish(CONFIG2['mqtt_eq3_out'], bytes(msg_out, 'ascii'))
        # ### if connection or writing not succesful, then re-add
        ###
        ###
        if msg_out != None:
            #print2('=== msg ===', msg_out)
            mqtth.publish(topic_out, bytes(msg_out, 'ascii'))
            #=time.sleep(0.1)
            #vwork_status[VGLOB['addr']] = msg_out
            VWORK_LIST[addrd][5] = msg_out
            # recache page only if something changed/sent
        # go to status 7 if still work to do # 50_20
        if len( VWORK_LIST[addrd][4] ) > 0:
            VWORK_LIST[addrd][3] = 7
            print2('fbleirq writing-notify success, but more work')
        else:
            print2('fbleirq writing-notify success, disconnecting')
            fdisconnect(ble, value_handle) # was ble.gap_disconnect
        ###
        gc.collect()
        # check if here the value changes to 8
        # as connection cleanup is missing
    else:
        # catch some other ble connection values
        print2('fbleirq unknown ble status')
        #gc.collect()
    ###
    ###
    # it would be nice to, not collect here, not to overload irq
    # still it might make sense
    #gc.collect()
    return

#-####
#-####
#-####

def fmqtt_irq(topic, msg, aaa=False, bbb=False) -> None:
    #gc.collect()
    # ### if the check msg is started, then this function is triggered
    print2("fmqttirq trigger")
    # stop scan if any
    fstopscan(ble)
    #
    global VWORK_LIST
    if type(msg) is bytes:
        msg = msg.decode()
    if type(topic) is bytes:
        topic = str(topic.decode())
    # ### split address and command
    ###
    ###
    worka = str(msg).strip().split(' ', 1)
    #del msg
    if len(worka) == 1:
        worka.append(worka[0])
        topica = topic.replace(CONFIG2['mqtt_eq3'], "").split("/", 1)[0]
        # v52_33 opt code
        worka[0] = "00:1A:22:" + ":".join(topica[i:i + 2] for i in range(0, len(topica), 2))
    print2('fmqttirq - ', str(topic), str(worka))
    ###
    ###
    # 31 add
    # -### new approach
    if topic in (CONFIG2['mqtt_eq3'] + str(mmm).replace(":", "")[6:12] + "/radin/temp" for mmm in VWORK_LIST):
        #VWORK_LIST[worka[0]][4] = "settemp " + worka[1]
        workfin = "settemp " + worka[1]
        if workfin not in VWORK_LIST[worka[0]][4]: # do not double the work
            VWORK_LIST[worka[0]][4].append( "settemp " + worka[1] ) # append instead of setting the value
            print2('fmqttirq work added temp')
    elif topic in (CONFIG2['mqtt_eq3'] + str(mmm).replace(":", "")[6:12] + "/radin/mode" for mmm in VWORK_LIST):
        #VWORK_LIST[worka[0]][4] = worka[1]
        print2('fmqttirq work added mode')
    elif worka[0] not in list(VWORK_LIST):
        # if not the above, and the mac not in the list, then drop
        print2('fmqttirq not on list')
    elif len(worka[0]) == 17 and len(worka[1]) > 5 and len(worka[1]) < 14:
        ### part from previous approach, do not add manual, if some other command exists
        workfin = worka[1]
        if workfin not in VWORK_LIST[worka[0]][4]: # do not double the work
            VWORK_LIST[worka[0]][4].append( worka[1] ) #list
            print2('fmqttirq work added global')
    else:
        print2('fmqttirq irq bad message')
    # time.sleep(1)
    ###
    ### move back the clock so that this work will be done faster
    VWORK_LIST[worka[0]][1] -= 60
    #except Exception as e:
    #    print2('-- fmqttirq work prio fail, paralel work')
    # ### if len 1, then scan and reset allowed
    # ### scan, adds scan to worklist, reset - resets immediately
    if len(worka) == 1:
        if worka[0] == 'scan':
            # start scan
            fscan(0)
        elif worka[0] == 'reset':
            # reset
            # machine.reset()
            freset(time, machine, VWORK_LIST)
    # ### if above not true and address not in the list, then skip
    gc.collect()
    # _thread.exit()
    return

#-####
#-####
#-####

def fworker(var=None) -> None:
    ###
    #print2('worker started')
    try:
        wdt.feed()
    except Exception as e:
        print2('fworker wdt error, maybe not initialised ', e)
    ###
    gc.collect()
    global VWORK_LIST
    #global VGLOB
    # was 20, but now it is the count of the devices to test
    #errordelay = int( len(VWORK_LIST) * VGLOB['delaywork'] )
    errordelay = 20 # it has to be slightly longer to allow scanning
    VGLOB['flood'] = 0
    #global VSCAN_LIST
    ###
    try:
        ### check messages
        ### skip check if working v53_31, to avoid overload
        # but do not stop worker function, as work needs to be done
        # was not in [7, 17, 18, 77]
        if VGLOB['status'] in [5, 8]:
            mqtth.check_msg()
    except Exception as e:
        print2('fworker mqtt check error ', e)
        #time.sleep(0.5)
        #fmqtt_recover() ### do not add this here, it should be fixed automatically
        return ### ADDED
    ### [int(aaa[2] or 0) for aaa in VWORK_LIST.values()]
    #if max(int(aaa[2] or 0) for aaa in VWORK_LIST.values()) > 3:
    if len( [aaa[5] for aaa in VWORK_LIST.values() if not 'None'] ) > 1:
        ### check how many ble connections open, stop if more than 3
        print2('fworker max simultaneous connections')
        return
    ### SET current time for this run
    ftimenow = time.time()
    ###
    fworkout = ''
    ###
    ### find if some device is working/connected
    # to continue work
    if fworkout == '':
        fworkout = ffind_status(VWORK_LIST, 7)
    ###
    ### v53_24 moved this to the end, to allow paralel connections
    ### find if some device finished work, and needs to be cleaned
    if fworkout == '':
        fworkout = ffind_status(VWORK_LIST, 18)
    ###
    ### get the oldest device with work
    # start new work only if no work is being done
    if fworkout == '' and VGLOB['status'] in [5, 8]:
        try:
            # shorter and cleaner
            ### v52_02 seleting only due work
            ### v52_08 bug fix, bad comparision
            #fworkout = min( [ iii for iii in VWORK_LIST.items() if ( len(iii[1][4])>0 and iii[0]!='00:00:00:00:00:00' and iii[1][1]<ftimenow ) ], key=lambda jjj: jjj[1][1] )[0]
            ### v53_24
            fworkout = min( [ iii for iii in VWORK_LIST.items() if ( len(iii[1][4])>0 and iii[0]!='00:00:00:00:00:00' and iii[1][1]<ftimenow and iii[1][3] == 8 ) ], key=lambda jjj: jjj[1][1] )[0]
        except:
            fworkout = ''
    ###
    ### if no device with work, then just recheck the devices
    ### recheck is good for disconnect old connections
    if fworkout == '':
        try:
            # shorter and cleaner
            fworkout = min( VWORK_LIST.items(), key=lambda kkk: kkk[1][1] )[0]
            #fworkout = fworkout[0]
        except:
            fworkout = ''
    ###    
    ### print selected device
    #print2('worker ', fworkout, ftimediff)
    ###
    ### if no work, and not scanning then scan
    #if VGLOB['status'] == 8 and sum( ( len( aaa[4] ) for aaa in VWORK_LIST.values() ) ) == 0: # v52_33 code opt
    ### v52_33 code opt, v53_11 added time check
    # fworkout == '' and
    if VGLOB['status'] == 8 and sum( ( len( aaa[4] ) for aaa in VWORK_LIST.values() if aaa[1] < ftimenow ) ) == 0:
        #VWORK_LIST['00:00:00:00:00:00'][4].append( 'scanlong' )
        ### v52_09 just start scan, do not add anything to the list
        fscan(0)
        ### v52_43 return here, not to do any more tests
        return
    ###
    ###
    # 4 is worklist, 2 is handle
    #####
    ##### v53_21
    ##### this step assumes that one device is already selected !!!
    #####
    #if VWORK_LIST[fworkout][4] == None and VWORK_LIST[fworkout][3] != 7: 
    if VWORK_LIST[fworkout][4] == [] and VWORK_LIST[fworkout][3] not in [7, 77]: # so status is 8, 17 or 18
        ### chkeck if there is work, and if not connected
        if VWORK_LIST[fworkout][2] != None:
            ### if handle exists, but no work, then disconnect, or if connection count eq 3
            try:
                #ble.gap_disconnect(VWORK_LIST[fworkout][2])
                fdisconnect(ble, VWORK_LIST[fworkout][2])
            except Exception as e:
                print2('fworker disconn warn 1 ', e)
                VWORK_LIST[fworkout][2] = None
                VWORK_LIST[fworkout][3] = 8
                VWORK_LIST[fworkout][5] = None
        # update time, for checking
        VWORK_LIST[fworkout][1] = ftimenow
        return
    ###
    ### IMPORTANT everything below assumes there is work to do
    ### print info if some work to be done
    #print2('worker ', fworkout, ftimediff)
    print2('fworker ', fworkout)
    ###
    # change 39
    # there is work, but not being done, then delay this work, and reset timers
    ###
    ### retries
    ### ISSUE
    # v53_23 changed from == to is
    if type( VWORK_LIST[fworkout][5] ) is int:
        ### v52_17 - changed to 4 rounds, to give more time, was 3
        if int( VWORK_LIST[fworkout][5] or 0 ) > 4:
            ### update the check and conn timer
            #VWORK_LIST[fworkout][0] = ftimenow
            print2('fworker tried a few times, delaying')
            # this happens also too often, not logging
            ### v51_25 adding 2 minutes
            ### v52_17 shortening to 10 sec, as delay time is added elsewhere
            ### v52_42 add more, as there were 5 retries
            try:
                #ble.gap_disconnect(VWORK_LIST[fworkout][2])
                #ble.gap_disconnect(0)
                #ble.gap_disconnect(1)
                print2('fworker connect cleanup pending ', fworkout)
                fdisconnect(ble, 0)
                fdisconnect(ble, 1)
                VWORK_LIST[fworkout][1] = ftimenow + errordelay
                VWORK_LIST[fworkout][3] = 8
                VWORK_LIST[fworkout][5] = None
            except:
                print2('fworker connect cleanup failed ', fworkout)
                pass
            if len(VWORK_LIST[fworkout][4]) > 4: ### v51_25 was 10 is 4, how many tasks are in the list
                ### too much work, removing
                VWORK_LIST[fworkout][4].pop(0)
            #gc.collect()
            return
            ### no return in main if, as there might be some work to do
    ###
    ### if the above is fine, just move forward
    ###
    if VWORK_LIST[fworkout][3] not in [7, 8, 77]:
        # v53_21 added 77 so that waiting connection will not be cleaned up
        print2('fworker maybe working')
        ### v52_02 clean up in case of stuck device
        gc.collect()
        # TODO
        # if maybe working for more than 10 sec, then disconnect
        # it waits until next round
#        if ftimenow - VWORK_LIST[fworkout][1] > 10:
        if ftimenow - VWORK_LIST[fworkout][1] > ( VGLOB['delaywork'] * len(VWORK_LIST) ) + 5:
            try:
                #ble.gap_disconnect(VWORK_LIST[fworkout][2])
                fdisconnect(ble, VWORK_LIST[fworkout][2])
            except Exception as e:
                print2('fworker disconn warn 3 ', e)
                #VWORK_LIST[fworkout][1] = ftimenow + 120 ### v51_24 added 2 minutes wait
                VWORK_LIST[fworkout][2] = None
                VWORK_LIST[fworkout][3] = 8 # v53_23
            ### v52_02 - delaying anyway
            ### v51_24 added 2 minutes wait, v52_04 - 3 minutes, v52_10 changed to 1 min, v52_17 delay changed to 20 sec
            VWORK_LIST[fworkout][1] = ftimenow + errordelay
            print2("fworker connection too long")
        # return
    ###
    # v53_17 added new 
    elif VWORK_LIST[fworkout][3] == 77:
        #
        if type( VWORK_LIST[fworkout][5] ) is str: # from == to is
            VWORK_LIST[fworkout][5] = None
        # longer waiting times
        # do not update time here, as the connection may fail
        VWORK_LIST[fworkout][5] = int(VWORK_LIST[fworkout][5] or 0) + 1
        print2("fworker waiting for connection", VWORK_LIST[fworkout][5] )
    #
    # and VGLOB['status'] in [5, 8] 
    elif VWORK_LIST[fworkout][3] == 8 and ftimenow > VWORK_LIST[fworkout][1]: ### v51_25 added time check
        ### finally, all above is fine, and work is to be done, so connect first
        print2("fworker connecting")
        ### v52_15 cleanup the value, as the detection is postponed already
        if type( VWORK_LIST[fworkout][5] ) is str: # from == to is
            VWORK_LIST[fworkout][5] = None
        # longer waiting times
        # do not update time here, as the connection may fail
        #VWORK_LIST[fworkout][5] = int(VWORK_LIST[fworkout][5] or 0) + 1 # v53_21
        VWORK_LIST[fworkout][3] = 77 # v53_14 added status change !!! to avoid reconnecting
        VGLOB['status'] = 77
        try:
            # increased connection time
            #ble.gap_connect( 0, fcode_addr(fworkout), 10000 )
            ### GAP CONNECT           
            VWORK_LIST[fworkout][5] = 1 # v53_21
            #ble.gap_connect( 0, fcode_addr(fworkout), int( 3 * VGLOB['delaywork'] * 1000 ) )
            ble.gap_connect( 0, fcode_addr(fworkout), int( 4 * VGLOB['delaywork'] * 1000 ) ) # v53_16 longer time 4*
        ## v52_39 defined error exceptions added
        ## v52_40 improved error detection
        # other error [Errno 19] ENODEV
        except Exception as e:
            print2('fworker conn warn ', e, fworkout)
            #print2(e.__class__.__name__)
            if str(e).split("] ",1)[1] in ('EIO'):
                try:
                    #ble.gap_disconnect(0) # v53_21 changed from 0, to an actual value
                    #ble.gap_disconnect(VWORK_LIST[fworkout][2])
                    #ble.gap_disconnect(1)
                    fdisconnect(ble, 0)
                    fdisconnect(ble, 1)
                    VWORK_LIST[fworkout][1] = ftimenow + errordelay
                    VWORK_LIST[fworkout][3] = 8 # v53_15
                    VWORK_LIST[fworkout][5] = None # v53_21
                except:
                    print2('fworker connect cleanup failed ', fworkout)
                    pass
            if str(e).split("] ",1)[1] in ('EALREADY'):
                print2('fworker connect already connected ', fworkout)
            # this appears every time a single connection fails, not necessary to report
            print2("fworker connection timeout")
            fpostpone()
        #
    ###
    ### assuming connected, so work
    elif VWORK_LIST[fworkout][3] in [7, 18]:
        print2("fworker connected, and handle available, send work")
        # stop scan if any
        fstopscan(ble)
        #
        if len( VWORK_LIST[fworkout][4] ) == 0:
            ### this deletes position 5 if working, is it fine ?
            ### clean up [5] only if no work to be done, v53_04
            VWORK_LIST[fworkout][5] = None
            ###
            print2("fworker, connected, but no work, disconnect")
            #ble.gap_disconnect(VWORK_LIST[fworkout][2])
            fdisconnect(ble, VWORK_LIST[fworkout][2])
            ### v52_01 - cleaning
            gc.collect()
            return
        # maybe not update, to do whole work in one run
        # select first from the work list
        worka = str(VWORK_LIST[fworkout][4][0]).strip().split(' ')
        for iii in range(max(0, 2 - len(worka))):
            worka.append('')
        ### 43 no thread
        _thread.start_new_thread(fble_write, (fworkout, worka[0], worka[1]))
        #fble_write(fworkout, worka[0], worka[1])
    ###
    ### some other situation happened
    else:
        #mqtth.check_msg()
        #fscan(0) ### v51_26 added, if nothing happens then scan
        print2('fworker unexpected situation - no work, nothing done')
    gc.collect()
    return

#-####
#-####
# -#### webpage generating function

def fwebpage() -> str:
    html_in = ""
    for addr, val in VWORK_LIST.items():
        html_in += str(addr) + " - " + str(val[4]) + "\n"
    # generate table
    # generate rest of html
    #""" + str(VGLOB) + """
    html = """<!DOCTYPE html>
<html lang="en" xml:lang="en">
<head>
<title>EQ3 controller</title>
<meta content="width=device-width, initial-scale=0.8" name="viewport" />
<meta http-equiv="Cache-Control" content="no-store" />
<meta http-equiv="pragma" content="no-cache" />
</head>
<body>
<h1>EQ3 controller</h1>
By Dr. JJ on ESP32 and micropython.<br/>
<a href="https://github.com/yunnanpl/esp32_python_eq3">GitHub page</a>.
<h2>System</h2>
Last work done on: """ + str(fnow(VGLOB['timelast'])) + """<br/>
Last change: """ + str(fnow()) + """<br/>
Boot: """ + str(fnow(VGLOB['timeup'])) + """<br/>
Location: """ + str(CONFIG2['mqtt_usr']) + """<br/>
IP: """ + str(station.ifconfig()[0]) + """<br/>
Version: """ + str(CONFIG2['__version__']) + """
<h2>Links:</h2>
<a href="/list">List of devices</a><br/>
<a href="/ota">Update OTA</a><br/>
<a href="/info">System info</a><br/>
<a href="/webrepl">Add webrepl</a> - <a href="http://micropython.org/webrepl/#""" + str(station.ifconfig()[0]) + """:8266/">Webrepl console</a> (pass: 1234)<br/>
<br/>
<a href="/mqttauto">Publish MQTT autodiscovery</a><br/>
<a href="/scan">Rescan devices</a><br/>
<a href="/reset">Reset</a>
<h2>List of contacted devices</h2>
<pre>
""" + str(html_in) + """
</pre>
<h2>---</h2>
</body>
</html>"""
    del html_in
    html = html.encode('ascii')
    #html = html.encode('latin-1')
    print2('fweb generating page')
    #
    #gc.collect()
    #
    return( html )

#-####
#-####
# -#### webpage loop function
# -#### was based on socket, but now on async is more responsive and less consuming

async def loop_web(reader, writer) -> None:
    flood = 0
    #
    #if VGLOB['status'] in [17, 18]: # v53_29 if working, skip page to avoid flood
    # detect and avoid flood earlier, v53_06, changed from 20000 to 45000
    if gc.mem_free() < 25000 or VGLOB['flood'] == 1:#
        print2('fweb page flood 1')
        flood = 1
        #return
    #global VGLOB
    VGLOB['flood'] = 1
    # waiting for input
    #recv = await reader.read(64)
    ### timeout here ? # v53_10
    # reader, writer = yield from asyncio.wait_for(fut, timeout=3)
    gc.collect()
    #global ERRORLOG
    try:
        #recvtmp = recv.decode()
        if flood == 0:
            #=await asyncio.sleep(0.1)
            recv = yield from reader.read(64)
            requesttype = recv.decode()[0:3]
            requestfull = recv.decode().split('\r')[0].split(' ')[1].split('?')
            #requestfull = requestfull  # [4:-6]
            #recv2 = await reader.read()
            #print2( recv2.decode() )
        else:
            requestfull = ['/flood']
    except Exception as e:
        # if request invalid or malformed
        print2('fweb page request warn ', e)
        requestfull = ['/']
        # continue
    # ?
    #
    print2('fweb serving page ', requestfull)
    #global VGLOB
    #global VSCAN_LIST
    request = requestfull[0]
    #print2(request, requestfull)
    requestval = ''
    vwebpage = b''
    resp = b''
    #timer2 = time.ticks_ms()
    #gc.collect()
    if len(requestfull) == 2:
        requestval = requestfull[1]
    #
    if request == "/":
        vwebpage = fwebpage()
        # Server-Timing: text;dur=""" + str(time.ticks_ms() - timer2) + """, req;dur=""" + str(timer2 - timer1) + """
        header = """HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: """ + str(len(vwebpage)) + """
Connection: close
"""
        #conn.sendall(header + "\r\n" + vwebpage)
        await writer.awrite(header + "\r\n")
        # gc.collect()
        # INFO
        # continue
    #####
    #####
    elif request == "/flood":
        header = """HTTP/1.1 429 Too Many Requests
Retry-After: 3
Content-Type: text/plain
Content-Length: 27
Connection: close

flood, retry in 1-2 seconds
"""
        await writer.awrite(header + "\r\n")
    #    # gc.collect()
    elif request == "/list":
        # stop scan if any
        fstopscan(ble)
        # collect
        gc.collect()
        #
        vwebpage = '<pre>\n'
        vwebpage += '<form method="post" action="/todo">\n'
        if len(VSCAN_LIST) > 0:
            vwebpage += '<hr />MAC, last seen, rssi, name\n'
            for iii in VSCAN_LIST.items():
                #vwebpage += '<a href="/wlistdo?' + str(iii[0]) + '">add</a> ' + str(iii[0]) + ' ' + \
                #    '{: >{w}}'.format(str(time.time() - iii[1][3]), w=5) + ' ' + str(iii[1][1]) + ' ' + str(iii[1][2]) + '\n'
                vwebpage += '<input type="radio" name="maca" value="' + str(iii[0]) + '">'+ str(iii[0]) + ' ' + '{: >{w}}'.format(str(time.time() - iii[1][3]), w=5) + ' ' + str(iii[1][1]) + ' ' + str(iii[1][2]) + '\n'
            vwebpage += 'Type:\n<input type="radio" name="type" value="none">none\n<input type="radio" name="type" value="climate">climate\n<input type="radio" name="type" value="tracker">tracker\n'
            vwebpage += '<input type="submit" name="work" value="add">\n'
            vwebpage += '</form>\n'
        else:
            vwebpage += '<pre>empty list\n'
        ###
        vwebpage += '\n'
        vwebpage += '<hr />MAC remove white listed\n'
        vwebpage += '<form method="post" action="/todo">\n'
        for kkk in list(VWORK_LIST):
            if kkk == '00:00:00:00:00:00':
                continue
            vwebpage += '<input type="radio" name="macr" value="' + str(kkk) + '">' + str(kkk) + '\n'
        vwebpage += '<input type="submit" name="work" value="del">\n'
        vwebpage += '</form>\n'
        vwebpage += '</pre>\n'
        ###
        header = """HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: """ + str(len(vwebpage)) + """
Connection: close
"""
        #conn.sendall(header + "\r\n" + vwebpage)
        await writer.awrite(header + "\r\n")
        # INFO
        # await writer.awrite(vwebpage)
        # conn.close()
    #####
    ##### do all the work here
    #####
    elif request == "/todo":
        #maca=E1:CF:E3:5A:04:28&type=climate&work=add
        #if requesttype != "POS":
        #    #break
        #    return
        recv2 = yield from reader.read(2000)
        recv3 = recv2.decode().split('\r')[-1].replace('%3A', ':').strip().split('&')
        print2('fweb', recv3)
        recv3w = recv3[-1].split('=')[1]
        recv3m = recv3[0].split('=')[1]
        #vwork['0'] = 'scan'
        header = """HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 39
Connection: close

Work -> """ + str( recv3w ) + """, mac -> """ + str( recv3m ) + """.
"""
        #conn.sendall(header + "\r\n" + vwebpage)
        await writer.awrite(header + "\r\n")
        # addr, time, handle, work, status
        # VSCAN_LIST[str(requestval)][0]
        if recv3w == "del":
            #requestval = str(requestval)[0:17]
            del VWORK_LIST[str(recv3m)]
        elif recv3w == "add":
            VWORK_LIST[str(recv3m)] = [None, time.time(), None, 8, [], None]
        else:
            return
        filewl = open('wl.txt', 'w')
        filewl.write( str(VWORK_LIST) )
        filewl.close()
    #####
    #####
    #####
    elif request == "/deldo":
        header = """HTTP/1.1 302 Found
Content-Length: 0
Location: /info
Connection: close
"""
        # Connection: close
        if requestval != '':
            try:
                os.remove(requestval)
            except Exception as e:
                # try to remove file, if fail no panic
                print2('fweb deldo file does not exist ', e)
                #pass
        # conn.sendall(header)
        await writer.awrite(header + "\r\n")
        # await writer.awrite(vwebpage)
    #####
    #####
    elif request == "/info":
        #
        if machine.reset_cause() == 0:
            reset_cause = "PWRON_RESET"
        elif machine.reset_cause() == 1:
            reset_cause = "HARD_RESET"
        elif machine.reset_cause() == 2:
            reset_cause = "WDT_RESET"
        elif machine.reset_cause() == 3:
            reset_cause = "DEEPSLEEP_RESET"
        elif machine.reset_cause() == 4:
            reset_cause = "SOFT_RESET"
        elif machine.reset_cause() == 5:
            reset_cause = "BROWN_OUT_RESET"
        else:
            reset_cause = "unknown"
        #
        if VGLOB['status'] == 8:
            status = "idle"
        elif VGLOB['status'] == 5:
            status = "scanning"
        elif VGLOB['status'] == 1:
            status = "recovering"
        else:
            status = "working"
        #
        # MQTT addresses IN:\n""" + "\n".join( [ str(aaa) for aaa in VMQTT_SUB_LIST ] ) + """
        vwebpage = """Directory listing on ESP. By writing /deldo?filename, files can be removed (dangerous).
Files with _old are safety copies after OTA, can be safely removed.
To disable webrepl, delete webrepl_cfg.py and reboot device.

Dir: """ + str(os.listdir()) + """

Global variables and settings: """ + str(VGLOB) + """

Current time: """ + str(time.time()) + """

Status: """ + status + """

Error log:\n""" + "\n".join( ( str(aaa) for aaa in ERRORLOG ) ) + """

Details:\n""" +  "\n".join( ( str(aaa) for aaa in VWORK_LIST.items() ) ) + """

Reset cause: """ + str(reset_cause) + """
Micropython version: """ + str(os.uname()) + """
Free RAM: """ + str(gc.mem_free()) + """."""
        # v52_33 above, code opt
        #vwebpage = vwebpage.encode('latin-1')
        vwebpage = vwebpage.encode('ascii')
        #
        header = """HTTP/1.1 200 OK
Content-Type: text/plain
Content-Length: """ + str(len(vwebpage)) + """
Connection: close
"""
        #conn.sendall(header + "\r\n" + vwebpage)
        await writer.awrite(header + "\r\n")
        # INFO
        # await writer.awrite(vwebpage)
        # conn.close()
    #####
    #####
    elif request == "/webrepl":
        #requestval = requestfull.split('\r')[0].split(' ')[1].split('?')[1]
        #vwebpage = str(requestval) + "\n" + str(os.listdir())
        try:
            fff = open('webrepl_cfg.py', 'w')
            await fff.write("PASS = \'1234\'\n")
            fff.close()
        except Exception as e:
            print2('fweb webrepl init issue ', e)
            # try to open file, if fail no panic
            #pass
        header = """HTTP/1.1 302 Found
Content-Length: 0
Location: /reset
Connection: close
"""
        #conn.sendall(header + "\r\n" + vwebpage)
        await writer.awrite(header + "\r\n")
        # await writer.awrite(vwebpage)
        # machine.reset()
    #####
    #####
    elif request == "/scan":
        #vwork['0'] = 'scan'
        header = """HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 15
Connection: close

Scan scheduled.
"""
        #conn.sendall(header + "\r\n" + vwebpage)
        VWORK_LIST['00:00:00:00:00:00'][4].append( 'scan' )
        await writer.awrite(header + "\r\n")
        # await writer.awrite(vwebpage)
    elif request == "/mqttauto":
        # fpostpone()
        fdisc(mqtth, VWORK_LIST, CONFIG2)
        header = """HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 30
Connection: close

MQTT Autodiscovery published.
"""
        #conn.sendall(header + "\r\n" + vwebpage)
        await writer.awrite(header + "\r\n")
        # await writer.awrite(vwebpage)
    #####
    #####
    elif request == "/purge":
        fclean(1)
        header = """HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 77
Connection: close

Old devices removed from the list and if necessary the work status was reset.
"""
        #conn.sendall(header + "\r\n" + vwebpage)
        await writer.awrite(header + "\r\n")
        # await writer.awrite(vwebpage)
    #####
    #####
    elif request == "/ota":
        # postpone job, to speed up ota
        fpostpone()
        # method="post"
        vwebpage = """<pre>Usually upload main.py file. Sometimes boot.py file. Binary files do not work yet.
<br/>
<form action="otado" name="upload" method="post" enctype="multipart/form-data">
<input type="file" name="filename">
<input type="submit">
</form>
</pre>"""
        header = """HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: """ + str(len(vwebpage)) + """
Connection: close
"""
        #conn.sendall(header + "\r\n" + vwebpage)
        await writer.awrite(header + "\r\n")
        # INFO
        # await writer.awrite(vwebpage)
    #####
    #####
    elif request == "/otado":
        # postpone job, to speed up ota
        fpostpone()
        # stop scan if any
        fstopscan(ble)
        #
        vwebpage = ''
        #VGLOB = ''
        #VSCAN_LIST = {}
        #gc.collect()
        # s.setblocking(0)
        ### v52_09 automatic reset after upload
        # Location: /reset
        header = """HTTP/1.1 302 Found
Content-Length: 0
Location: /
Connection: close

"""
        # =
        #ble.active(False)
        #gc.collect()
        #headerin = conn.recv(500).decode()
        headerin = yield from reader.read(500)
        # print2(headerin)
        headerin = headerin.decode()
        boundaryin = headerin.split("boundary=", 2)[1].split('\r\n')[0]
        lenin = int(headerin.split("\r\nContent-Length: ", 2)[1].split('\r\n')[0])
        # dividing into 2000 bytes pieces
        bufflen = round(lenin / float(str(round(lenin / 2500)) + ".5"))
        #lenin = 0
        #print2( "===" )
        begin = 0
        try:
            os.remove('upload')
        except Exception as e:
            # try to upload file, if fail no panic
            print2('fweb otado cleaning fail 1, this is fine', e)
            #pass
        fff = open('upload', 'wb')
        while True:
            #dataaa = conn.recv(bufflen).decode().split('\r\n--' + boundaryin, 2)
            dataaa = yield from reader.read(bufflen)
            dataaa = dataaa.decode().split('\r\n--' + boundaryin, 2)
            splita = len(dataaa)
            #print2( splita )
            #filein += dataaa
            if begin == 0 and splita == 3:
                #print2( "= short" )
                # short
                # conn.sendall(header)
                # conn.close()
                await writer.awrite(header + "\r\n")
                namein = dataaa[1].split(' filename="', 1)[1].split('"\r\n', 1)[0]
                fff.write(dataaa[1].split('\r\n\r\n', 1)[1])
                # done with success
                begin = 3
                break
            if begin == 0 and splita == 2:
                #print2( "= first" )
                # first
                namein = dataaa[1].split(' filename="', 1)[1].split('"\r\n', 1)[0]
                fff.write(dataaa[1].split('\r\n\r\n', 1)[1])
                begin = 1
            elif begin == 1 and splita == 1:
                #print2( "= middle" )
                # middle
                fff.write(dataaa[0])
            elif begin == 1 and splita == 2:
                #print2( "= last" )
                # last
                # conn.sendall(header)
                await writer.awrite(header + "\r\n")
                # conn.close()
                fff.write(dataaa[0])
                # done with success
                begin = 3
                break
        fff.close()
        # now replace new file
        if begin == 3:
            try:
                os.remove(namein + "_old")
            except Exception as e:
                print2('fweb otado cleaning fail 2, this is fine', e)
                #pass
            try:
                os.rename(namein, namein + "_old")
            except Exception as e:
                print2('fweb otado cleaning fail 3, this is fine', e)
            os.rename('upload', namein)
        #print2( "===" )
        #print2( namein )
        #print2( lenin )
        dataaa = ''
        ### v52_10
        ### added wait time, so that header is nicely sent
        await asyncio.sleep(0.3)
        freset(time, machine, VWORK_LIST)
        #ble.active(True)
        #gc.collect()
    #####
    #####
    elif request == "/reset":
        fpostpone()
        header = """HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 34
Connection: close

Do <a href="/resetdo">reset</a> ?
"""
        # Connection: close
        # conn.sendall(header)
        await writer.awrite(header + "\r\n")
        # await writer.awrite(vwebpage)
        # conn.close()
        # time.sleep(2) # no sleep here ;)
    #####
    #####
    elif request == "/resetdo":
        header = """HTTP/1.1 302 Found
Content-Length: 0
Location: /
Connection: close

"""
        # Connection: close
        # conn.sendall(header)
        await writer.awrite(header + "\r\n")
        # await writer.awrite(vwebpage)
        # conn.close()
        # time.sleep(2) # no sleep here ;)
        await asyncio.sleep(0.3) # was 0.3, 0.1 was not good
        #machine.reset()
        freset(time, machine, VWORK_LIST)
        # time.sleep(1)
    #####
    #####
    else:
        # Server-Timing: text;dur=""" + str(time.ticks_ms() - timer2) + """, req;dur=""" + str(timer2 - timer1) + """
        header = """HTTP/1.0 404 Not Found
Content-Type: text/plain
Content-Length: 23
Connection: close

404 No page like this.
"""
        # conn.sendall(header)
        await writer.awrite(header + "\r\n")
        # await writer.awrite(vwebpage)
        # conn.close()
    # END IF
    # conn.close() # close or not ?
    # whatever
    try:
        await writer.awrite(vwebpage)
        #=await asyncio.sleep(0.1)
        await writer.drain()
    except Exception as e:
        print2('fweb page flood 2a', e)
        #vwebpage = b''
        #resp = b'
        return
    # drain and sleep needed for good transfer
    vwebpage = b''
    resp = b''
    # 0.3 is perfect, 0.4 makes delay issues, 0.2 breaks the connections sometimes
    await asyncio.sleep(0.2)
    # waiting until everything is sent, to close
    try:
        await reader.wait_closed()
    except Exception as e:
        print2('fweb page flood 2c', e)
    # await reader.aclose()
    #gc.collect()
    #await asyncio.sleep(0.1)
    #print2("-- f serving page done")
    try:
        # if run as thread, then stop thread
        if not CONFIG2['loop']:
            _thread.exit()
            return
        #pass
    except Exception as e:
        # if this fails, there is no reason to panic, function not in thread
        print2('fweb loop_web close thread:', e)
        # break
    # catch OSError: [Errno 104] ECONNRESET ?
    return

#-####
#-####
#-#### check function, should be async as it causes locks

def fcheck(var=None) -> None:
    ###
    ### check function run for cleaning, usually every 1-5 minutes
    ###
    ### var is needed, as this function is started in timer, which sends some arguments
    ###
    ### check of station/wifi, mqtt, ble, webpage server, ntptime, and watchdog
    # do not stop scanning, but also do not return if scanning 50_11
    # always collect here
    gc.collect()
    # check log
    print2('fcheck start')
    ### not needed here as already in fworker, v53_07
    #try:
    #    wdt.feed()
    #except Exception as e:
    #    print2('- fcheck wdt error, maybe not initialised ', e)
    ###
    ###
    try:
        mqtth.ping()
    except Exception as e:
        print2('fcheck mqtt ping error ', e)
        #fmqtt_recover()
    ###
    global VGLOB
    # do not stop if scanning 50_11
    if VGLOB['status'] == 5:
        print2('fcheck stopping scan')
        # stop scan if any
        fstopscan(ble)
        #gc.collect()
        #return
    ### if all is fine, then get some globals first
    global VSCAN_LIST
    global VWORK_LIST
    ftimenow = time.time()
    ###
    ###
    # if still no work done - enforce reset
    # should be slightly longer than router or mqtt server reboot, just in case
    if ftimenow > ( VGLOB['timelast'] + ( VGLOB['delayquery'] * 6 ) ):
        # 3 rounds no response, resetting
        print2('fcheck reset recover')
        ### here add job saving etc
        freset(time, machine, VWORK_LIST)
        #
    # v52_35 readded the check, if no work is done in a few rounds
    if ble.active() == False: #or ftimenow > ( VGLOB['timelast'] + (3 * VGLOB['delayquery'] ) ):
        #or VGLOB['timescan'] > ( VGLOB['timelast'] + (2 * VGLOB['delayquery'] ) ):
        print2('fcheck ble error')
        #fpostpone(5)
        ble.active(False) ### ADDED
        time.sleep(0.1)   ### ADDED, was 0.5
        ble.active(True)
        #gc.collect()
        return
        # fble_recover()
    #
    if station.isconnected() == False or station.ifconfig()[0] == '0.0.0.0':
        print2('fcheck wifi error')
        #fpostpone(5)
        station.connect()
        #gc.collect()
        return
        # machine.reset()
    ###
    ### this is in ms, most other calculations for time are in seconds
    # v52_45 changed to 3 minutes, from 5
    if time.ticks_ms() - mqtth.last_cpacket > 3 * 60 * 1000:
        print2('fcheck bad mqtt')
        # postpone is in the function recovery already, 50_7
        #fpostpone(5)
        # has to be in thread
        _thread.start_new_thread(fmqtt_recover, ())
        #fmqtt_recover()
        #gc.collect()
        return
    ###
    ### remove addresses older than x minutes, clean up old
    ### v51_30, previously it was 20 minutes, now lowering to 10
    ### v51_31, now lowering to 7 minutes
    #last_contact = 9999
    # this concerns VSCAN_LIST and not VWORK_LIST
    for addr, val in VSCAN_LIST.items():
        if ftimenow - val[3] > 7 * 60:
            VSCAN_LIST.pop(addr)
    ###
    ### check ntp every 12 hours, v52_11 changed from 24h to 12h, with error catching
    if ftimenow - VGLOB['timentp'] > 12 * 60 * 60:
        VGLOB['timentp'] = ftimenow
        fntp()
    ###
    ### check autodiscovery every 1 hours
    if ftimenow - VGLOB['timedisc'] > 1 * 60 * 60:
        VGLOB['timedisc'] = ftimenow
        fdisc(mqtth, VWORK_LIST, CONFIG2)
    ###  
    ### if some minutes from the last contact, then scan
    # INFO: optimisations for scan scheduling make no sense, start every 1 minute
    # here I use the global variable timescan
    # still the VWORK_LIST['00:00:00:00:00:00'][0] system variable last work could be used
    ###
    ### v52_04 - TODO increase delay for OFF
    if ftimenow - VGLOB['timework'] > VGLOB['delayquery']:
        VGLOB['timework'] = ftimenow
        for addr, val in VWORK_LIST.items():
            # check if not connected [2] == None
            # possible to check if no work [4] == None
            #if ftimenow - val[1] > VGLOB['delayquery'] and VGLOB['timework']and val[2] == None and addr.replace(":", "")[0:6] == '001A22':
            if val[2] == None and addr.replace(":", "")[0:6] == '001A22':
                if len( VWORK_LIST[addr][4] ) == 0:
                    VWORK_LIST[addr][4].append( 'manual' )
                #VWORK_LIST['00:00:00:00:00:00'][1] = time.time()
            #if ftimenow - val[1] > VGLOB['delayquery'] and val[2] == None and addr.replace(":", "")[0:6] == '4C65A8':
            if val[2] == None and addr.replace(":", "")[0:6] == '4C65A8':
                if len( VWORK_LIST[addr][4] ) == 0:
                    VWORK_LIST[addr][4].append( 'gettemp' )
            #VWORK_LIST['00:00:00:00:00:00'][1] = time.time()
    ###
    ###
    ### if no work then start long scan
    gc.collect()
    #_thread.exit()
    #VGLOB['status'] = 8
    #print2('-- fcheck done')
    return

#-####
#-####
#-####

def fmqtt_recover(var=None) -> None:
    #gc.collect()
    global VGLOB
    print2('fmqtt recover')
    #fpostpone(5) this is skipped here, but added while calling function
    VGLOB['status'] = 1
    # mqtth.keepalive = 130 # that is that ping fits easily 3 times
    mqtth.keepalive = int(3.5 * VGLOB['delaycheck'])
    #time.sleep(0.5)
    mqtth.connect()
    #time.sleep(0.1) # ???
    mqtth.set_callback(fmqtt_irq)
    #time.sleep(0.5)
    for lll in VMQTT_SUB_LIST:
        mqtth.subscribe(lll)
        #time.sleep(0.1) # ???
    # mqtth.subscribe(CONFIG2['mqtt_eq3_in'])
    VGLOB['status'] = 8
    #gc.collect()
    try:
        # if run as thread, then stop thread
        _thread.exit()
        #pass
    except Exception as e:
        # if this fails, there is no reason to panic, function not in thread
        print2('fmqtt fblew close thread:', e)
    ### v52_01 - cleaning
    gc.collect()
    return

def fstart_server() -> None:
    async_loop = asyncio.get_event_loop()
    vserver = asyncio.start_server(loop_web, "0.0.0.0", 80, 2)
    # loop=async_loop, limit=4096 # v53_10, none of these settings work
    # backlog set to 2, this works
    # limit streamreader - maybe 4096, as dividing OTA into 2500 bytes pieces
    async_loop.create_task(vserver)
    async_loop.run_forever()
    return

################
################ BASE
#gc.collect()
# -#### mqtt
# -#### this is moved from boot, to allow recovery
#_thread.stack_size(1024)
_thread.start_new_thread(fmqtt_recover, ())
# wait for connection at boot
# wait longer, was 2, but warning at boot
time.sleep(0.5) # shortened from 4 in 50_8

#-####
#-####
# -#### connect interrupts
ble.irq(fble_irq)
time.sleep(0.5) # 2 in 50_8

#-####
# -#### threads
#loopwebthread = _thread.start_new_thread(loop_web, ())

#-####
#thread_web = _thread.start_new_thread(fstart_server, ())
_thread.start_new_thread(fstart_server, ())
time.sleep(0.5)

#time.sleep(1)
#-####
fntp()
time.sleep(0.5)

#-#### WDT
# do not move this to boot
# after boot is succesful
# changed from 3 to 2.5, v53_05
# changed from delaycheck (around 60 sec) to delaywork (around 2-3 sec), v53_07
# moved just before workers to avoid too long delays, but scanning does wdt so before scan
#wdt = machine.WDT( timeout = int( VGLOB['delaycheck'] * 3 ) * 1000 )
wdt = machine.WDT( timeout = int( VGLOB['delaywork'] * 4 ) * 1000 )
time.sleep(0.5)

### v52_03 usefull to start anyway in case delays in boot
fscan(0)
time.sleep(0.5)

# -#### timers
# 4-5 seconds is completely fine for work
#
### v51_30, added 0.5, so that it is never 0
timer_work.init( period = int( ( VGLOB['delaywork'] ) * 1000 ), callback=fworker)
# ### clean every x minutes, multiplied by 1000, as this is in ms
#_thread.start_new_thread(fble_write, (fworkout, worka[0], worka[1]))
time.sleep(0.5)
#
timer_check.init( period = int( VGLOB['delaycheck'] * 1000 ), callback=fcheck)

time.sleep(0.5)
fdisc(mqtth, VWORK_LIST, CONFIG2)

### cleanup
gc.collect()

print2("BOOTED")

#-###
