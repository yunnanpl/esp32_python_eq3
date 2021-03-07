# ### v 0.20

# whitelist here
# blacklist here

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
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_GATTS_READ_REQUEST = const(4)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_GATTC_SERVICE_RESULT = const(9)
_IRQ_GATTC_SERVICE_DONE = const(10)
_IRQ_GATTC_CHARACTERISTIC_RESULT = const(11)
_IRQ_GATTC_CHARACTERISTIC_DONE = const(12)
_IRQ_GATTC_DESCRIPTOR_RESULT = const(13)
_IRQ_GATTC_DESCRIPTOR_DONE = const(14)
_IRQ_GATTC_READ_RESULT = const(15)
_IRQ_GATTC_READ_DONE = const(16)
_IRQ_GATTC_WRITE_DONE = const(17)
_IRQ_GATTC_NOTIFY = const(18)
_IRQ_GATTC_INDICATE = const(19)
_IRQ_GATTS_INDICATE_DONE = const(20)
_IRQ_MTU_EXCHANGED = const(21)
_IRQ_L2CAP_ACCEPT = const(22)
_IRQ_L2CAP_CONNECT = const(23)
_IRQ_L2CAP_DISCONNECT = const(24)
_IRQ_L2CAP_RECV = const(25)
_IRQ_L2CAP_SEND_READY = const(26)
_IRQ_CONNECTION_UPDATE = const(27)
_IRQ_ENCRYPTION_UPDATE = const(28)
_IRQ_GET_SECRET = const(29)
_IRQ_SET_SECRET = const(30)

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
    for iii in vglob_list.items():
        if cmd == 'clean' and time.time() - iii[1][3] > 7200:
           vglob_list.pop(iii[0])
        print(iii[0], (time.time() - iii[1][3]), iii[1][1], iii[1][2])


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
            # return
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
    #global vmijia_data
    # ### get event variable and publish global so other threads react as needed
    vglob['status'] = event
    #if event == 17: # 17
    #    print('--', event, '--', vglob['addr'])
    # ###
    if event == _IRQ_SCAN_RESULT:
        # ### scan results, and publish gathered addresses in vglob_list
        addr_type, addr, adv_type, rssi, adv_data = data
        vglob_list[str(fdecode_addr(addr))] = [bytes(addr), rssi, bytes(adv_data)[2:14], time.time()]
    elif event == _IRQ_SCAN_DONE:
        # ### scan done and cleanup, reseting variables as needed
        vglob['status'] = 8
        vglob['result'] = 0
        gc.collect()
    elif event == _IRQ_PERIPHERAL_CONNECT:
        # ### connected 7
        vglob['handle'], addr_type, addr = data
        #vglob['addr'] = str(fdecode_addr(addr))
        #vmijia_data = [0, 0]
        vglob['result'] = 2
        vglob_list[vglob['addr']][3] = time.time()
    elif event == _IRQ_PERIPHERAL_DISCONNECT:
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
            print('=== msg ===', msg_out)
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
    elif event == _IRQ_GATTC_WRITE_DONE:
        # ### write to device
        vglob['handle'], value_handle, status = data
        vglob['result'] = 4
    elif event == _IRQ_GATTC_NOTIFY:
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
    # ### fix the connection if needed
    # ### wlan fixes itself
    if mqtth.is_conn_issue():
       # ### reconnect
       if mqtth.reconnect():
          mqtth.resubscribe()
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
        # ### tests
        if len(work) == 0:
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
        _thread.start_new_thread(fble_write, (workaddr, worka[0], worka[1]))
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
    # ### when no job done in last 20 mintes, then clean job variable
    if time.time() - vglob['time'] > 1200:
        vglob['time'] = time.time()
        vglob['status'] = 8
        vglob['result'] = 0
        vglob['addr'] = ''
        vglob['work'] = ''
    gc.collect()

# ### connect interrupts
ble.irq(fble_irq)

# ### mqtt
mqtth = umqtt.MQTTClient(config2['mqtt_usr'], config2['mqtt_srv'], user=config2['mqtt_usr'], password=config2['mqtt_usr'], port=1883)
mqtth.set_callback(fmqtt_irq)
mqtth.connect()
mqtth.subscribe(config2['mqtt_eq3_in'])
#mqtth.keepalive = 1

# ### threads
#loopwebthread = _thread.start_new_thread(loop_web, ())

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
