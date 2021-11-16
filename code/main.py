# ###

#import sys
# whi#telist here
# blacklist here

# maybe add micropython version
# os.uname()

# get timeup (time.ticks_ms()/1000/60/60/24)
# or set time.time() as a boot time

# checking

# ### define global variables
vglob = {}
vglob['addr'] = ''
vglob['handle'] = ''
vglob['status'] = 8  # 8=disconnected
vglob['result'] = 0
vglob['work'] = ''
vglob['data'] = ''
vglob['time'] = time.time()
vglob['timescan'] = time.time()
vglob['timeup'] = time.time()
vglob['timework'] = time.time()

vglob_list = {}
# ### work list
vwork = OrderedDict()

vwork_status = {}

vwork_list = {}

#-####
#-####
#-####


def fnow(nowtime="", ttt="s"):
    # typing time.time in default value does not work
    if nowtime == "":
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
# -#### decode addres in a readable format

def ffind_handle(handle):
    global vwork_list
    for key, iii in vwork_list.items():
        if iii[2] == handle:
            return key

def fdecode_addr(addr):
    result = []
    for iii in addr:
        result.append('{:0>2}'.format(str(hex(iii).split('x')[1])))
    return str((':').join(result)).upper()


def fcode_addr(addr):
    result = []
    for iii in addr.split(":"):
        result.append( int(str(iii), 16) )
    return bytes( result )

#-####
#-####
#-#### load white lists

try:
    wl = open('wl.txt', 'r')
    vwork_temp = eval( str(wl.read()) )
    for jjj in vwork_temp:
        vwork_list[ jjj ] = [ fcode_addr(jjj), time.time(), None, None, None, None ]
    del vwork_temp
    wl.close()
except:
    vwork_list[ '00:00:00:00:00:00' ] = [ b'\x00\x00\x00\x00\x00\x00', time.time(), None, None, None, None ]

#-####
#-####
# -#### pretty list print

def fprint(cmd='show'):
    global vglob_list
    ret = ""
    if cmd == 'show':
        for iii in vglob_list.items():
            ret += str(iii[0]) + " " + '{: >{w}}'.format(str(time.time() - iii[1][3]), w=5) + " " + str(iii[1][1]) + " " + str(iii[1][2]) + "\n"
        print(ret)
    if cmd == 'get':
        return ret

#-####
#-####
# -#### main worker


def fble_write(addr, data1, data2=''):
    # writer triggered in fget_work, and results in ble irqs
    global vglob
    global vglob_list
    global vwork
    global vwork_list
    #print('- fble_write - ', str(addr), str(data1))
    # ### main loop
    # ### try connection 20 times, if succesful stop the loop
    print("- f ble write")
    #print( str(addr), str(data1), str(data2) )
    #print( str(vglob['addr']), str(vglob['work']) )
    if (addr[0:8] == '4C:65:A8' or addr[0:8] == 'A4:C1:38') and data1 == 'gettemp':
        data1 = 0x10
        data2 = b'\x01\x00'
    elif addr[0:8] == '00:1A:22' and data1 == 'settemp' and (str(data2).split('.')[0]).isdigit():
        data1 = 0x0411
        if float(data2) > 28:
            data2 = 28
        if float(data2) < 12:
            data2 = 12
        data2 = '\x41' + chr(int(round(2 * float(data2))))
    elif addr[0:8] == '00:1A:22' and data1 == 'manual':
        data1 = 0x0411
        data2 = '\x40\x40'
    #else:
    #    # ### when bad variables, end by simulating status disconnected
    #    vglob['status'] = 8
    #    # continue
    #    #break
    # ### if no issue with above
    # ### and variables cleaned, try to write
    try:
        fhandle = vwork_list[addr][2]
        #ble.gattc_write(vglob['handle'], data1, data2, 1)
        ble.gattc_write( fhandle, data1, data2, 1 )
        print('-- ble write write')
        # for jjj in range(60):
        #    #print('--- wait for connect')
        #    f vglob['status'] != 8:
        #        continue
        #    time.sleep(0.5)
    except Exception as e:
        print('-- exc disconn exc:', e)
    #
    # ### if loop ended or break then try to disconnect, set status to disconnected
    # 31 add
    gc.collect()
    # ?
    try:
        # if run as thread, then stop thread
        _thread.exit()
    except:
        pass
    return

#-####
#-####
# -#### main function to handle irqs from mqtt


def fble_irq(event, data):
    # interrupt triggered by ble
    # usually only if connection is processed
    global vwork_list
    global vglob_list
    global vglob
    #global vwebpage
    global vwork_status
    # ### get event variable and publish global so other threads react as needed
    vglob['status'] = event
    #print( "f ble irq", event)
    # do not print scans, event 5
    if event != 5:  # 17
        print('- f ble irq ', event, ', ', list(data))
    # ###
    if event == 5:  # _IRQ_SCAN_RESULT
        # ### scan results, and publish gathered addresses in vglob_list
        addr_type, addr, adv_type, rssi, adv_data = data
        # special case for presence sensors with FF:FF addresses
        addr_decode = str(fdecode_addr(addr))
        if bytes(addr)[0:2] == b'\xff\xff' and adv_type == 0:
            adv_type = 4
            # this has to be like this, to pass through the cleaner later
            adv_data = b'__Tracker'
        # only full detections, with names, so adv_type == 4
        if adv_type == 4:
            #print( str(bytes(adv_data)[2:24].split(b'\xff')[0] ) )
            vglob_list[addr_decode] = [bytes(addr), rssi, bytes((x for x in bytes(adv_data)[2:22].split(b'\xff')
                                                                 [0] if x >= 0x20 and x < 127)).decode("ascii").strip(), time.time()]
        else:
            pass
            # return
        # debug temp
        if addr_decode[0:8] == '4C:65:A8' or addr_decode == 'A4:C1:38':
            pass
        #    print( "-- irq temp ", addr_decode, list( bytearray( adv_data ) ) )
        # clean after each new result
        gc.collect()
    elif event == 6:  # _IRQ_SCAN_DONE
        #vwebpage = fwebpage()
        # ### scan done and cleanup, reseting variables as needed
        # 31 added
        # time.sleep(1)
        vglob['status'] = 8
        vglob['result'] = 0
        print('-- scan done')
        # gc.collect()
    elif event == 7:  # _IRQ_PERIPHERAL_CONNECT
        # ### connected 7
        handle, addr_type, addr = data
        addrd = fdecode_addr(addr)
        #print( addrd )
        vglob['result'] = 2
        vglob['handle'] = handle
        #try:
        #    vglob_list[vglob['addr']][3] = time.time()
        #except:
        #    pass
        # do not change the time with connect, but only disconnect
        #vwork_list[ addrd ][1] = time.time()
        vwork_list[ addrd ][2] = handle
        vwork_list[ addrd ][3] = event
    elif event == 8:  # _IRQ_PERIPHERAL_DISCONNECT
        # ### disconnected 8, do actions
        handle, addr_type, addr = data
        addrd = fdecode_addr(addr)
        vglob['handle'] = handle
        #### DONE
        # update the time of the original address too
        #addrdo = ffind_handle(handle)
        #print( addrd, handle, addrdo )
        #vwork_list[ addrdo ][1] = time.time()
        #### TODO
        # if disconnected from handle, with address 00, then the device is out of range
        # try later, so update the timer
        #### INFO the above does not work so well ;D
        ###
        # remove the handle
        vwork_list[ addrd ][1] = time.time()
        vwork_list[ addrd ][2] = None # this is handle
        vwork_list[ addrd ][3] = event
        vwork_list[ addrd ][5] = None
        # written, so remove from work list
        # only in response obtained 18
        #vwork_list[ addrd ][4] = None
        # for mijia
        # 20211109 new
        #vglob['addr'] = ''
        vglob['timework'] = time.time()
        #vglob['work'] = ''
        gc.collect()
    elif event == 17:  # 17 _IRQ_GATTC_WRITE_DONE
        # ### write to device
        handle, value_handle, status = data
        addrd = ffind_handle(handle)
        ### update work times, but do not remove work list (until response)
        vwork_list[ addrd ][1] = time.time()
        vwork_list[ addrd ][3] = event
        ###
        vglob['handle'] = handle
        vglob['result'] = 4
    elif event == 18:  # _IRQ_GATTC_NOTIFY
        # ### getting ble notification irq
        handle, value_handle, notify_data = data
        addrd = ffind_handle(handle)
        vwork_list[ addrd ][1] = time.time()
        vwork_list[ addrd ][3] = event
        # written, so remove from work list
        vwork_list[ addrd ][4] = None
        #vwork_list[ addrd ][5] = notify_data
        ###
        msg_out = None
        ###
        ###
        vglob['data'] = notify_data
        vglob['addr'] = addrd
        ###
        ### new
        if ( vglob['addr'][0:8] == '4C:65:A8' or vglob['addr'][0:8] == 'A4:C1:38' ) and vwork_list[ addrd ][5] == None:
            # ### only if result 3 = if notify succesful, then publish
            # ### create mqtt
            datas = str(bytes(vglob['data']), 'ascii').strip('\x00').strip().replace(' ', '=').split('=')
            msg_out = '{"trv":"' + vglob['addr'] + '","temp":"' + str(datas[1]) + '","hum":"' + str(datas[3]) + '"}'
            #topic_out = config2['mqtt_mijia_out']
            topic_out = 'esp/sensor/sensor' + str(vglob['addr'][9:17].replace(":", "")) + '/state'
            # send only once
            vwork_list[ addrd ][5] = 1
        ###
        if vglob['addr'][0:8] == '00:1A:22':
            # ### create mqtt
            datas = list(bytearray(vglob['data']))
            msg_out = '{"trv":"' + vglob['addr'] + '","temp":"' + str(float(datas[5]) / 2) + '","mode":"manual"}'
            topic_out = config2['mqtt_eq3_out']
            #mqtth.publish(config2['mqtt_eq3_out'], bytes(msg_out, 'ascii'))
        # ### if connection or writing not succesful, then re-add
        ###
        ###
        if msg_out != None:
            #print('=== msg ===', msg_out)
            mqtth.publish(topic_out, bytes(msg_out, 'ascii'))
            vwork_status[vglob['addr']] = msg_out
            # recache page only if something changed/sent
            #vwebpage = fwebpage()
            # sleep for jobs to finish
            # 31 added
            # time.sleep(1)
        ###
        ### old
        #print( bytes(value_handle) )
        vglob['handle'] = handle
        # ### for mijia
        vglob['data'] = notify_data
        # ### set result to 3, which means success notify
        vglob['result'] = 6
        ###
        gc.collect()
    else:
        print('-- else')
    ###
    ###
    gc.collect()
    # not in thread
    # _thread.exit()
    return

#-####
#-####
#-####


def fble_scan(var):
    # ### starting scanning thread and setting variables
    #print('- fble_scan - ', str(var))
    vglob['status'] = 1
    vglob['result'] = 1
    vglob['work'] = 'scan'
    vglob['timescan'] = time.time()
    print('- scan start')
    # sleep for jobs to finish
    # time.sleep(1)
    if str(var) == '0':
        # 40 seconds as a full scan is more than necessary
        # was 30, but made 40 at boot
        #_thread.start_new_thread(ble.gap_scan, (40 * 1000, 30000, 30000, 1))
        #ble.gap_scan(40 * 1000, 30000, 30000, 1)
        ble.gap_scan(40 * 1000, 50000, 30000, 1)
    else:
        # was 15 seconds, is 20, 10 is a little too short
        #_thread.start_new_thread(ble.gap_scan, (15 * 1000, 30000, 30000, 1))
        #ble.gap_scan(15 * 1000, 30000, 30000, 1)
        ble.gap_scan(15 * 1000, 50000, 30000, 1)
    # 31 add
    # time.sleep(1)
    gc.collect()
    # _thread.exit()
    return

#-####
#-####
#-####


def fmqtt_irq(topic, msg, aaa=False, bbb=False):
    # ### if the check msg is started, then this function is triggered
    # interruption when the message from mqtt arrives
    # this happens only if messages are previously requested
    print("- f mqtt irq trigger")
    global vwork
    if type(msg) is bytes:
        msg = msg.decode()
    if type(topic) is bytes:
        topic = topic.decode()
    # ### split address and command
    worka = str(msg).strip().split(' ', 1)
    #print('- fmqtt_irq - ', str(msg))
    # 31 add
    #-### new approach
    if worka[0] not in list(vwork_list):
        print('-- f mqtt irq not on list')
    elif len(worka[0]) == 17 and len(worka[1]) > 5 and len(worka[1]) < 14:
        if worka[1] == "manual" and vwork_list[ worka[0] ][4] != None:
            # do not overwrite if only temp check
            pass
        else:
            vwork_list[ worka[0] ][4] = worka[1]
    else:
        print('-- f mqtt irqbad message')
    # time.sleep(1)
    # ### if len 1, then scan and reset allowed
    # ### scan, adds scan to worklist, reset - resets immediately
    if len(worka) == 1:
        if worka[0] == 'scan':
            # add scan to worklist
            vwork['0'] = 'scan'
            return
        elif worka[0] == 'reset':
            # reset
            machine.reset()
            # is this necessary ? NO
            # time.sleep(1)
    # ### if above not true and address not in the list, then skip
    # ### whitelist could be added
    #elif worka[0] not in vglob_list.keys() and worka[0] not in vwork_status.keys():
    #    print('-- address not available')
    #    # return
    ## ### if addres in the list, of correct lenght, and command lenght between 5 and 14 letters
    #elif len(worka[0]) == 17 and len(worka[1]) > 5 and len(worka[1]) < 14:
    #    # do not overwrite if work task is not 'manual', else add if not in the list
    #    #
    #    if worka[0] not in vwork.keys() or worka[1] != 'manual':
    #        vwork[worka[0]] = worka[1]
    #        return
    # ### otherwise, bad message, syntax, etc
    #else:
    #    print('-- bad message')
    gc.collect()
    # _thread.exit()
    return

#-####
#-####
#-####

def fworker(var):
    #global vwork
    global vwork_list
    global vglob
    #global vglob_list
    # select which device was checked longest time ago
    try:
        mqtth.check_msg()
    except:
        pass
    ftimenow = time.time()
    ftimediff = 0
    fworkout = None
    for kkk in vwork_list.items():
        if ftimediff < ftimenow - kkk[1][1]:
            ftimediff = ftimenow - kkk[1][1]
            fworkout = kkk[0]
            #print(ftimediff, fworkout)
    # print selected device
    #print('- worker ', fworkout, ftimediff)
    # if just rebooted, then change None with 8
    if vwork_list[fworkout][3] == None:
        vwork_list[fworkout][3] = 8
    # chckeck if there is work
    # no work
    #if vwork_list[fworkout][3] == 8 and vwork_list[fworkout][4] == None:
    if vwork_list[fworkout][4] == None:
        try:
            ble.gap_disconnect(vwork_list[fworkout][2])
        except:
            pass
        vwork_list[fworkout][1] = time.time()
        return
    print('- worker ', fworkout, ftimediff)
    if fworkout == '00:00:00:00:00:00':
        if vwork_list[fworkout][4] == 'scan':
            print('--- start scan')
        if vwork_list[fworkout][4] == 'reboot':
            print('--- reboot')
        #if vwork_list[fworkout][4] == 'ntp':
    # check if connection locked, and disconnect
    if vwork_list[fworkout][3] != 8 and ftimenow - vwork_list[fworkout][1] == 3*60:
        try:
            ble.gap_disconnect(vwork_list[fworkout][2])
        except:
            pass
        vwork_list[fworkout][1] = time.time()
        vwork_list[fworkout][2] = None
        vwork_list[fworkout][3] = 8
        # do not reset the work, so that it will be re-done
        #vwork_list[fworkout][4] = None
        return
    # if the above is fine
    if vwork_list[fworkout][3] != 8 and vwork_list[fworkout][3] != 7:
        print('-- worker maybe working')
        #### TODO
        #### if maybe working for more than 10 sec, then disconnect
        if ftimenow - vwork_list[fworkout][1] > 20:
            try:
                ble.gap_disconnect(vwork_list[fworkout][2])
            except:
                pass
            vwork_list[fworkout][1] = time.time()
            vwork_list[fworkout][2] = None
            vwork_list[fworkout][3] = 8
        #return
    # work is to be done, so connect first
    elif vwork_list[fworkout][3] == 8 and vwork_list[fworkout][4] != None:
        print("-- worker connecting")
        # longer waiting times
        try:
            ble.gap_connect( 0, vwork_list[fworkout][0] )
            # does not work on older esp32
            #, 5000, 30000 )
        except Exception as e:
            print('-- worker conn ', e)
            pass
        #return
        # do not change the timer, to go into work write in the next round
    # assuming connected, so work
    elif vwork_list[fworkout][3] == 7:
        print("-- worker connected - send work")
        #
        # maybe not update, to do whole work in one run
        #vwork_list[fworkout][1] = time.time()
        #
        worka = str( vwork_list[fworkout][4] ).strip().split(' ')
        for iii in range(max(0, 2 - len(worka))):
            worka.append('')
        _thread.start_new_thread( fble_write, ( fworkout, worka[0], worka[1] ) )
        #return
    else:
        print('-- worker else')
    gc.collect()
    return

#-####
#-####
# -#### webpage generating function


def fwebpage():
    html_in = ""
    for vvv in vwork_list.items():
        html_in += str(vvv[0]) + " - " + str(vvv[1][4]) + "\n"
    # generate table
    # vglob['time']
    # generate rest of html
    #""" + str(vglob) + """
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
By Dr. JJ on ESP32 and micropython.
<h2>System</h2>
Last work done on: """ + str(fnow(vglob['time'])) + """<br/>
Last change: """ + str(fnow()) + """<br/>
Boot: """ + str(fnow(vglob['timeup'])) + """<br/>
Location: """ + str(config2['mqtt_usr']) + """<br/>
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
    # returning bytes, does not save memory
    return(str(html))

#-####
#-####
# -#### webpage loop function
# -#### was based on socket, but now on async is more responsive and less consuming


async def loop_web(reader, writer):
    # waiting for input
    recv = await reader.read(64)
    flood = 0
    if gc.mem_free() < 20000:
        print('- page flood 1')
        #GET / HTTP/1.1
        flood = 1
    #print("- f serving page")
    #timer1 = time.ticks_ms()
    # 'GET / HTTP/1.
    try:
        #recvtmp = recv.decode()
        if flood == 0:
            requestfull = recv.decode().split('\r')[0].split(' ')[1].split('?')  # [4:-6]
        else:
            requestfull = ['/flood']
    except:
        requestfull = ['/']
        # continue
    # ?
    gc.collect()
    print('- f serving page ', requestfull)
    request = requestfull[0]
    #print(request, requestfull)
    requestval = ''
    vwebpage = b''
    resp = b''
    #timer2 = time.ticks_ms()
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
        # INFO
        # await writer.awrite(vwebpage)
        #vwebpage = b''
        # continue
    #####
    #####
    elif request == "/flood":
        await writer.awrite("flood" + "\r\n")
    elif request == "/list":
        vwebpage = '<pre>\n'
        vwebpage += 'MAC, last seen, rssi, name\n'
        if len(vglob_list) > 0:
            for iii in vglob_list.items():
                vwebpage += '<a href="/wlistdo?' + str(iii[0]) + '">add</a> ' + str(iii[0]) + ' ' + \
                    '{: >{w}}'.format(str(time.time() - iii[1][3]), w=5) + ' ' + str(iii[1][1]) + ' ' + str(iii[1][2]) + '\n'
        else:
            vwebpage = '<pre>empty list</pre>\n'
        ###
        vwebpage += '\n\n'
        vwebpage += 'MAC remove white listed\n'
        for kkk in list(vwork_list):
            vwebpage += '<a href="/wlistdo?' + str(kkk) + '-">remove</a> ' + str(kkk) + ' ' + '\n'
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
    #####
    elif request == "/wlistdo":
        #vwork['0'] = 'scan'
        header = """HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 36
Connection: close

Added or removed """ + str(requestval) + """.
"""
        #conn.sendall(header + "\r\n" + vwebpage)
        await writer.awrite(header + "\r\n")
        # addr, time, handle, work, status
        #vglob_list[str(requestval)][0]
        if str(requestval)[-1] == "-":
            requestval = str(requestval)[0:17]
            del vwork_list[ str(requestval) ]
        else:
            vwork_list[ str(requestval) ] = [ bytes(vglob_list[ str(requestval) ][ 0 ]), time.time(), None, None, None, None ]
        filewl = open('wl.txt', 'w')
        filewl.write( str(list(vwork_list)) )
        filewl.close()
        # await writer.awrite(vwebpage)
        # machine.reset()
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
            except:
                pass
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
        if vglob['status'] == 8:
            status = "idle"
        elif vglob['status'] == 5:
            status = "scanning"
        elif vglob['status'] == 1:
            status = "recovering"
        else:
            status = "working"
        #
        vwebpage = """Directory listing on ESP. By writing /deldo?filename, files can be removed (dangerous).
Files with _old are safety copies after OTA, can be safely removed.
To disable webrepl, delete webrepl_cfg.py and reboot device.

Dir: """ + str(os.listdir()) + """

Current work: """ + str(vglob) + """
Scheduled work: """ + str(vwork) + """

Status: """ + status + """

Reset cause: """ + str(reset_cause) + """
Micropython version: """ + str(os.uname()) + """
Free RAM (over 40k is fine, 70k is good): """ + str(gc.mem_free()) + """."""

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
        except:
            pass
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
        vwork['0'] = 'scan'
        header = """HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 15
Connection: close

Scan scheduled.
"""
        #conn.sendall(header + "\r\n" + vwebpage)
        await writer.awrite(header + "\r\n")
        # await writer.awrite(vwebpage)
        # machine.reset()
    elif request == "/mqttauto":
        fmqtt_discover()
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
        vwebpage = ""
        gc.collect()
        # s.setblocking(0)
        header = """HTTP/1.1 302 Found
Content-Length: 0
Location: /reset
Connection: close

"""
        # =
        #headerin = conn.recv(500).decode()
        headerin = await reader.read(500)
        # print(headerin)
        headerin = headerin.decode()
        boundaryin = headerin.split("boundary=", 2)[1].split('\r\n')[0]
        lenin = int(headerin.split("\r\nContent-Length: ", 2)[1].split('\r\n')[0])
        bufflen = round(lenin / float(str(round(lenin / 3000)) + ".5"))
        #lenin = 0
        # print("===")
        #print( headerin )
        #print( "===" )
        begin = 0
        try:
            os.remove('upload')
        except:
            pass
        fff = open('upload', 'wb')
        while True:
            #dataaa = conn.recv(bufflen).decode().split('\r\n--' + boundaryin, 2)
            dataaa = await reader.read(bufflen)
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
            except:
                pass
            try:
                os.rename(namein, namein + "_old")
            except:
                pass
            os.rename('upload', namein)
        #print( "===" )
        #print( namein )
        #print( lenin )
        dataaa = ''
        # gc.collect()
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
    await asyncio.sleep(0.2)
    await reader.wait_closed()
    # await reader.aclose()
    gc.collect()
    print("-- f serving page done")
    if not config2['loop']:
        _thread.exit()
        return
        # break
    # catch OSError: [Errno 104] ECONNRESET ?

#-####
#-####
#-####


def fcheck(var):
    # ### yes, cleaning
    # new watchdog should check
    # station/wifi, mqtt, ble, webpage server, ntptime
    print('- fcheck')
    try:
        mqtth.ping()
    except Exception as e:
        print('-- fcheck mqqt ping error', e)
    global vglob
    global vglob_list
    if vglob['result'] != 0 and vglob['status'] == 8:
        vglob['result'] = 0
        vglob['data'] = ''
        vglob['work'] = ''
    if time.time() - vglob['timework'] > 3 * 60 and vglob['status'] != 8:
        vglob['status'] = 1
        #fble_recover()
    if vglob['status'] != 8:
        return
    if ble.active() == False:
        print('-- fcheck ble')
        ble.active(True)
        # fble_recover()
    if station.isconnected() == False or station.ifconfig()[0] == '0.0.0.0':
        print('-- fcheck wifi')
        station.connect()
        # machine.reset()
    # this is in ms, most other calculations for time are in seconds
    # if mqtth.last_cpacket - mqtth.last_ping > 10*60*1000:
    #    print('-- fcheck mqtt')
    #    fmqtt_recover()
    if time.ticks_ms() - mqtth.last_cpacket > 5 * 60 * 1000:
        print('-- fcheck mqtt')
        fmqtt_recover()
    #global vglob
    #global vglob_list
    #vglob['status'] = 1
    # ### remove addresses older than 21 minutes (was 2 hours)
    #last_contact = 9999
    for iii in vglob_list.items():
        if time.time() - iii[1][3] > 21 * 60:
            vglob_list.pop(iii[0])
    # check for the time of the freshest last contact
    #    if iii[1][3] < last_contact:
    #        last_contact = iii[1][3]
    # ### if 5 minutes from the last contact, then scan
    # INFO: optimisations for scan scheduling make no sense, start every 5 minutes
    if time.time() - vglob['timescan'] > 2 * 60:
        ### if all handles are null, start scan
        if [aaa[2] for aaa in vwork_list.values()] == [None] * len(vwork_list):
            vglob['timescan'] = time.time()
            ble.gap_scan(40 * 1000, 50000, 30000, 1)
    # wait to be nice
    # time.sleep(1)
    # ### when no job done in last 15 mintes, then clean job variable and reconnect mqtt
    # if time.time() - vglob['time'] > 15 * 60:
        # if no job done, then maybe mqtt broken
        # fble_recover()
    #    fmqtt_recover()
    # if len(vglob_list) == 0:
        # if list empty, then reset ble
    #    fble_recover()
    #    fmqtt_recover()
    gc.collect()
    #vglob['status'] = 8
    #print('-- fcheck done')
    return

#-####
#-####
#-####


def fmqtt_discover():
    # discovery topic should be retained
    #print("publishing mqtt autodiscovery")
    #topic_out = 'esp/sensor/sensor' + str(vglob['addr'][9:17].replace(":","")) + '/state'
    for hhh in vwork_status:
        time.sleep(1)
        if (hhh[0:8] == '4C:65:A8' or hhh[0:8] == 'A4:C1:38'):
            #html_in += str(vvv) + "\n"
            mac = str(hhh[9:17].replace(":", ""))
            topict = 'homeassistant/sensor/Mijia' + mac + 'Temp/config'
            devicet = '{"device_class": "temperature", "name": "Mijia ' + mac + ' Temperature", "state_topic": "esp/sensor/sensor' + mac + \
                '/state", "unit_of_measurement": "°C", "value_template": "{{ value_json.temp }}", "uniq_id": "' + \
                mac + '_T", "dev": { "ids": [ "' + mac + '" ], "name":"Mijia ' + mac + '" } }'
            mqtth.publish(topict, bytes(devicet, 'ascii'), True)
            topich = 'homeassistant/sensor/Mijia' + mac + 'Hum/config'
            deviceh = '{"device_class": "humidity", "name": "Mijia ' + mac + ' Humidity", "state_topic": "esp/sensor/sensor' + mac + \
                '/state", "unit_of_measurement": "%", "value_template": "{{ value_json.hum }}", "uniq_id": "' + \
                mac + '_H", "dev": { "ids": [ "' + mac + '" ], "name":"Mijia ' + mac + '" } }'
            mqtth.publish(topich, bytes(deviceh, 'ascii'), True)
            # add True at the end to retain or retain=True
    gc.collect()
    return

#  "~": "homeassistant/light/kitchen",
#topicc = 'homeassistant/climate/Eq3' + mac + 'Clim/config'
# devicec = '{
#  "name":"Eq3' + mac + 'Clim",
#  "mode_cmd_t":"homeassistant/climate/climate' + mac + '/thermostatModeCmd",
#  "mode_stat_t":"homeassistant/climate/climate' + mac + '/state",
#  "mode_stat_tpl":"",
#  "temp_cmd_t":"homeassistant/climate/climate' + mac + '/targetTempCmd",
#  "temp_stat_t":"homeassistant/climate/climate' + mac + '/state",
#  "temp_stat_tpl":"",
#  "curr_temp_t":"homeassistant/climate/climate' + mac + '/state",
#  "curr_temp_tpl":"",
#  "min_temp":"12",
#  "max_temp":"28",
#  "temp_step":"0.5",
#  "modes":["off", "manual"]
# }'

#-####
#-####
#-####


def fble_recover():
    time.sleep(1)
    global vglob
    vglob['status'] = 1
    #try:
    #    ble.gap_disconnect(vglob['handle'])
    #except:
    #    pass
    #
    try:
        ble.active(0)
        time.sleep(2)
        ble.active(1)
        time.sleep(2)
    except:
        pass
    vglob['timework'] = time.time()
    vglob['time'] = time.time()
    vglob['status'] = 8
    vglob['result'] = 0
    vglob['addr'] = ''
    vglob['work'] = ''
    gc.collect()
    return

#-####
#-####
#-####


def fmqtt_recover():
    print("- f mqtt recover")
    vglob['status'] = 1
    mqtth.keepalive = 180
    time.sleep(0.5)
    mqtth.connect()
    time.sleep(0.5)
    mqtth.set_callback(fmqtt_irq)
    time.sleep(0.5)
    mqtth.subscribe(config2['mqtt_eq3_in'])
    gc.collect()
    vglob['status'] = 8
    return

#-####
#-####
#-####


async def fmqtt_recovera():
    print("- f mqtt recovera")
    await mqtth.connect()
    await asyncio.sleep(1)
    await mqtth.subscribe(config2['mqtt_eq3_in'])
    gc.collect()
    return

#-####
#-####
#-####


def fschedule(var):
    print("- f schedule")
    # give time for the main function to finish
    #time.sleep(1)
    if not config2['loop']:
        return
    global vwork
    # fclean(1)
    # time.sleep(2)
    # add timers, or last run
    vwork['0'] = 'scan'
    # add schedule for eq3 querying
    # add schedule for mijia querying
    # add schedule for hardware thermometer testing, but this can be queried every time
    # split "purging" cleaning and restart work
    gc.collect()
    return

#-####
#-####
#-####


async def fschedulea(var):
    global vwork
    print("- f schedulea")
    # await fclean(1)
    # await asyncio.sleep(2)
    # add timers, or last run
    vwork['0'] = 'scan'
    # add schedule for eq3 querying
    # add schedule for mijia querying
    # add schedule for hardware thermometer testing, but this can be queried every time
    # split "purging" cleaning and restart work
    gc.collect()
    return

#-####
#-####
# -#### connect interrupts
ble.irq(fble_irq)

# -#### mqtt
# -#### this is moved to boot
#mqtth = umqtt.MQTTClient(config2['mqtt_usr'], config2['mqtt_srv'], user=config2['mqtt_usr'], password=config2['mqtt_usr'], port=1883)
# mqtth.set_callback(fmqtt_irq)
fmqtt_recover()

#-####
#-####
# -#### threads
#loopwebthread = _thread.start_new_thread(loop_web, ())


def fstart_server():
    async_loop = asyncio.get_event_loop()
    vserver = asyncio.start_server(loop_web, "0.0.0.0", 80)
    async_loop.create_task(vserver)
    async_loop.run_forever()

#-####
#-####
#-####
thread_web = _thread.start_new_thread(fstart_server, ())

# -#### timers
# -#### scan every x minutes
# quic scan could be done every 5 min
# scan can be added by automatic timer, or mqtt, or web
#timer_schedule.init(period=(10 * 60 * 1000), callback=fschedule)
# ### work every 5 seconds
# maybe lower to 4 seconds ?
# this is ms
#timer_work.init(period=(5 * 1000), callback=fget_work)
timer_work.init(period=(3 * 1000), callback=fworker)
# ### clean every 1 minutes
timer_check.init(period=(1 * 60 * 1000), callback=fcheck)

#-####
#-####
# -#### first scan, longer

fble_scan(0)

# gc.collect()
#-###
