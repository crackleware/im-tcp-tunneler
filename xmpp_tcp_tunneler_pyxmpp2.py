#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
tcp tunneling over xmpp (based on echo bot)

to run:
    virtualenv env
    source env/bin/activate
    pip install xmpppy2
    python xmpp_tcp_tunneler_pyxmpp2.py ...
"""

import sys
import logging
from getpass import getpass
import argparse

from pyxmpp2.jid import JID
from pyxmpp2.message import Message
from pyxmpp2.presence import Presence
from pyxmpp2.client import Client
from pyxmpp2.settings import XMPPSettings
from pyxmpp2.interfaces import EventHandler, event_handler, QUIT
from pyxmpp2.streamevents import AuthorizedEvent, DisconnectedEvent
from pyxmpp2.interfaces import XMPPFeatureHandler
from pyxmpp2.interfaces import presence_stanza_handler, message_stanza_handler
from pyxmpp2.ext.version import VersionProvider
from pyxmpp2.mainloop.select import SelectMainLoop
from pyxmpp2.mainloop.threads import ThreadPool

import xmpp_tcp_tunneler

def send_xmpp_message(from_jid, to_jid, txt):
    msg = Message(stanza_type = 'chat',
                  from_jid = JID(from_jid),
                  to_jid = JID(to_jid),
                  subject = None, body = txt,
                  thread = None)
    bot.client.send(msg)
xmpp_tcp_tunneler.send_xmpp_message = send_xmpp_message

def get_client_jid():
    return bot.client.jid.as_unicode()
xmpp_tcp_tunneler.get_client_jid = get_client_jid


class Bot(EventHandler, XMPPFeatureHandler):
    def __init__(self, my_jid, settings):
        version_provider = VersionProvider(settings)
        self.main_loop = SelectMainLoop(settings)
        #self.main_loop = ThreadPool(settings)
        #self.main_loop.start(daemon=True)
        self.client = Client(my_jid, [self, version_provider], settings, main_loop=self.main_loop)
        #self.client = Client(my_jid, [self, version_provider], settings)

    def run(self):
        """Request client connection and start the main loop."""
        self.client.connect()
        self.client.run()

    def disconnect(self):
        """Request disconnection and let the main loop run for a 2 more
        seconds for graceful disconnection."""
        self.client.disconnect()
        self.client.run(timeout = 2)

    @presence_stanza_handler("subscribe")
    def handle_presence_subscribe(self, stanza):
        logging.info(u"{0} requested presence subscription".format(stanza.from_jid))
        presence = Presence(to_jid = stanza.from_jid.bare(), stanza_type = "subscribe")
        return [stanza.make_accept_response(), presence]

    @presence_stanza_handler("subscribed")
    def handle_presence_subscribed(self, stanza):
        logging.info(u"{0!r} accepted our subscription request".format(stanza.from_jid))
        return True

    @presence_stanza_handler("unsubscribe")
    def handle_presence_unsubscribe(self, stanza):
        logging.info(u"{0} canceled presence subscription".format(stanza.from_jid))
        presence = Presence(to_jid = stanza.from_jid.bare(), stanza_type = "unsubscribe")
        return [stanza.make_accept_response(), presence]

    @presence_stanza_handler("unsubscribed")
    def handle_presence_unsubscribed(self, stanza):
        logging.info(u"{0!r} acknowledged our subscrption cancelation".format(stanza.from_jid))
        return True

    # @message_stanza_handler()
    # def handle_message(self, stanza):
    #     """Echo every non-error ``<message/>`` stanza.
        
    #     Add "Re: " to subject, if any.
    #     """
    #     if stanza.subject:
    #         subject = u"Re: " + stanza.subject
    #     else:
    #         subject = None
    #     if stanza.body is None:
    #         txt = None
    #     else:
    #         txt = stanza.body+'!'
    #     msg = Message(stanza_type = stanza.stanza_type,
    #                   from_jid = stanza.to_jid, to_jid = stanza.from_jid,
    #                   subject = subject, body = txt,
    #                   thread = stanza.thread)
    #     return msg
    @message_stanza_handler()
    def handle_message(self, stanza):
        if stanza.stanza_type == 'chat' and not hasattr(stanza, 'processed'):
            #print stanza
            stanza.processed = True

            to_jid = stanza.to_jid.as_unicode()
            from_jid = stanza.from_jid.as_unicode()
            
            xmpp_tcp_tunneler.handle_message(from_jid, to_jid, stanza.body)
            
        return True
        
    @event_handler(DisconnectedEvent)
    def handle_disconnected(self, event):
        """Quit the main loop upon disconnection."""
        return QUIT
    
    @event_handler()
    def handle_all(self, event):
        """Log all events."""
        logging.info(u"-- {0}".format(event))

def main():
    """Parse the command-line arguments and run the bot."""
    parser = argparse.ArgumentParser(description = 'XMPP echo bot',
                                    parents = [XMPPSettings.get_arg_parser()])
    parser.add_argument('jid', metavar = 'JID', 
                        help = 'The bot JID')
    
    parser.add_argument('tunnel_conf', metavar = 'TUNNEL_CONF')
    
    parser.add_argument('--debug',
                        action = 'store_const', dest = 'log_level',
                        const = logging.DEBUG, default = logging.INFO,
                        help = 'Print debug messages')
    parser.add_argument('--quiet', const = logging.ERROR,
                        action = 'store_const', dest = 'log_level',
                        help = 'Print only error messages')
    parser.add_argument('--trace', action = 'store_true',
                        help = 'Print XML data sent and received')
   
    args = parser.parse_args()
    settings = XMPPSettings({
                            "software_name": "TCP Tunneler Bot"
                            })
    settings.load_arguments(args)

    if settings.get("password") is None:
        password = getpass("{0!r} password: ".format(args.jid))
        if sys.version_info.major < 3:
            password = password.decode("utf-8")
        settings["password"] = password

    if sys.version_info.major < 3:
        args.jid = args.jid.decode("utf-8")

    logging.basicConfig(level = args.log_level)
    if args.trace:
        print "enabling trace"
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        for logger in ("pyxmpp2.IN", "pyxmpp2.OUT"):
            logger = logging.getLogger(logger)
            logger.setLevel(logging.DEBUG)
            logger.addHandler(handler)
            logger.propagate = False

    xmpp_tcp_tunneler.setup_tunnels(args.tunnel_conf)

    global bot
    bot = Bot(JID(args.jid), settings)
    try:
        bot.run()
    except KeyboardInterrupt:
        bot.disconnect()

if __name__ == '__main__':
    main()
