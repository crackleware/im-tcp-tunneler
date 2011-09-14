## TCP tunneler over instant messaging clients (XMPP, Skype, ...)

### Requirements

- Python (2.6+)
- (optional but suggested) virtualenv

- for XMPP:
    - libxml2 (http://xmlsoft.org/)
    - dnspython (http://pypi.python.org/pypi/dnspython/1.9.4)
    - pyxmpp (http://pypi.python.org/pypi/pyxmpp/1.1.2)

- for Skype:
    - skype4py (http://pypi.python.org/pypi/Skype4Py/1.0.32.0)

- for encryption:
    - python-gnupg (http://pypi.python.org/pypi/python-gnupg/0.2.8)
    - m2crypto (http://pypi.python.org/pypi/M2Crypto/0.21.1)

### Usage example

#### XMPP

Server tunnels.conf:

	exposed = {
        # 'IP:PORT': ['JID', ...], ...
		'127.0.0.1:80' : ['*'],
		'127.0.0.1:22' : ['trusted-buddy-1@domainA.com'],
		}

	forwarded = [
		# 'IP:PORT->IP:PORT!JID',
		]

Server command-line:

	$ virtualenv env; source env/bin/activate; pip install pyxmpp; pip install dnspython
    $ python xmpp_tcp_tunneler_pyxmpp.py someone@domain1.com/tunneler ***password*** tls_noverify tunnels.conf

Client tunnels.conf:

	exposed = {
        # 'IP:PORT': ['JID', ...], ...
		}

	forwarded = [
		# 'IP:PORT->IP:PORT!JID',
		'127.0.0.1:9999->127.0.0.1:80!someone@domain1.com/tunneler',
		'127.0.0.1:2222->127.0.0.1:22!someone@domain1.com/tunneler',
		]

Client command-line:

	$ virtualenv env; source env/bin/activate; pip install pyxmpp; pip install dnspython
	$ python xmpp_tcp_tunneler_pyxmpp.py someone@domain2.com/tunneler ***password*** tls_noverify tunnels.conf

Open http://127.0.0.1:9999/ on client.

Tested on:

- ejabberd ( http://www.ejabberd.im/ ):

	- for example, to increase "normal" shaper limits traffic speed to 10000 B/s:

			< {shaper, normal, {maxrate, 1000}}.
			---
			> {shaper, normal, {maxrate, 10000}}.

#### Skype

Structure of tunnels.conf is the same as for XMPP. JID is actually skypename.

	$ virtualenv env; source env/bin/activate; pip install skype4py
    $ python2 skype_tcp_tunneler.py tunnels.conf

#### Encryption (GPG + AES)

Install:

	$ pip install python-gnupg m2crypto

In tunnels.conf add:

	gpg_keys = [
		# 'JID' or ('JID', 'keyid'), ...
        'someone@domain1.com', # or ('skype-buddy-1', 'someone@domain1.com'),
		]

    gpg_passphrase = PROMPT # or AGENT or 'PASSWORD'

### Todo

- encrypt whole message data
- better access control
- better configuration management (web GUI, HTTP/XMLRPC API...)
- make Python package to simplify installation
- investigate http://xmpp.org/extensions/xep-0047.html

### Related

- Xmpp-tunnel: IP tunneling over XMPP (Android support) - http://jahrome.free.fr/index.php/xmpp-tunnel-ip-tunneling-xmpp-android-ssh?lang=en (https://github.com/jahrome/xmpp-tunnel)
- http://code.google.com/p/skypeproxy/ - peer2peer network tunneling tool (Java)
- http://jonathanverner.appspot.com/download - Skype Proxy - A program for forwarding TCP/IP connections over Skype. (C++, Qt4)
