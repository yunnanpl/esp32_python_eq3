# -*- coding: utf-8 -*-
"""
This is main code part.

TODO
add quick mqtt response for climate, to make home assistant happy
add presence sensor based on ble trackers
add other temperature sensors
"""

# ### define global variables
VGLOB = {}
VGLOB['status'] = 8  # 8=disconnected
VGLOB['timescan'] = time.time()
VGLOB['timeup'] = time.time()
VGLOB['timelast'] = time.time()
VGLOB['timework'] = time.time()
VGLOB['timecheck'] = time.time()
VGLOB['timentp'] = 0
VGLOB['timedisc'] = 0

# time between 2-5 is fine
VGLOB['delaywork'] = 5 # in seconds
VGLOB['delayquery'] = 120 # in seconds
VGLOB['delaycheck'] = 60 # in seconds

# -#### global variables
VSCAN_LIST = {}
VWORK_LIST = {}
VMQTT_SUB_LIST = []
VMQTT_SUB_LIST.append( CONFIG2['mqtt_eq3_in'] )

try:
    wl = open('wl.txt', 'r')
    vwork_temp = eval(str(wl.read()))
    for jjj, val in vwork_temp.items():
        VWORK_LIST[jjj] = [val[0], time.time() + 60, None, 8, [], None]
        #mac = str( jjj[9:17].replace(":", "") )
        mac = str(jjj.replace(":", "")[6:12])
        VMQTT_SUB_LIST.append(f'{CONFIG2['mqtt_eq3']}{mac}/radin/mode')
        VMQTT_SUB_LIST.append(f'{CONFIG2['mqtt_eq3']}{mac}/radin/temp')
    del vwork_temp
    wl.close()
except Exception as e:
    print('- load wl failed, setting default, this is ok ', e)
    # if the above fails for whatever reason, start with clean white list
    VWORK_LIST['00:00:00:00:00:00'] = ["system", time.time() + 60, None, 8, [], None]

#-####
#-####
#-####


def fnow(nowtime: int = 0, ttt: str = "s"):
    # typing time.time in default value does not work
    if nowtime == 0:
        nowtime = time.time()
    #nowtime = str(time.time()),
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

#-####
#-####
# -#### handy functions

def ffind_handle(handle: int) -> str:
    # get addr of the handle
    #global VWORK_LIST
    for val, iii in VWORK_LIST.items():
        if iii[2] == handle:
            return str(val)

def ffind_status(status: int = 7) -> str:
    # get addr of the connected state
    #global VWORK_LIST
    for val, iii in VWORK_LIST.items():
        if iii[3] == status:
            return str(val)
    # else
    return ''

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

def fscan(duration: int = 15) -> None:
    global VGLOB
    global VWORK_LIST
    print('= scan start')
    VGLOB['timescan'] = time.time()
    VWORK_LIST['00:00:00:00:00:00'][1] = time.time()
    if len( VWORK_LIST['00:00:00:00:00:00'][4] ) > 0:
        # usually started from list, but in case of the first or manual scan catch error
        VWORK_LIST['00:00:00:00:00:00'][4].pop(0)
    ### delay other devices, for the a nice scan
    ### ERRORs, but solved with time.time
    for ffaddr in list(VWORK_LIST):
        #print( ffaddr, VWORK_LIST[ffaddr][1] )
        #VGLOB['timework'] = time.time() + int( duration * (2/3) )
        if ffaddr != '00:00:00:00:00:00':
            VWORK_LIST[ffaddr][1] = time.time() + int( duration * (2/3) )
    ###
    try:
        ble.gap_scan(int(duration) * 1000, 50000, 30000, 1)
    except Exception as e:
        print('= scan already running ', e)
    #VWORK_LIST['00:00:00:00:00:00'][4] = None
    return

def fntp() -> None:
    print('= set time ntp')
    VGLOB['timentp'] = time.time()
    ntptime.settime()
    return

def faddwork() -> None:
    # function for adding work
    # should check where to add the work, and if this or similar work exists
    # if the work makes sense
    pass

def fdisconnect() -> None:
    # disconnect and clean up, with all error catching etc
    pass

#def fprint() -> None:
#    for addr, val in VWORK_LIST:
#        print('== ', str(addr), ' - ', str(val))

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
    # writer triggered in fget_work, and results in ble irqs
    # maybe no global for writing needed
    #global VGLOB
    #global VSCAN_LIST
    #global VWORK_LIST
    #print('- fble_write - ', str(addr), str(data1))
    # ### main loop
    # ### try connection 20 times, if succesful stop the loop
    print("= fblew work")
    mac_type = str(addr.replace(":", "")[0:6])
    #print( str(addr), str(data1), str(data2) )
    #print( str(VGLOB['addr']), str(VGLOB['work']) )
    if (mac_type == '4C65A8' or mac_type == 'A4C138') and data1 == 'gettemp':
        data1 = 0x10
        data2 = b'\x01\x00'
    elif mac_type == '001A22' and data1 == 'settemp' and (str(data2).split('.')[0]).isdigit():
        data1 = 0x0411
        if float(data2) > 29.5:
            data2 = 29.5
        if float(data2) < 5:
            data2 = 5
        data2 = '\x41' + chr(int(round(2 * float(data2))))
    elif mac_type == '001A22' and data1 == 'manual':
        data1 = 0x0411
        data2 = '\x40\x40'
    # ### if no issue with above
    # ### and variables cleaned, try to write
    try:
        fhandle = VWORK_LIST[addr][2]
        #ble.gattc_write(VGLOB['handle'], data1, data2, 1)
        ble.gattc_write(fhandle, data1, data2, 1)
        print('= fblew write')
        # for jjj in range(60):
        #    #print('--- wait for connect')
        #    f VGLOB['status'] != 8:
        #        continue
        #    time.sleep(0.5)
    except Exception as e:
        print('- fblew exc write:', e)
    #
    # ### if loop ended or break then try to disconnect, set status to disconnected
    # 31 add
    # ?
    try:
        # if run as thread, then stop thread
        _thread.exit()
        #pass
    except Exception as e:
        # if this fails, there is no reason to panic, function not in thread
        print('- fblew close thread:', e)
    gc.collect()
    return

#-####
#-####
# -#### main function to handle irqs from mqtt


def fble_irq(event, data) -> None:
    # interrupt triggered by ble
    # usually only if connection is processed
    global VWORK_LIST
    global VSCAN_LIST
    global VGLOB
    #global vwebpage
    #global vwork_status
    # ### get event variable and publish global so other threads react as needed
    VGLOB['status'] = event
    #print( "f ble irq", event)
    try:
        wdt.feed()
    except Exception as e:
        print('- fbleirq wdt error, maybe not yet initialised ', e)
    # do not print scans, event 5
    #if event not in [5, 6, 18]:  # 17
    #    print('- fbleirq ', event, ', ', list(data))
    # ###
    if event == 5:  # _IRQ_SCAN_RESULT
        # ### scan results, and publish gathered addresses in VSCAN_LIST
        addr_type, addr, adv_type, rssi, adv_data = data
        # special case for presence sensors with FF:FF addresses
        addrd = str(fdecode_addr(addr))
        mac = str(addrd.replace(":", "")[6:12])
        mac_type = str(addrd.replace(":", "")[0:6])
        #print('+ fbleirq ', addrd, addr_type, adv_type)
        ###
        ### this has to before rewriting last seen time
        if addrd in VWORK_LIST and addrd in VSCAN_LIST:
            if mac_type[0:4] == 'FFFF' and time.time() > VSCAN_LIST[addrd][3] + 5:
                #print('-- fbleirq ', addrd, bytes(adv_data))
                #msg_out = '{"id":"' + mac + '","name":"tracker' + mac + '","location":"'+ str(CONFIG2['mqtt_usr']) +'","timestamp":' + str(time.time()) + '}'
                #msg_out = '{"id":"' + mac + '","name":"tracker' + mac + '","location":"'+ str(CONFIG2['mqtt_usr']) +'" }'
                msg_out = '{"payload":"' + str(CONFIG2['mqtt_usr']) + '", "location":"'+ str(CONFIG2['mqtt_usr']) +'" }'
                topic_out = CONFIG2['mqtt_presence'] + mac + '/radout/status'
                mqtth.publish(topic_out, bytes(msg_out, 'ascii'))
        #        #VSCAN_LIST[addrd][3] = time.time()
        ###
        if mac_type[0:4] == 'FFFF' and adv_type == 0:
            adv_type = 4
            # this has to be like this, to pass through the cleaner later
            adv_data = b'__Tracker'
        ### only full detections, with names, so adv_type == 4
        if adv_type == 4:
            #print( str(bytes(adv_data)[2:24].split(b'\xff')[0] ) )
            VSCAN_LIST[addrd] = [bytes(addr), rssi, bytes((x for x in bytes(adv_data)[2:22].split(b'\xff')
                                                                 [0] if x >= 0x20 and x < 127)).decode("ascii").strip(), time.time()]
        ### here actions for addresses in the list
        #else:
        #    pass
        # return
        # debug temp
        #if addr_decode[0:8] == '4C:65:A8' or addr_decode == 'A4:C1:38':
        #    pass
        #    print( "-- irq temp ", addr_decode, list( bytearray( adv_data ) ) )
        # clean after each new result
    elif event == 6:  # _IRQ_SCAN_DONE
        #vwebpage = fwebpage()
        # ### scan done and cleanup, reseting variables as needed
        # 31 added
        # time.sleep(1)
        VGLOB['status'] = 8
        #VGLOB['result'] = 0
        # new
        #VWORK_LIST['00:00:00:00:00:00'][4] = []
        print('= fbleirq scan done')
        # gc.collect()
    elif event == 7:  # _IRQ_PERIPHERAL_CONNECT
        # ### connected 7
        handle, addr_type, addr = data
        addrd = fdecode_addr(addr)
        #print( addrd )
        # do not change the time with connect, but only disconnect
        #VWORK_LIST[ addrd ][1] = time.time()
        VWORK_LIST[addrd][1] = time.time()
        VWORK_LIST[addrd][2] = handle
        VWORK_LIST[addrd][3] = event
    elif event == 8:  # _IRQ_PERIPHERAL_DISCONNECT
        # ### disconnected 8, do actions
        handle, addr_type, addr = data
        addrd = fdecode_addr(addr)
        #VGLOB['handle'] = handle
        # DONE
        # update the time of the original address too
        #addrdo = ffind_handle(handle)
        #print( addrd, handle, addrdo )
        #VWORK_LIST[ addrdo ][1] = time.time()
        # TODO
        # if disconnected from handle, with address 00, then the device is out of range
        # try later, so update the timer
        # INFO the above does not work so well ;D
        ###
        # remove the handle
        #VWORK_LIST[addrd][0] = time.time()
        VWORK_LIST[addrd][1] = time.time()
        VWORK_LIST[addrd][2] = None  # this is handle
        VWORK_LIST[addrd][3] = event
        VWORK_LIST[addrd][5] = None
        # written, so remove from work list
        # only in response obtained 18
        #VWORK_LIST[ addrd ][4] = []
        # for mijia
        # 20211109 new
        #VGLOB['addr'] = ''
        VGLOB['timelast'] = time.time()
        #VGLOB['work'] = ''
        # gc.collect()
    elif event == 17:  # 17 _IRQ_GATTC_WRITE_DONE
        # ### write to device
        handle, value_handle, status = data
        addrd = ffind_handle(handle)
        # update work times, but do not remove work list (until response)
        VWORK_LIST[addrd][1] = time.time()
        VWORK_LIST[addrd][3] = event
        ###
        #VGLOB['handle'] = handle
        #VGLOB['result'] = 4
    elif event == 18:  # _IRQ_GATTC_NOTIFY
        # ### getting ble notification irq
        handle, value_handle, notify_data = data
        addrd = ffind_handle(handle)
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
        if (mac_type == '4C65A8' or mac_type == 'A4C138') and VWORK_LIST[addrd][5] == None:
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
            #print( datas )
            # datas 5 is temperature
            # datas 3 is probably valve open value
            # datas for battery ?
            #msg_out = '{"trv":"' + addrd + '","temp":"' + str(float(datas[5]) / 2) + '","mode":"manual","mode2":"heat"}'
            batt_out = "OK"
            if int(datas[2]) > 70:
                batt_out = "LOW"
            msg_out = '{"trv":"' + addrd + '","temp":"' + str(float(datas[5]) / 2) + '","valve":"' + str(int(datas[3])) + '","battery":"' + str(batt_out) + '","mode":"manual","mode2":"heat"}'
            #topic_out = CONFIG2['mqtt_eq3_out']
            topic_out = CONFIG2['mqtt_eq3'] + mac + '/radout/status'
            #mqtth.publish(CONFIG2['mqtt_eq3_out'], bytes(msg_out, 'ascii'))
        # ### if connection or writing not succesful, then re-add
        ###
        ###
        if msg_out != None:
            #print('=== msg ===', msg_out)
            mqtth.publish(topic_out, bytes(msg_out, 'ascii'))
            #vwork_status[VGLOB['addr']] = msg_out
            VWORK_LIST[addrd][5] = msg_out
            # recache page only if something changed/sent
        ###
        #gc.collect()
    else:
        # catch some other ble connection values
        print('- fbleirq unknown ble status')
        #gc.collect()
    ###
    ###
    # it would be nice to, not collect here, not to overload irq
    # still it might make sense
    gc.collect()
    return

#-####
#-####
#-####


def fmqtt_irq(topic, msg, aaa=False, bbb=False) -> None:
    # ### if the check msg is started, then this function is triggered
    # interruption when the message from mqtt arrives
    # this happens only if messages are previously requested
    print("= fmqttirq trigger")
    global VWORK_LIST
    if type(msg) is bytes:
        msg = msg.decode()
    if type(topic) is bytes:
        topic = str(topic.decode())
    # ### split address and command
    ###
    ###
    worka = str(msg).strip().split(' ', 1)
    if len(worka) == 1:
        worka.append(worka[0])
        topica = topic.replace(CONFIG2['mqtt_eq3'], "").split("/", 1)[0]
        worka[0] = "00:1A:22:" + ":".join([topica[i:i + 2] for i in range(0, len(topica), 2)])
    print('= fmqttirq - ', str(topic), str(worka))
    ###
    ###
    # 31 add
    # -### new approach
    if topic in [CONFIG2['mqtt_eq3'] + str(mmm).replace(":", "")[6:12] + "/radin/temp" for mmm in VWORK_LIST]:
        #VWORK_LIST[worka[0]][4] = "settemp " + worka[1]
        workfin = "settemp " + worka[1]
        if workfin not in VWORK_LIST[worka[0]][4]: # do not double the work
            VWORK_LIST[worka[0]][4].append( "settemp " + worka[1] ) # append instead of setting the value
            print('= fmqttirq work added temp')
    elif topic in [CONFIG2['mqtt_eq3'] + str(mmm).replace(":", "")[6:12] + "/radin/mode" for mmm in VWORK_LIST]:
        #VWORK_LIST[worka[0]][4] = worka[1]
        print('= fmqttirq work added mode')
    elif worka[0] not in list(VWORK_LIST):
        # if not the above, and the mac not in the list, then drop
        print('+ fmqttirq not on list')
    elif len(worka[0]) == 17 and len(worka[1]) > 5 and len(worka[1]) < 14:
        ### part from previous approach, do not add manual, if some other command exists
        #if worka[1] == "manual" and len( VWORK_LIST[worka[0]][4] != None:
        #    # do not overwrite if only temp check
        #    pass
        #else:
        #VWORK_LIST[worka[0]][4] = worka[1]
        ### adding manual, to the worklist normally
        workfin = worka[1]
        if workfin not in VWORK_LIST[worka[0]][4]: # do not double the work
            VWORK_LIST[worka[0]][4].append( worka[1] ) #list
            print('= fmqttirq work added global')
    else:
        print('- fmqttirq irqbad message')
    # time.sleep(1)
    ###
    ### move back the clock so that this work will be done faster
    VWORK_LIST[worka[0]][1] -= 60
    #except Exception as e:
    #    print('-- fmqttirq work prio fail, paralel work')
    # ### if len 1, then scan and reset allowed
    # ### scan, adds scan to worklist, reset - resets immediately
    if len(worka) == 1:
        if worka[0] == 'scan':
            # start scan
            fscan(30)
        elif worka[0] == 'reset':
            # reset
            machine.reset()
    # ### if above not true and address not in the list, then skip
    # ### whitelist could be added
    # it would be nice to, not collect here, not to overload irq
    # still it might make sense
    gc.collect()
    # _thread.exit()
    return

#-####
#-####
#-####


def fworker(var=None) -> None:
    ###
    #print('. worker started')
    try:
        wdt.feed()
    except Exception as e:
        print('- fcheck wdt error, maybe not initialised ', e)
    ###
    global VWORK_LIST
    global VGLOB
    #global VSCAN_LIST
    ###
    try:
        ### check messages
        mqtth.check_msg()
    except Exception as e:
        print('- worker mqtt check error ', e)
    ###
    if max(int(aaa[2] or 0) for aaa in VWORK_LIST.values()) > 3:
        ### check how many ble connections open, stop if more than 3
        print('+ max simultaneous connections')
        return
    ftimenow = time.time()
    ###
    ### find if some device is working/connected
    fworkout = ffind_status(7)
    ###
    ### if noselect which device was checked longest time ago
    ftimediff = 0
    if fworkout == '':
        for addr, val in VWORK_LIST.items():
            if ftimediff < ftimenow - val[1]:
                ftimediff = ftimenow - val[1]
                fworkout = addr
                #print(ftimediff, fworkout)
    ###
    ### print selected device
    #print('- worker ', fworkout, ftimediff)
    ###
    ### if just rebooted, then change None with 8
    ### 43 remove
    #try:
    #    if VWORK_LIST[fworkout][3] == None:
    #        VWORK_LIST[fworkout][3] = 8
    #except Exception as e:
    #    print('- worker, this fails for unknown reason', e)
    ###
    # 4 is worklist, 2 is handle
    # change 39
    ###
    #if VWORK_LIST[fworkout][4] == None and VWORK_LIST[fworkout][3] != 7:
    if VWORK_LIST[fworkout][4] == [] and VWORK_LIST[fworkout][3] != 7:
        ### chkeck if there is work, and if not connected
        if VWORK_LIST[fworkout][2] != None:
            ### if handle exists, but no work, then disconnect, or if connection count eq 3
            try:
                ble.gap_disconnect(VWORK_LIST[fworkout][2])
            except Exception as e:
                print('- worker disconn warn 1 ', e)
                VWORK_LIST[fworkout][2] = None
                VWORK_LIST[fworkout][3] = 8
                VWORK_LIST[fworkout][5] = None
        VWORK_LIST[fworkout][1] = ftimenow
        return
    ###
    ### IMPORTANT everything below assumes there is work to do
    ### print info if some work to be done
    print('= worker ', fworkout, ftimediff)
    ###
    ###
    if fworkout == '00:00:00:00:00:00' and len( VWORK_LIST[fworkout][4] ) > 0:
        ### do some system actions
        if VWORK_LIST[fworkout][4][0] == 'scan':
            fscan(20)
        elif VWORK_LIST[fworkout][4][0] == 'reboot':
            machine.reboot()
        elif VWORK_LIST[fworkout][4][0] == 'ntp':
            ntptime.settime()
        elif VWORK_LIST[fworkout][4][0] == 'disc':
            fdisc()
        gc.collect()
        return
    #if VWORK_LIST[fworkout][3] != 8 and ftimenow - VWORK_LIST[fworkout][1] == 1 * 60:
    # change 39
    # there is work, but not being done, then delay this work, and reset timers
    ###
    #if ftimenow - VWORK_LIST[fworkout][1] > ( VGLOB['delaywork'] * len(VWORK_LIST) ) + ( 3 * VGLOB['delaywork'] ): # and abs( VWORK_LIST[fworkout][0] - VWORK_LIST[fworkout][1] ) > 30:
    ###
    ### retries
    ### ISSUE
    if type( VWORK_LIST[fworkout][5] ) == int:
        if int( VWORK_LIST[fworkout][5] or 0 ) > 3:
            ### update the check and conn timer
            #VWORK_LIST[fworkout][0] = ftimenow
            print('= worker tried a few times, delaying')
            VWORK_LIST[fworkout][1] = ftimenow
            VWORK_LIST[fworkout][5] = None
            if len(VWORK_LIST[fworkout][4]) > 10:
                ### too much work, removing
                VWORK_LIST[fworkout][4].pop(0)
            gc.collect()
            return
            ### no return in main if, as there might be some work to do
    ###
    ### if the above is fine, just move forward
    ###
    if VWORK_LIST[fworkout][3] not in [8, 7]:
        print('= worker maybe working')
        # TODO
        # if maybe working for more than 10 sec, then disconnect
        # it waits until next round
#        if ftimenow - VWORK_LIST[fworkout][1] > 10:
        if ftimenow - VWORK_LIST[fworkout][1] > ( VGLOB['delaywork'] * len(VWORK_LIST) ) + 5:
            try:
                ble.gap_disconnect(VWORK_LIST[fworkout][2])
            except Exception as e:
                print('- worker disconn warn 3 ', e)
                #VWORK_LIST[fworkout][0] = ftimenow
                VWORK_LIST[fworkout][1] = ftimenow
                VWORK_LIST[fworkout][2] = None
                VWORK_LIST[fworkout][3] = 8
        # return
    ###
    elif VWORK_LIST[fworkout][3] == 8:
        ### finally, all abouve is fine, and work is to be done, so connect first
        print("= worker connecting")
        # longer waiting times
        # do not update time here, as the connection may fail
        VWORK_LIST[fworkout][5] = int(VWORK_LIST[fworkout][5] or 0) + 1
        try:
            # increased connection time
            ble.gap_connect( 0, fcode_addr(fworkout), 5000 )
        except Exception as e:
            print('- worker conn warn ', e)
            #pass
        # return
    ###
    ### assuming connected, so work
    elif VWORK_LIST[fworkout][3] in [7, 18]:
        print("- worker connected - send work")
        #
        VWORK_LIST[fworkout][5] = None
        if len( VWORK_LIST[fworkout][4] ) == 0:
            print("= worker, connected, but no work, disconnect")
            ble.gap_disconnect(VWORK_LIST[fworkout][2])
            return
        # maybe not update, to do whole work in one run
        #VWORK_LIST[fworkout][1] = time.time()
        # select first from the work list
        worka = str(VWORK_LIST[fworkout][4][0]).strip().split(' ')
        for iii in range(max(0, 2 - len(worka))):
            worka.append('')
        ### 43 no thread
        _thread.start_new_thread(fble_write, (fworkout, worka[0], worka[1]))
        #fble_write(fworkout, worka[0], worka[1])
        # return
    ###
    ### some other situation happened
    else:
        print('- worker unexpected situation')
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
    # VGLOB['time']
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
IP: """ + str(station.ifconfig()[0]) + """
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
    html = html.encode('ascii')
    #
    gc.collect()
    #
    return( html )

#-####
#-####
# -#### webpage loop function
# -#### was based on socket, but now on async is more responsive and less consuming

async def loop_web(reader, writer) -> None:
    # waiting for input
    #recv = await reader.read(64)
    await asyncio.sleep(0.1)
    recv = yield from reader.read(64)
    flood = 0
    if gc.mem_free() < 10000:
        print('+ page flood 1')
        #GET / HTTP/1.1
        flood = 1
    #print("- f serving page")
    #timer1 = time.ticks_ms()
    # 'GET / HTTP/1.
    try:
        #recvtmp = recv.decode()
        if flood == 0:
            requesttype = recv.decode()[0:3]
            requestfull = recv.decode().split('\r')[0].split(' ')[1].split('?')
            #requestfull = requestfull  # [4:-6]
            #recv2 = await reader.read()
            #print( recv2.decode() )
        else:
            requestfull = ['/flood']
    except Exception as e:
        # if request invalid or malformed
        print('+ page request warn ', e)
        requestfull = ['/']
        # continue
    # ?
    #
    print('= f serving page ', requestfull)
    global VGLOB
    global VSCAN_LIST
    request = requestfull[0]
    #print(request, requestfull)
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
        # await writer.awrite(vwebpage)
        #vwebpage = b''
        # continue
    #####
    #####
    elif request == "/flood":
        header = """HTTP/1.1 200 OK
        Content-Type: text/html
        Content-Length: 12
        Connection: close
        """
        await writer.awrite(header + "\r\n" + "flood, retry" + "\r\n")
        # gc.collect()
    elif request == "/list":
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
        print(recv3)
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
                print('--- deldo file does not exist ', e)
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
        vwebpage = """Directory listing on ESP. By writing /deldo?filename, files can be removed (dangerous).
Files with _old are safety copies after OTA, can be safely removed.
To disable webrepl, delete webrepl_cfg.py and reboot device.

Dir: """ + str(os.listdir()) + """

Current work: """ + str(VGLOB) + """

Details:\n""" +  "\n".join( [ str(aaa) for aaa in VWORK_LIST.items() ] ) + """

MQTT addresses IN:\n""" + "\n".join( [ str(aaa) for aaa in VMQTT_SUB_LIST ] ) + """

Status: """ + status + """

Reset cause: """ + str(reset_cause) + """
Micropython version: """ + str(os.uname()) + """
Free RAM (over 40k is fine, 70k is good): """ + str(gc.mem_free()) + """."""
        #
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
            print('--- webrepl init issue ', e)
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
        # machine.reset()
    elif request == "/mqttauto":
        fdisc()
        header = """HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 30
Connection: close

MQTT Autodiscovery published.
"""
        #conn.sendall(header + "\r\n" + vwebpage)
        await writer.awrite(header + "\r\n")
        # await writer.awrite(vwebpage)
        # machine.reset()
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
        # machine.reset()
    #####
    #####
    elif request == "/ota":
        # postpone job, to speed up ota
        VGLOB['timework'] = time.time()+120
        VGLOB['timescan'] = time.time()+180
        ble.gap_scan( 0 )
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
        VGLOB['timework'] = time.time()+120
        VGLOB['timescan'] = time.time()+180
        vwebpage = ''
        #VGLOB = ''
        VSCAN_LIST = {}
        #gc.collect()
        # s.setblocking(0)
        header = """HTTP/1.1 302 Found
Content-Length: 0
Location: /reset
Connection: close

"""
        # =
        ble.active(False)
        gc.collect()
        #headerin = conn.recv(500).decode()
        headerin = yield from reader.read(500)
        # print(headerin)
        headerin = headerin.decode()
        boundaryin = headerin.split("boundary=", 2)[1].split('\r\n')[0]
        lenin = int(headerin.split("\r\nContent-Length: ", 2)[1].split('\r\n')[0])
        # dividing into 2000 bytes pieces
        bufflen = round(lenin / float(str(round(lenin / 2000)) + ".5"))
        #lenin = 0
        # print("===")
        #print( headerin )
        #print( "===" )
        begin = 0
        try:
            os.remove('upload')
        except Exception as e:
            # try to upload file, if fail no panic
            print('+ otado cleaning fail 1, this is fine', e)
            #pass
        fff = open('upload', 'wb')
        while True:
            #dataaa = conn.recv(bufflen).decode().split('\r\n--' + boundaryin, 2)
            dataaa = yield from reader.read(bufflen)
            dataaa = dataaa.decode().split('\r\n--' + boundaryin, 2)
            splita = len(dataaa)
            #print( splita )
            #filein += dataaa
            if begin == 0 and splita == 3:
                #print( "= short" )
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
                #print( "= first" )
                # first
                namein = dataaa[1].split(' filename="', 1)[1].split('"\r\n', 1)[0]
                fff.write(dataaa[1].split('\r\n\r\n', 1)[1])
                begin = 1
            elif begin == 1 and splita == 1:
                #print( "= middle" )
                # middle
                fff.write(dataaa[0])
            elif begin == 1 and splita == 2:
                #print( "= last" )
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
                print('+ otado cleaning fail 2, this is fine', e)
                #pass
            try:
                os.rename(namein, namein + "_old")
            except Exception as e:
                print('+ otado cleaning fail 3, this is fine', e)
            os.rename('upload', namein)
        #print( "===" )
        #print( namein )
        #print( lenin )
        dataaa = ''
        ble.active(True)
        #gc.collect()
    #####
    #####
    elif request == "/reset":
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
        await asyncio.sleep(0.1) # was 0.3
        machine.reset()
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
        await writer.drain()
    except Exception as e:
        print('- page flood 2', e)
    # drain and sleep needed for good transfer
    vwebpage = b''
    resp = b''
    # was 0.2
    await asyncio.sleep(0.1)
    await reader.wait_closed()
    # await reader.aclose()
    gc.collect()
    #print("-- f serving page done")
    if not CONFIG2['loop']:
        _thread.exit()
        return
        # break
    # catch OSError: [Errno 104] ECONNRESET ?

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
    print('- fcheck')
    try:
        wdt.feed()
    except Exception as e:
        print('- fcheck wdt error, maybe not initialised ', e)
    ###
    if int(gc.mem_free()) < 30000:
        print('- fcheck memory full')
        gc.collect()
        return
    ###
    try:
        mqtth.ping()
    except Exception as e:
        print('- fcheck mqqt ping error ', e)
    ###
    global VGLOB
    if VGLOB['status'] == 5:
        return
    ### if all is fine, then get some globals first
    global VSCAN_LIST
    global VWORK_LIST
    ftimenow = time.time()
    ###
    ###
    if ble.active() == False:
        print('- fcheck ble')
        ble.active(True)
        return
        # fble_recover()
    ###
    ###
    if station.isconnected() == False or station.ifconfig()[0] == '0.0.0.0':
        print('- fcheck wifi')
        station.connect()
        return
        # machine.reset()
    # if mqtth.last_cpacket - mqtth.last_ping > 10*60*1000:
    #    print('-- fcheck mqtt')
    #    fmqtt_recover()
    ###
    ### this is in ms, most other calculations for time are in seconds
    if time.ticks_ms() - mqtth.last_cpacket > 5 * 60 * 1000:
        print('- fcheck mqtt')
        _thread.start_new_thread(fmqtt_recover, ())
        #fmqtt_recover()
        return
    ###
    ### remove addresses older than x minutes
    #last_contact = 9999
    # this concerns VSCAN_LIST and not VWORK_LIST
    for addr, val in VSCAN_LIST.items():
        if ftimenow - val[3] > 20 * 60:
            VSCAN_LIST.pop(addr)
    ###
    ### check ntp every 24 hours
    if ftimenow - VGLOB['timentp'] > 24 * 60 * 60:
        VGLOB['timentp'] = ftimenow
        fntp()
    ###
    ### check autodiscovery every 6 hours
    if ftimenow - VGLOB['timedisc'] > 6 * 60 * 60:
        VGLOB['timedisc'] = ftimenow
        fdisc()
    ###
    ### if 5 minutes from the last contact, then scan
    # INFO: optimisations for scan scheduling make no sense, start every 1 minute
    # here I use the global variable timescan
    # still the VWORK_LIST['00:00:00:00:00:00'][0] system variable last work could be used
    if ftimenow - VGLOB['timescan'] > 1 * 60 and len( VWORK_LIST['00:00:00:00:00:00'][4] ) == 0:
        # if all handles are null, start scan
        #if [aaa[2] for aaa in VWORK_LIST.values()] == [None] * len(VWORK_LIST):
        if len( VWORK_LIST['00:00:00:00:00:00'][4] ) == 0:
            VWORK_LIST['00:00:00:00:00:00'][4].append( 'scan' )
            #VWORK_LIST['00:00:00:00:00:00'][0] = time.time()
            #VWORK_LIST['00:00:00:00:00:00'][1] = time.time()
            #ble.gap_scan(20 * 1000, 50000, 30000, 1)
            #ble.gap_scan(40 * 1000, 50000, 30000, 1)
    ###
    ###
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
    gc.collect()
    #_thread.exit()
    #VGLOB['status'] = 8
    #print('-- fcheck done')
    return

#-####
#-####
#-####


def fdisc(var=None) -> None:
    ###
    print('= send mqtt autodiscovery')
    ### home assistant auto discovery
    ### discovery topic should be retained
    #print("publishing mqtt autodiscovery")
    ###
    ### loop through all trusted devices
    for hhh in VWORK_LIST:
        time.sleep(0.1) # was 0.5
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
            devicet = '{"device_class": "temperature", "name": "Mijia ' + mac + ' Temperature", \
"state_topic": "' + CONFIG2["mqtt_thermo"] + mac + '/radout/status", "unit_of_measurement": "°C", "value_template": "{{ value_json.temp }}", \
"uniq_id": "temp_' + mac + '_T", "dev": { "ids": [ "temp_' + mac + '" ], "name":"temp_' + mac + '" } }'
            mqtth.publish(topict, bytes(devicet, 'ascii'), True)
            ###
            topich = f'homeassistant/sensor/temp_{mac}_hum/config'
            deviceh = '{"device_class": "humidity", "name": "Mijia ' + mac + ' Humidity", \
"state_topic": "' + CONFIG2["mqtt_thermo"] + mac + '/radout/status", "unit_of_measurement": "%", "value_template": "{{ value_json.hum }}", \
"uniq_id": "temp_' + mac + '_H", "dev": { "ids": [ "temp_' + mac + '" ], "name":"temp_' + mac + '" } }'
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
            devicec = '{ "name": "clim_' + mac + '_eq3", "unique_id": "id_' + mac + '", "modes": [ "heat" ], \
"mode_cmd_t": "' + CONFIG2['mqtt_eq3'] + mac + '/radin/mode2", "mode_stat_t": "' + CONFIG2['mqtt_eq3'] + mac + '/radout/status", \
"mode_stat_tpl": "{{value_json.mode2}}", "temp_cmd_t": "' + CONFIG2['mqtt_eq3'] + mac + '/radin/temp", \
"temp_stat_t": "' + CONFIG2['mqtt_eq3'] + mac + '/radout/status", "temp_stat_tpl": "{{value_json.temp}}", \
' + currtemp + ' "min_temp": "5", "max_temp": "29.5", "temp_step": "0.5", \
"hold_state_template": "{{value_json.mode}}", "hold_state_topic": "' + CONFIG2['mqtt_eq3'] + mac + '/radout/status", \
"hold_command_topic": "' + CONFIG2['mqtt_eq3'] + mac + '/radin/mode", "hold_modes": [ "auto", "manual", "boost", "away" ] }'
            mqtth.publish(topicc, bytes(devicec, 'ascii'), True)
            ### battery and valve open sensors
            topicc = f'homeassistant/sensor/clim_{mac}_eq3_valve/config'
            devicec = '{ "name": "clim_' + mac + '_eq3_valve", \
"state_topic": "' + CONFIG2['mqtt_eq3'] + mac + '/radout/status", "value_template": "{{ value_json.valve }}", \
"uniq_id": "id_' + mac + '_valve" }'                     
            mqtth.publish(topicc, bytes(devicec, 'ascii'), True)
            ###
            topicc = f'homeassistant/sensor/clim_{mac}_eq3_battery/config'
            devicec = '{ "name": "clim_' + mac + '_eq3_battery", \
"state_topic": "' + CONFIG2['mqtt_eq3'] + mac + '/radout/status", "value_template": "{{ value_json.battery }}", \
"uniq_id": "id_' + mac + '_battery" }'                     
            mqtth.publish(topicc, bytes(devicec, 'ascii'), True)
            ###    
            # add True at the end to retain or retain=True
        if mac_type[0:4] == 'FFFF':
            #topicp = f'homeassistant/sensor/presence_{mac}_eq3/config'
            topicp = f'homeassistant/device_tracker/presence_{mac}_eq3/config'
            devicep = '{"name": "Tracker ' + mac + '", "state_topic": "' + CONFIG2["mqtt_presence"] + mac + '/radout/status", \
"expire_after": "240", "consider_home": "180", "unique_id": "tracker_' + mac + '", "source_type": "bluetooth" }'
            #devicep = '{"name": "Tracker ' + mac + '", "state_topic": "' + CONFIG2["mqtt_presence"] + mac + '/radout/status", "value_template": "{{ value_json.location }}", "expire_after": "180", "uniq_id": "tracker_' + mac + '", "dev": { "ids": [ "tracker_' + mac + '" ], "name":"tracker_' + mac + '" }}'
            #devicep = '{"device_class": "None", "name": "Tracker ' + mac + '", "state_topic": "' + CONFIG2["mqtt_presence"] + mac + '/radout/status", "value_template": "{{ value_json.location }}", "uniq_id": "tracker_' + mac + '", "dev": { "ids": [ "tracker_' + mac + '" ], "name":"tracker_' + mac + '" }, "expire_after": 120 }'
            mqtth.publish(topicp, bytes(devicep, 'ascii'), True)
        ###
        ### here additional devices for publishing can be added
    gc.collect()
    return

#-####
#-####
#-####

def fmqtt_recover(var=None) -> None:
    global VGLOB
    print('= f mqtt recover')
    VGLOB['status'] = 1
    mqtth.keepalive = 130 # that is that ping fits easily 3 times
    #time.sleep(0.5)
    mqtth.connect()
    #time.sleep(0.5)
    mqtth.set_callback(fmqtt_irq)
    #time.sleep(0.5)
    for lll in VMQTT_SUB_LIST:
        mqtth.subscribe(lll)
    # mqtth.subscribe(CONFIG2['mqtt_eq3_in'])
    VGLOB['status'] = 8
    #gc.collect()
    try:
        # if run as thread, then stop thread
        _thread.exit()
        #pass
    except Exception as e:
        # if this fails, there is no reason to panic, function not in thread
        print('- fblew close thread:', e)
    gc.collect()
    return


# -#### mqtt
# -#### this is moved from boot, to allow recovery
_thread.start_new_thread(fmqtt_recover, ())
# wait for connection at boot
time.sleep(2)

#-####
#-####
# -#### connect interrupts
ble.irq(fble_irq)

#-####
#-####
# -#### threads
#loopwebthread = _thread.start_new_thread(loop_web, ())

def fstart_server() -> None:
    async_loop = asyncio.get_event_loop()
    vserver = asyncio.start_server(loop_web, "0.0.0.0", 80)
    async_loop.create_task(vserver)
    async_loop.run_forever()
    return

#-####
#-####
#-####
#thread_web = _thread.start_new_thread(fstart_server, ())
_thread.start_new_thread(fstart_server, ())

#-#### WDT
# do not move this to boot
# after boot is succesful
wdt = machine.WDT( timeout = int( VGLOB['delaycheck'] * 2 ) * 1000 )

#-####
#-####
# -#### first scan, longer
# if this is on, then something other fails...
fdisc()
fntp()
fscan(60)
# wait for connection at boot
time.sleep(2)

# -#### timers
# -#### scan every x minutes
# 4-5 seconds is completely fine for work
#
timer_work.init( period = ( VGLOB['delaywork'] * 1000 ), callback=fworker)
# ### clean every 1 minutes
#_thread.start_new_thread(fble_write, (fworkout, worka[0], worka[1]))

#
timer_check.init( period = ( VGLOB['delaycheck'] * 1000 ), callback=fcheck)
#timer_check.init( period = ( VGLOB['delaycheck'] * 60 * 1000 ), callback=_thread.start_new_thread( fcheck, [None] ) )

# no timers to save timers ;)
###
### Main loop
###
#while True:
#    # #await asyncio.sleep(5)
#    time.sleep(5)
#    gc.collect()
#    # #
#    #ftimenow = time.time()
#    print('. main loop', time.time() - VGLOB['timework'], VGLOB['delayquery'] )
#    # #
#    if time.time() - VGLOB['timework'] > VGLOB['delayquery']:
#        print('. worker')
#        fworker(1)
#    elif time.time() - VGLOB['timecheck'] > VGLOB['delayquery'] * 1000:
#        print('. check')
#        VGLOB['timecheck'] = time.time()
#        fcheck(1)

#time.sleep(2)

gc.collect()

#-###
