# ###

# whitelist here
# blacklist here

# cleaning up names
#re.sub('\s\W+', '', aaa)
#re.sub('(\W|\-)+', '', list(vglob_list.values())[7][2])
#bytes((x for x in a if x >= 0x20 and x < 127))

# get uptime (time.ticks_ms()/1000/60/60/24)
# or set time.time() as a boot time
uptime = time.time()

# ### define global variables
vglob = {}
vglob['addr'] = ''
vglob['handle'] = ''
vglob['status'] = 8  # 8=disconnected
vglob['result'] = 0
vglob['work'] = ''
vglob['data'] = ''
vglob['time'] = time.time()

vglob_list = {}
# ### work list
vwork = OrderedDict()

vwork_status = {}
# ### data
#vmijia_data = [0, 0]

#import random
# random.choice([1,2,3])

# ### define results
# removed

# ### definitions

# def localtime(  ):


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

# ### decode addres in a readable format


def fdecode_addr(addr):
    result = []
    for iii in addr:
        result.append('{:0>2}'.format(str(hex(iii).split('x')[1])))
    return str((':').join(result)).upper()

# ### pretty list print


def fprint(cmd='show'):
    global vglob_list
    ret = ""
    for iii in vglob_list.items():
        # if cmd == 'clean' and time.time() - iii[1][3] > 60*60: # now 1 hour instead of 2
        #   vglob_list.pop(iii[0])
        ret += str(iii[0]) + " " + '{: >{w}}'.format(str(time.time() - iii[1][3]), w=5) + " " + str(iii[1][1]) + " " + str(iii[1][2]) + "\n"
    if cmd == 'show':
        print(ret)
    if cmd == 'get':
        return ret

# ### main worker


def fble_write(addr, data1, data2=''):
    global vglob_list
    global vglob
    global vwork
    # ### main loop
    # ### try connection 20 times, if succesful stop the loop
    for iii in range(10):
        #print('=== log ===', vglob)
        # ### if status 8, disconnected, then try to connect
        if iii == 9:
            vglob['result'] = 0
            vglob['status'] = 8
            vwork[vglob['addr']] = vglob['work']
            break
        elif vglob['status'] == 8:
            try:
                ble.gap_connect(0, vglob_list[addr][0])
            except Exception as e:
                print('exc:', e)
                # break
                continue
            # ### if connection fails, try again, so no break but continue, as status 8 is expected
            finally:
                time.sleep(2)
        # ### if connection goes well and status is 7, then work
        # elif vglob['addr'] != '' and vglob['status'] == 7:
        # ### result 2, if connected then write
        elif vglob['result'] == 2 and vglob['status'] == 7:
            # time.sleep(1)
            # ### check temp value
            if addr[0:8] == '4C:65:A8' and data1 == 'gettemp':
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
            else:
                # ### when bad variables, end by simulating status disconnected
                vglob['status'] = 8
                # continue
                break
            # ### if no issue with above
            # ### and variables cleaned, try to write
            try:
                ble.gattc_write(vglob['handle'], data1, data2, 1)
            except Exception as e:
                print('exc:', e)
                # ### if error with writing, simulate disconnect and result error 8
                vglob['result'] = 8
                # ### disconnect if needed
                vglob['status'] = 18
                # break
            finally:
                #
                time.sleep(2)
        elif vglob['status'] == 17:
            # ### if status 17, written, but not 18, response, then wait
            # time.sleep(1)
            #
            pass
        elif vglob['status'] == 18:
            # ### if status 18, success write and response, then break the loop and disconnect
            # ### here, work from work list can be removed
            break
            # return
        # ### this will happen, if non of the above
        # so sleep before next try
        time.sleep(1)
        # ###
    # ### if loop ended or break then try to disconnect, set status to disconnected
    try:
        ble.gap_disconnect(vglob['handle'])
    except:
        vglob['status'] == 8
    # _thread.exit()
    return

# ### main function to handle irqs from mqtt


def fble_irq(event, data):
    global vglob_list
    global vglob
    global vwebpage
    global vwork_status
    #global vmijia_data
    # ### get event variable and publish global so other threads react as needed
    vglob['status'] = event
    # if event == 17: # 17
    #    print('--', event, '--', vglob['addr'])
    # ###
    if event == 5:  # _IRQ_SCAN_RESULT
        # ### scan results, and publish gathered addresses in vglob_list
        addr_type, addr, adv_type, rssi, adv_data = data
        #vglob_list[str(fdecode_addr(addr))] = [bytes(addr), rssi, bytes(adv_data)[2:14], time.time()]
        #re.sub('(\\\\x..|\ )', '', str())
        # special case for presence sensors with FF:FF addresses
        if bytes(addr)[0:2] == b'\xff\xff' and adv_type == 0:
            adv_type = 4
            # this has to be like this, to pass through the cleaner later
            adv_data = b'__Tracker'
        # only full detections, with names, so adv_type == 4
        if adv_type == 4:
            vglob_list[str(fdecode_addr(addr))] = [bytes(addr), rssi, bytes((x for x in bytes(adv_data)[2:20] if x >= 0x20 and x < 127)).decode("ascii").strip(), time.time()]
            #print( data, bytes((x for x in bytes(adv_data)[2:20] if x >= 0x20 and x < 127)).decode("ascii").strip() )
        else:
            return
    elif event == 6:  # _IRQ_SCAN_DONE
        vwebpage = fwebpage()
        # ### scan done and cleanup, reseting variables as needed
        vglob['status'] = 8
        vglob['result'] = 0
        gc.collect()
    elif event == 7:  # _IRQ_PERIPHERAL_CONNECT
        # ### connected 7
        vglob['handle'], addr_type, addr = data
        #vglob['addr'] = str(fdecode_addr(addr))
        #vmijia_data = [0, 0]
        vglob['result'] = 2
        vglob_list[vglob['addr']][3] = time.time()
    elif event == 8:  # _IRQ_PERIPHERAL_DISCONNECT
        # ### disconnected 8, do actions
        # for mijia
        msg_out = ''
        topic_out = ''
        if vglob['addr'][0:8] == '4C:65:A8' and vglob['result'] == 6:
            # ### only if result 3 = if notify succesful, then publish
            # ### create mqtt
            datas = str(bytes(vglob['data']), 'ascii').strip('\x00').strip().replace(' ', '=').split('=')
            msg_out = '{"trv":"' + vglob['addr'] + '","temp":"' + str(datas[1]) + '","hum":"' + str(datas[3]) + '"}'
            # the last part of mac vglob['addr'][9:17].replace(":","")
            #topic_out = config2['mqtt_mijia_out']
            topic_out = 'esp/sensor/sensor' + str(vglob['addr'][9:17].replace(":", "")) + '/state'
        if vglob['addr'][0:8] == '00:1A:22' and vglob['result'] == 6:
            # ### create mqtt
            datas = list(bytearray(vglob['data']))
            msg_out = '{"trv":"' + vglob['addr'] + '","temp":"' + str(float(datas[5]) / 2) + '","mode":"manual"}'
            topic_out = config2['mqtt_eq3_out']
            #mqtth.publish(config2['mqtt_eq3_out'], bytes(msg_out, 'ascii'))
        # ### for eq3
        # if vglob['addr'] != '' and vglob['result'] == 4:
        # ### if connection or writing not succesful, then re-add
        if msg_out != '':
            #print('=== msg ===', msg_out)
            mqtth.publish(topic_out, bytes(msg_out, 'ascii'))
            vwork_status[vglob['addr']] = msg_out
            # recache page only if something changed/sent
            vwebpage = fwebpage()
            # sleep for jobs to finish
            time.sleep(1)
        # ### if res 8, error, then add work again
        if vglob['result'] == 8:
            vwork[vglob['addr']] = vglob['work']
            vglob['addr'] = ''
            vglob['work'] = ''
        # ### not needed
        # if vglob['addr'] != '':
        #    vglob['result'] = 0
        # ### end and cleanup
        # ### do not cleanup completely if connection loop is running
        # ### to disallow new work to be taken
        if vglob['result'] != 1:
            vglob['result'] = 0
        vglob['data'] = ''
        vglob['handle'] = ''
        #vglob['addr'] = ''
        #vglob['work'] = ''
        gc.collect()
    elif event == 17:  # 17 _IRQ_GATTC_WRITE_DONE
        # ### write to device
        vglob['handle'], value_handle, status = data
        vglob['result'] = 4
    elif event == 18:  # _IRQ_GATTC_NOTIFY
        # ### getting ble notification irq
        vglob['handle'], value_handle, notify_data = data
        # ### for mijia
        vglob['data'] = notify_data
        # if vglob['addr'][0:8] == '4C:65:A8':
        #
        # ### for eq3
        # if vglob['addr'][0:8] == '00:1A:22':
        #    aaa = list(bytearray(notify_data))
        #    # send mqtt
        #    msg_out = '{"trv":"' + vglob['addr'] + '","temp":"' + str(float(aaa[5]) / 2) + '","mode":"manual"}'
        #    # print(msg_out)
        #    mqtth.publish(config2['mqtt_eq3_out'], bytes(msg_out, 'ascii'))
        # ### set result to 3, which means success notify
        vglob['result'] = 6
    else:
        print('else')
    return


def fble_scan(var):
    # ### starting scanning thread and setting variables
    vglob['status'] = 1
    vglob['result'] = 1
    vglob['work'] = 'scan'
    #print('start scan')
    # ### starting scans in thread, not to block console, etc.
    #ble.gap_scan(10000, 40000, 20000, 1)
    # sleep for jobs to finish
    # time.sleep(1)
    if str(var) == '0':
        # 40 seconds as a full scan is more than necessary
        _thread.start_new_thread(ble.gap_scan, (30 * 1000, 30000, 30000, 1))
    else:
        # was 15 seconds, is 20
        _thread.start_new_thread(ble.gap_scan, (10 * 1000, 30000, 30000, 1))
    time.sleep(1)
    return


def fwork(var):
    # ### this a worker controller
    # ### it checks for messages and starts the worker thread if needed
    global vglob
    #global vwork
    global vwork
    #global vwebpage
    # ### fix the connection if needed
    # ### wlan fixes itself
    # mqtth.ping()
    # removed, to remove the robust2 dependency
    # if mqtth.is_conn_issue():
    #    # ### reconnect
    #    if mqtth.reconnect():
    #        mqtth.resubscribe()
    #    # stop function
    #    return
    if vglob['status'] == 5:
        # if scan is running, skip round
        mqtth.ping()
        time.sleep(1)
        return
    # ### trigger checking for messages, and wait for messages to arrive
    mqtth.check_msg()
    # time.sleep(1)
    # ### expecting non 0 worklist, status 8 disconnected, and empty addr
    if len(vwork) > 0 and vglob['status'] == 8 and vglob['result'] == 0:
        # ### reset the last work timer
        vglob['time'] = time.time()
        # ### get work and address
        workaddr = list(vwork.keys())[0]
        work = vwork.pop(workaddr)
        # ### tests
        if len(work) == 0:
            # stop function
            return
        elif work == 'scan':
            fble_scan(0)
            return
        elif work[0] == '{':
            print('json')
            # parse json ?
        else:
            #worka = []
            #worka = str(msg).strip().split(' ', 1)
            #vglob['addr'] = worka[0]
            #vglob['work'] = worka[1]
            # ### got correct work, setting variables
            vglob['addr'] = workaddr
            vglob['work'] = work
            vglob['result'] = 1
            worka = str(work).strip().split(' ')
            for iii in range(max(0, 2 - len(worka))):
                worka.append('')
        # "offsetTemp":"-3.0", "valve":"79% open",
        # "mode":"manual","boost":"inactive","window":"closed","state":"unlocked","battery":"GOOD"}
        # sleep for jobs to finish

        # start thread
        _thread.start_new_thread(fble_write, (workaddr, worka[0], worka[1]))
        time.sleep(1)
    # not needed everywhere
    # gc.collect()
    return


def fmqtt_irq(topic, msg, aaa=False, bbb=False):
    # ### if the check msg is started, then this function is triggered
    global vwork
    if type(msg) is bytes:
        msg = msg.decode()
    if type(topic) is bytes:
        topic = topic.decode()
    #print('- irq -', msg)
    # ### split address and command
    worka = str(msg).strip().split(' ', 1)
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
    elif worka[0] not in vglob_list.keys():
        print('address not available')
        # return
    # ### if addres in the list, of correct lenght, and command lenght between 5 and 14 letters
    elif len(worka[0]) == 17 and len(worka[1]) > 5 and len(worka[1]) < 14:
        # do not overwrite if work task is not 'manual', else add if not in the list
        if worka[0] not in vwork.keys() or worka[1] != 'manual':
            vwork[worka[0]] = worka[1]
            return
    # ### otherwise, bad message, syntax, etc
    else:
        print('bad message')
    return

#####
#####
#####


def fclean(var):
    # ### yes, cleaning
    global vglob
    global vglob_list
    # ### remove addresses older than 1 hour (was 2 hours)
    # wait to be nice
    time.sleep(1)
    for iii in vglob_list.items():
        if time.time() - iii[1][3] > 60 * 60 * 1:
            vglob_list.pop(iii[0])
    # ### when no job done in last 20 mintes, then clean job variable and reconnect mqtt
    if time.time() - vglob['time'] > 20 * 60:
        vglob['time'] = time.time()
        vglob['status'] = 8
        vglob['result'] = 0
        vglob['addr'] = ''
        vglob['work'] = ''
        # mqtth.reconnect()
        # mqtth.resubscribe()
        fmqtt_recover()
    gc.collect()
    return

#-###
#-###
# -### webpage generating function


def fwebpage():
    html_in = ""
    for vvv in vwork_status.items():
        html_in += str(vvv) + "\n"
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
Boot: """ + str(fnow(uptime)) + """<br/>
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
<a href="/purge">Remove old devices from list</a><br/>
<a href="/reset">Reset</a>
<h2>List of contacted devices</h2>
<pre>
""" + str(html_in) + """
</pre>
<h2>Other</h2>
</body>
</html>"""
    # is this needed here ?
    # gc.collect()
    # returning bytes, does not save memory
    return(str(html))

#-###
#-###
# -### webpage socket loop function


def loop_web():
    # creating sockets etc
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # SO_REUSEPORT, whatever this is good for ?
    # from 300 to 60
    s.settimeout(120)
    # s.setblocking(1) # works with both
    s.setblocking(1)
    s.bind(('', 80))
    # how many connections in parallel
    s.listen(4)
    ###
    #webpage = ""
    while config2['loop']:
        # try to listen for connection
        time.sleep(1)
        try:
            conn, addr = s.accept()
            timer1 = time.ticks_ms()
            # this is maybe not needed ?
            conn.settimeout(10)
            # this is fast
            # find for requests was VERY slow
            # requestfull = conn.recv(64).decode()  # [4:-6]
            #request = requestfull.split('\r')[0].split(' ')[1].split('?')[0]
            requestfull = conn.recv(64).decode().split('\r')[0].split(' ')[1].split('?')  # [4:-6]
            request = requestfull[0]
            requestval = ""
            if len(requestfull) == 2:
                requestval = requestfull[1]
            timer2 = time.ticks_ms()
            #####
            #####
            if request == "/":
                header = """HTTP/1.1 200 OK
Content-Type: text/html
Server-Timing: text;dur=""" + str(time.ticks_ms() - timer2) + """, req;dur=""" + str(timer2 - timer1) + """
Content-Length: """ + str(len(vwebpage)) + """
Connection: close
"""
                conn.sendall(header + "\r\n" + vwebpage)
                # continue
            #####
            #####
            elif request == "/list":
                webpagea = "MAC, last seen, rssi, name\n" + str(fprint('get'))
                header = """HTTP/1.1 200 OK
Content-Type: text/plain
Content-Length: """ + str(len(webpagea)) + """
Connection: close
"""
                conn.sendall(header + "\r\n" + webpagea)
                # conn.close()
            #####
            #####
            elif request == "/deldo":
                header = """HTTP/1.1 302 Found
Content-Length: 0
Location: /info
Connection: close

"""
                # Connection: close
                if requestval != "":
                    try:
                        os.remove(requestval)
                    except:
                        pass
                conn.sendall(header)
            #####
            #####
            elif request == "/info":
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
                webpagea = """Directory listing on ESP. By writing /deldo?filename, files can be removed (dangerous).
Files with _old are safety copies after OTA, can be safely removed.
To disable webrepl, delete webrepl_cfg.py and reboot device.

Dir: """ + str(os.listdir()) + """

Current work: """ + str(vglob) + """
Scheduled work: """ + str(vwork) + """

Reset cause: """ + str(reset_cause) + """
Free RAM (over 40k is fine, 70k is good): """ + str(gc.mem_free()) + """."""

                header = """HTTP/1.1 200 OK
Content-Type: text/plain
Content-Length: """ + str(len(webpagea)) + """
Connection: close
"""
                conn.sendall(header + "\r\n" + webpagea)
                # conn.close()
            #####
            #####
            elif request == "/webrepl":
                #requestval = requestfull.split('\r')[0].split(' ')[1].split('?')[1]
                #webpagea = str(requestval) + "\n" + str(os.listdir())
                try:
                    fff = open('webrepl_cfg.py', 'w')
                    fff.write("PASS = \'1234\'\n")
                    fff.close()
                except:
                    pass
                header = """HTTP/1.1 302 Found
Content-Length: 0
Location: /reset
Connection: close

"""
                conn.sendall(header + "\r\n" + webpagea)
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
                conn.sendall(header + "\r\n" + webpagea)
                # machine.reset()
            elif request == "/mqttauto":
                fmqtt_discover()
                header = """HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 30
Connection: close

MQTT Autodiscovery published.
"""
                conn.sendall(header + "\r\n" + webpagea)
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
                conn.sendall(header + "\r\n" + webpagea)
                # machine.reset()
            #####
            #####
            elif request == "/ota":
                # method="post"
                webpagea = """<pre>Usually upload main.py file. Sometimes boot.py file. Binary files do not work yet.</pre>
<br/>
<form action="otado" name="upload" method="post" enctype="multipart/form-data">
  <input type="file" name="filename">
  <input type="submit">
</form>"""
                header = """HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: """ + str(len(webpagea)) + """
Connection: close
"""
                conn.sendall(header + "\r\n" + webpagea)
            #####
            #####
            elif request == "/otado":
                webpagea = ""
                gc.collect()
                # s.setblocking(0)
                header = """HTTP/1.1 302 Found
Content-Length: 0
Location: /reset
Connection: close

"""
                # =
                headerin = conn.recv(500).decode()
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
                    dataaa = conn.recv(bufflen).decode().split('\r\n--' + boundaryin, 2)
                    splita = len(dataaa)
                    #print( splita )
                    #filein += dataaa
                    if begin == 0 and splita == 3:
                        #print( "= short" )
                        # short
                        conn.sendall(header)
                        conn.close()
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
                        conn.sendall(header)
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
                dataaa = ""
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
                conn.sendall(header)
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
                conn.sendall(header)
                # conn.close()
                # time.sleep(2) # no sleep here ;)
                machine.reset()
                # time.sleep(1)
            #####
            #####
            else:
                header = """HTTP/1.0 404 Not Found
Content-Type: text/plain
Content-Length: 23
Server-Timing: text;dur=""" + str(time.ticks_ms() - timer2) + """, req;dur=""" + str(timer2 - timer1) + """
Connection: close

404 No page like this.
"""
                conn.sendall(header)
                # conn.close()
            # END IF
            # conn.close() # close or not ?
            # whatever
        except Exception as e:
            print('exc:', e)
            # timeout message hidden
            pass
        # END TRY
        # cleaning up
        requestfull = ""
        header = ""
        webpagea = ""
        #vwebpage = ""
        gc.collect()
        # time.sleep(1)
    # END WHILE
    # the function ends if loop fails
    # so this is not good
    # maybe reboot here ?
    time.sleep(60)  # first wait 1 minute, just in case, for webrepl etc
    if config2['loop']:
        machine.reset()

# ###


def fmqtt_discover():
    #print("publishing mqtt autodiscovery")
    #topic_out = 'esp/sensor/sensor' + str(vglob['addr'][9:17].replace(":","")) + '/state'
    for hhh in vwork_status:
        time.sleep(1)
        if hhh[0:8] == '4C:65:A8':
            #html_in += str(vvv) + "\n"
            mac = str(hhh[9:17].replace(":", ""))
            topict = 'homeassistant/sensor/Mijia' + mac + 'Temp/config'
            devicet = '{"device_class": "temperature", "name": "Mijia ' + mac + ' Temperature", "state_topic": "esp/sensor/sensor' + mac + \
                '/state", "unit_of_measurement": "°C", "value_template": "{{ value_json.temp }}", "uniq_id": "' + \
                mac + '_T", "dev": { "ids": [ "' + mac + '" ], "name":"Mijia ' + mac + '" } }'
            mqtth.publish(topict, bytes(devicet, 'ascii'))
            topich = 'homeassistant/sensor/Mijia' + mac + 'Hum/config'
            deviceh = '{"device_class": "humidity", "name": "Mijia ' + mac + ' Humidity", "state_topic": "esp/sensor/sensor' + mac + \
                '/state", "unit_of_measurement": "%", "value_template": "{{ value_json.hum }}", "uniq_id": "' + \
                mac + '_H", "dev": { "ids": [ "' + mac + '" ], "name":"Mijia ' + mac + '" } }'
            mqtth.publish(topich, bytes(deviceh, 'ascii'))
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

####

# ###


def fmqtt_recover():
    mqtth.connect()
    time.sleep(1)
    mqtth.subscribe(config2['mqtt_eq3_in'])
    return

# ###


def fschedule(var):
    fclean(1)
    time.sleep(1)
    # add timers, or last run
    vwork['0'] = 'scan'
    # add schedule for eq3 querying
    # add schedule for mijia querying
    # add schedule for hardware thermometer testing, but this can be queried every time
    # split "purging" cleaning and restart work
    return


# ### connect interrupts
ble.irq(fble_irq)

# ### mqtt
mqtth = umqtt.MQTTClient(config2['mqtt_usr'], config2['mqtt_srv'], user=config2['mqtt_usr'], password=config2['mqtt_usr'], port=1883)
mqtth.set_callback(fmqtt_irq)
fmqtt_recover()

#mqtth.keepalive = 1

vwebpage = fwebpage()
# ### threads
loopwebthread = _thread.start_new_thread(loop_web, ())

# ### timers
# ### scan every 10 minutes
# scan can be added by automatic timer, or mqtt, or web
timer_schedule.init(period=(10 * 60 * 1000), callback=fschedule)
# ### work every 5 seconds
timer_work.init(period=(5 * 1000), callback=fwork)
# ### clean every 50 minutes
#timer_clean.init(period=(1 * 50 * 60 * 1000), callback=fclean)

# ### first scan, longer
fble_scan(0)

#-###
