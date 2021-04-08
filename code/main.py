# ### v 0.24

# whitelist here
# blacklist here

# cleaning up names
#re.sub('\s\W+', '', aaa)
#re.sub('(\W|\-)+', '', list(vglob_list.values())[7][2])

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
# ### data
#vmijia_data = [0, 0]

#import random
# random.choice([1,2,3])

# ### define results
# removed

# ### definitions

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
       if cmd == 'clean' and time.time() - iii[1][3] > 60*60: # now 1 hour instead of 2
          vglob_list.pop(iii[0])
       ret += str(iii[0])+" "+ '{: >{w}}'.format(str(time.time() - iii[1][3]), w=5) +" "+ str(iii[1][1]) +" "+ str(iii[1][2]) +"\n"
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
            except:
                # break
                continue
            # ### if connection fails, try again, so no break but continue, as status 8 is expected
            time.sleep(2)
        # ### if connection goes well and status is 7, then work
        # elif vglob['addr'] != '' and vglob['status'] == 7:
        # ### result 2, if connected then write
        elif vglob['result'] == 2 and vglob['status'] == 7:
            time.sleep(1)
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
            except:
                # ### if error with writing, simulate disconnect and result error 8
                vglob['result'] = 8
                # ### disconnect if needed
                vglob['status'] = 18
                #break
            time.sleep(2)
        elif vglob['status'] == 17:
            # ### if status 17, written, but not 18, response, then wait
            time.sleep(1)
        elif vglob['status'] == 18:
            # ### if status 18, success write and response, then break the loo and disconnect
            # ### here, work from work list can be removed
            break
            ### return
        # ### this will happen, if non of the above
        # ###
    # ### if loop ended or break then try to disconnect, set status to disconnected
    try:
        ble.gap_disconnect(vglob['handle'])
    except:
        vglob['status'] == 8

# ### main function to handle irqs from mqtt
def fble_irq(event, data):
    global vglob_list
    global vglob
    global webpagemain
    #global vmijia_data
    # ### get event variable and publish global so other threads react as needed
    vglob['status'] = event
    #if event == 17: # 17
    #    print('--', event, '--', vglob['addr'])
    # ###
    if event == 5: #_IRQ_SCAN_RESULT
        # ### scan results, and publish gathered addresses in vglob_list
        addr_type, addr, adv_type, rssi, adv_data = data
        #vglob_list[str(fdecode_addr(addr))] = [bytes(addr), rssi, bytes(adv_data)[2:14], time.time()]
        vglob_list[str(fdecode_addr(addr))] = [bytes(addr), rssi, re.sub('(\\\\x..|\ )', '', str(bytes(adv_data)[2:20])), time.time()]
    elif event == 6: #_IRQ_SCAN_DONE
        webpagemain = web_page()
        # ### scan done and cleanup, reseting variables as needed
        vglob['status'] = 8
        vglob['result'] = 0
        gc.collect()
    elif event == 7: #_IRQ_PERIPHERAL_CONNECT
        # ### connected 7
        vglob['handle'], addr_type, addr = data
        #vglob['addr'] = str(fdecode_addr(addr))
        #vmijia_data = [0, 0]
        vglob['result'] = 2
        vglob_list[vglob['addr']][3] = time.time()
    elif event == 8: #_IRQ_PERIPHERAL_DISCONNECT
        webpagemain = web_page()
        # ### disconnected 8, do actions
        # for mijia
        msg_out = ''
        if vglob['addr'][0:8] == '4C:65:A8' and vglob['result'] == 6:
            # ### only if result 3 = if notify succesful, then publish
            # ### create mqtt
            datas = str(bytes(vglob['data']), 'ascii').strip('\x00').strip().replace(' ', '=').split('=')
            msg_out = '{"trv":"' + vglob['addr'] + '","temp":"' + str(datas[1]) + '","hum":"' + str(datas[3]) + '"}'
            topic_out = config2['mqtt_mijia_out']
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
    elif event == 17: #17 _IRQ_GATTC_WRITE_DONE
        # ### write to device
        vglob['handle'], value_handle, status = data
        vglob['result'] = 4
    elif event == 18: #_IRQ_GATTC_NOTIFY
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
    gc.collect()
    return


def fble_scan(var):
    # ### starting scanning thread and setting variables
    vglob['status'] = 1
    vglob['result'] = 1
    vglob['work'] = 'scan'
    print('start scan')
    # ### starting scans in thread, not to block console, etc.
    #ble.gap_scan(10000, 40000, 20000, 1)
    if str(var) == '0':
        _thread.start_new_thread(ble.gap_scan, (40000, 30000, 30000, 1))
    else:
        _thread.start_new_thread(ble.gap_scan, (15000, 30000, 30000, 1))
    return


def fwork(var):
    # ### this a worker controller, it checks for messages and starts the worker thread if needed
    global vglob
    #global vwork
    global vwork
    #global webpagemain
    # ### fix the connection if needed
    # ### wlan fixes itself
    if mqtth.is_conn_issue():
       # ### reconnect
       if mqtth.reconnect():
          mqtth.resubscribe()
       # stop function
       return
    # ### trigger checking for messages, and wait for messages to arrive
    mqtth.check_msg()
    time.sleep(1)
    # ### expecting non 0 worklist, status 8 disconnected, and empty addr
    if len(vwork) > 0 and vglob['status'] == 8 and vglob['result'] == 0:
        # ### reset the last work timer
        vglob['time'] = time.time()
        # ### get work and address
        workaddr = list(vwork.keys())[0]
        work = vwork.pop(workaddr)
        ### generate page
        #webpagemain = web_page()
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
        ### start thread
        _thread.start_new_thread(fble_write, (workaddr, worka[0], worka[1]))
    gc.collect()
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
            time.sleep(5)
    # ### if above not true and address not in the list, then skip
    # ### whitelist could be added
    elif worka[0] not in vglob_list.keys():
        print('address not available')
        return
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

def fclean(var):
    # ### yes, cleaning
    global vglob
    global vglob_list
    # ### remove addresses older than 2 hours
    for iii in vglob_list.items():
        if time.time() - iii[1][3] > 7200:
           vglob_list.pop(iii[0])
    # ### when no job done in last 20 mintes, then clean job variable and reconnect mqtt
    if time.time() - vglob['time'] > 1200:
        vglob['time'] = time.time()
        vglob['status'] = 8
        vglob['result'] = 0
        vglob['addr'] = ''
        vglob['work'] = ''
        mqtth.reconnect()
        mqtth.resubscribe()
    gc.collect()

#-###
#-###
#-### webpage generating function
def web_page():
  #html_in = ""
  #generate table

  #generate rest of html
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
<h2>Work</h2>
Last: """ + str( vglob ) + """
<h2>System</h2>
Update: """ + str( time.time() ) + """<br/>
Boot: """ + str( uptime ) + """<br/>
Location: """ + str( config2['mqtt_usr'] ) +"""<br/>
IP: """ + str( station.ifconfig()[0] ) +"""<br/>
Links: <a href="/hits.txt">Hits</a>, <a href="/countsnd">Counts daily</a>, <a href="/reset">Reset</a>
<h2>List</h2>
<pre>
""" + str( fprint('get') ) + """
</pre>
<h2>Other</h2>
</body>
</html>"""
  return( html )

#-###
#-###
#-### webpage socket loop function
def loop_web():
  ### creating sockets etc
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
  #SO_REUSEPORT, whatever this is good for ?
  # from 300 to 60
  s.settimeout(120)
  #s.setblocking(1) # works with both
  s.bind(('', 80))
  # how many connections in parallel
  s.listen(10)
  ###
  #webpage = ""
  while config2['loop']:
    # try to listen for connection
    try:
      conn, addr = s.accept()
      timer1 = time.ticks_ms()
      conn.settimeout(20)
      # this is fast
      # find for requests was VERY slow
      request = conn.recv(64).decode().split('\r')[0][5:-9] #[4:-6]
      #print(request)
      timer2 = time.ticks_ms()
      ###
      if request == "":
         #webpage = webpagemain
         header = """HTTP/1.1 200 OK
Content-Type: text/html
Server-Timing: text;dur=""" + str( time.ticks_ms() - timer2 ) + """, req;dur=""" + str( timer2 - timer1 ) + """
Content-Length: """ + str( len(webpagemain) ) + """
Connection: close
"""
         conn.sendall( header + "\r\n" + webpagemain )
         #continue
      ###
      elif request == "reset":
         header = """HTTP/1.1 302 Found
Content-Length: 0
Location: /
Connection: close

"""
         # Connection: close
         conn.sendall( header )
         #conn.close()
         #time.sleep(2) # no sleep here ;)
         machine.reset()
      ###
      else:
         header = """HTTP/1.0 404 Not Found
Content-Type: text/plain
Content-Length: 23
Server-Timing: text;dur=""" + str( time.ticks_ms() - timer2 ) + """, req;dur=""" + str( timer2 - timer1 ) + """
Connection: close

404 No page like this.
"""
         conn.sendall( header )
         #conn.close()
      ### END IF
      #conn.close() # close or not ?
      # whatever
    except Exception as e:
      print( 'Just web loop info:', e )
      pass
    ### END TRY
    # cleaning up
    header = ""
    #webpagemain = ""
    #webpagel = ""
    gc.collect()
  ### END WHILE
  # the function ends if loop fails
  # so this is not good
  # maybe reboot here ?
  sleep(120) # first wait 2 minutes, just in case
  if keep_loop:
     machine.reset()


# ### connect interrupts
ble.irq(fble_irq)

# ### mqtt
mqtth = umqtt.MQTTClient(config2['mqtt_usr'], config2['mqtt_srv'], user=config2['mqtt_usr'], password=config2['mqtt_usr'], port=1883)
mqtth.set_callback(fmqtt_irq)
mqtth.connect()
mqtth.subscribe(config2['mqtt_eq3_in'])
#mqtth.keepalive = 1

webpagemain = web_page()
# ### threads
loopwebthread = _thread.start_new_thread(loop_web, ())

# ### timers
# ### scan every 10 minutes
timer_scan.init(period=(10 * 60 * 1000), callback=fble_scan)
# ### work every 10 seconds
timer_work.init(period=(5 * 1000), callback=fwork)
# ### clean every 1 hour
timer_clean.init(period=(1 * 60 * 60 * 1000), callback=fclean)

# ### first scan

fble_scan(0)

#-###
