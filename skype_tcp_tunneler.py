import sys
import time
import traceback
import os
import threading

DBG1 = 0
DBG2 = 0

import im_tcp_tunneler

appsByUser = {}

lock = threading.Lock()

def send_xmpp_message(from_jid, to_jid, txt):
    if 0: print 'send_xmpp_message: %s->%s, %r' % (from_jid, to_jid, txt[0:])
    try:
        with lock:
            if to_jid in appsByUser:
                uapp = appsByUser[to_jid]
            else:
                print 'connect to %s' % to_jid
                uapp = appsByUser[to_jid] = app.Connect(to_jid, WaitConnected=True)
        if DBG1: print 'send: %s: len(data)=%d' % (uapp, len(txt))
        for i in range(5):
            try:
                uapp.write(txt)
            except Skype4Py.SkypeAPIError, e:
                print e, '- trying again'
            else:
                break
    except:
        traceback.print_exc()
im_tcp_tunneler.send_xmpp_message = send_xmpp_message

def get_client_jid():
    return skype.CurrentUser.Handle
im_tcp_tunneler.get_client_jid = get_client_jid

im_tcp_tunneler.setup_tunnels(sys.argv[-1])

if 0: im_tcp_tunneler.data_coding_mode = 'raw'

import Skype4Py

proto = os.environ.get('SKYPE_TCP_TUNNELER_PROTO', None)
if proto: skype = Skype4Py.Skype(Transport=proto)
else:     skype = Skype4Py.Skype()

skype.Attach()

def onApplicationReceiving(app_, streams):
    if app_.Name != app.Name: return False
    while 1:
        ret = False
        for strm in list(streams):
            ret = True
            try:
                data = strm.read()
                if DBG1: print 'received: %s: len(data)=%d' % (strm, len(data))
                if DBG2: print 'received: %s: %r' % (strm, data)
                im_tcp_tunneler.handle_message(strm.PartnerHandle, skype.CurrentUser.Handle, data)
            except:
                traceback.print_exc()
        if 1: break
        if not ret: break
    return ret

print 'your skypename:', skype.CurrentUser.Handle

app = skype.Application('tcp-tunneler-1')
app.Create()
try:
    try:
        print 'app:', app

        keep_running = True

        if 0:
            import code
            def interact():
                code.interact(local=globals())
                global keep_running; keep_running = False
            t = threading.Thread(target=interact)
            t.setDaemon(True)
            t.start()

        if 1:
            # max xfer rate = 1/dt_min*c.bufsize
            dt_max = 0.5
            dt_min = 0.01
            dt = dt_max

            while keep_running:
                if onApplicationReceiving(app, app.ReceivedStreams):
                    dt /= 4.0
                else:
                    dt *= 2.0
                if dt < dt_min: dt = dt_min
                if dt > dt_max: dt = dt_max
                if DBG2: print dt
                time.sleep(dt)
        if 0:
            skype.OnApplicationReceiving = onApplicationReceiving
            while keep_running:
                time.sleep(5)
            
    except KeyboardInterrupt:
        print 'ctrl+c'
finally:
    app.Delete()
    print '== app deleted =='

