
from wsgiref.simple_server import make_server
import urlparse
import threading
import time
import uuid
import traceback
import socket
import pprint

exposed = [
    # 'IP:PORT', ...
    ]

forwarded = [
    # 'IP:PORT->IP:PORT!JID', ...
    ]

web_port = None

DBG1 = True
DBG2 = False

def send_xmpp_message(from_jid, to_jid, body): raise NotImplemented
def get_client_jid(): raise NotImplemented

def web_app(environ, start_response):
    q = urlparse.parse_qs(environ['QUERY_STRING'])

    if '/test' in environ['PATH_INFO']:
        start_response('200 OK', [('Content-Type', 'text/html')])
        return ['OK: %s\n' % time.asctime()]

    else:
        start_response('404 Not Found', [('Content-Type', 'text/plain')])
        return ['Not Found\n']

class Connection:
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.sock = None
        self.remote_jid = None
    def __repr__(self):
        return '%s(id=%r, remote_jid=%r)' % (self.__class__.__name__, self.id, self.remote_jid)
    
conns = {}

lock = threading.RLock()

def s2x_socket_listener((src_addr, src_port), (dst_addr, dst_port), dst_jid):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((src_addr, src_port))
    sock.listen(5)
    while 1:
        conn, addr = sock.accept()
        conn.settimeout(0.3)
        if DBG1:
            print 's2x_socket_listener(%s:%d->%s:%d!%s), accepted: %r' % (
                src_addr, src_port, dst_addr, dst_port, dst_jid, (conn, addr))
        c = Connection()
        c.sock = conn
        c.remote_jid = dst_jid
        with lock:
            conns[c.id] = c
            if DBG2: print conns
        send_xmpp_message(get_client_jid(), c.remote_jid,
                          'CONNECT %s:%d %s' % (dst_addr, dst_port, c.id))
        t = threading.Thread(target=connection_handler, args=(c,))
        t.setDaemon(True)
        t.start()

def connection_handler(c):
    while 1:
        try: d = c.sock.recv(1024)
        except socket.timeout:
            if DBG2: print 'socket.timeout', c.id
            continue
        except socket.error:
            if DBG1: traceback.print_exc()
            break
        if DBG2: print 'd: %r' % d
        if not d: break
        send_xmpp_message(get_client_jid(), c.remote_jid,
                          'DATA %s %s' % (c.id, d.encode('hex')))
    try:
        c.sock.close()
        c.sock.recv(1024)
    except socket.error:
        if DBG1: traceback.print_exc()
    with lock:
        if c.id in conns:
            del conns[c.id]
            if DBG2: print 'del conns[%r]' % c.id
        if DBG2: print conns
    send_xmpp_message(get_client_jid(), c.remote_jid,
                      'CLOSE %s' % (c.id))

def parse_addr_port(addr_port):
    addr, port = addr_port.split(':')
    port = int(port)
    return addr, port
    
def setup_accept_and_forward():
    # accept local connections and forward them to remote tunneler
    for s in forwarded:
        src_addr_port, dst = s.split('->')
        dst_addr_port, dst_jid = dst.split('!')
        t = threading.Thread(target=s2x_socket_listener, args=(
                parse_addr_port(src_addr_port),
                parse_addr_port(dst_addr_port), dst_jid))
        t.setDaemon(True)
        t.start()

def handle_message(from_jid, to_jid, body):
    try:
        resp = None

        if body.startswith('CONNECT '):
            _, addr_port, conn_id = body.split(' ')
            if addr_port in exposed:
                addr, port = addr_port.split(':')
                port = int(port)

                c = Connection()
                c.id = conn_id
                c.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                c.sock.connect((addr, port))
                c.remote_jid = from_jid
                with lock:
                    conns[c.id] = c
                    if DBG2: print conns

                t = threading.Thread(target=connection_handler, args=(c,))
                t.setDaemon(True)
                t.start()

                resp = 'CONNECT_RESULT %s OK' % c.id

            else:
                resp = 'CONNECT_RESULT %s ERROR not exposed' % c.id

        # elif body.startswith('CONNECT_RESULT '):
        #     _, conn_id, status = body.split(' ')

        #     if status != 'OK':
        #         # TODO
        #         pass

        elif body.startswith('CLOSE '):
            _, conn_id = body.split()
            with lock:
                c = conns.get(conn_id, None)
                if DBG2: print conns
            if c:
                c.sock.close()
                if DBG2: print 'sock.close:', c
            #     resp = 'CLOSE_RESULT %s OK' % conn_id
            # else:
            #     resp = 'CLOSE_RESULT %s ERROR unknown connection id' % conn_id

        # elif body.startswith('CLOSE_RESULT '):
        #     # TODO
        #     pass

        elif body.startswith('DATA '):
            _, conn_id, data = body.split()
            data = data.decode('hex')
            if DBG2: print 'data: %r' % data
            with lock:
                c = conns.get(conn_id, None)
                if DBG2: print conns
            if c:
                c.sock.send(data)
                time.sleep(0.1)
                # resp = 'DATA_RESULT %s OK' % conn_id
            else:
                resp = 'DATA_RESULT %s ERROR unknown connection id' % conn_id

        if resp is not None:
            send_xmpp_message(to_jid, from_jid, resp)
        else:
            # send_xmpp_message(to_jid, from_jid, 'ACK')
            pass
    except:
        traceback.print_exc()

def setup_tunnels(filename):
    execfile(filename, globals())
    if DBG1: print 'exposed:'
    pprint.pprint(exposed)
    if DBG1: print 'forwarded:'
    pprint.pprint(forwarded)
    if DBG1: print 'web_port:', web_port

    setup_accept_and_forward()

    if web_port is not None:
        httpd = make_server('', web_port, web_app)
        t = threading.Thread(target=httpd.serve_forever)
        t.setDaemon(True)
        t.start()

