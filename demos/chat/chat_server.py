#!/usr/bin/python

from serf.ws_server import serve_ws
from chat import *

ROOM_LIST = RoomList()

def autoProxy(obj):
    if type(obj) is Room:
        return 'room:' + str(hash(obj))

JC_OPTS = {
    'auto_proxy': autoProxy
}

class SessionHandler(object):
    def initSession(self, handler):
        handler.provide('rooms', ROOM_LIST)
        handler.provide('me', Person('%s:%s' % handler.client_address))
    def closeSession(self, handler):
        handler.storage['me'].leaveAll()

if __name__ == '__main__':
    serve_ws(SessionHandler(), 9903, jc_opts=JC_OPTS)
