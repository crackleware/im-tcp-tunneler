## TCP tunneler over XMPP

### Requirements

- Python (2.6+)
- (optional but suggested) virtualenv
- libxml2 (http://xmlsoft.org/)
- dnspython (http://pypi.python.org/pypi/dnspython/1.9.4)
- pyxmpp (http://pypi.python.org/pypi/pyxmpp/1.1.2)

### Usage

Server tunnels.conf example:

	exposed = [
		# 'IP:PORT',
		'127.0.0.1:80',
		'127.0.0.1:22',
		]

	forwarded = [
		# 'IP:PORT->IP:PORT!JID',
		]

Server command-line example:

	$ virtualenv env; source env/bin/activate; pip install pyxmpp; pip install dnspython
    $ python xmpp_tcp_tunneler_pyxmpp.py someone@domain1.com/tunneler ***password*** tls_noverify tunnels.conf

Client tunnels.conf example:

	exposed = [
		# 'IP:PORT',
		]

	forwarded = [
		# 'IP:PORT->IP:PORT!JID',
		'127.0.0.1:9999->127.0.0.1:80!someone@domain1.com/tunneler',
		'127.0.0.1:2222->127.0.0.1:22!someone@domain1.com/tunneler',
		]

Client command-line example:

	$ virtualenv env; source env/bin/activate; pip install pyxmpp; pip install dnspython
	$ python xmpp_tcp_tunneler_pyxmpp.py someone@domain2.com/tunneler ***password*** tls_noverify tunnels.conf

Open http://127.0.0.1:9999/ on client.

### Tested on

- ejabberd (http://www.ejabberd.im/):

	- for example, to increase "normal" shaper limits traffic speed to 10000 B/s:

			< {shaper, normal, {maxrate, 1000}}.
			---
			> {shaper, normal, {maxrate, 10000}}.

### Todo

- access control
- better configuration management (web GUI, HTTP/XMLRPC API...)
- make Python package to simplify installation

### Related

- Xmpp-tunnel: IP tunneling over XMPP (Android support) - http://jahrome.free.fr/index.php/xmpp-tunnel-ip-tunneling-xmpp-android-ssh?lang=en (https://github.com/jahrome/xmpp-tunnel)
