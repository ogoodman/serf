#!/usr/bin/python

from SocketServer import TCPServer, ThreadingMixIn
import thread
from publisher import Publisher
from websocket_handler import WebSocketHandler
from rpc_handler import RPCHandler
from model import Model

SINGLETON_MODEL = Model()

def makeRPCHandler(socket, client_address, server):
    print client_address, 'connected'
    transport = WebSocketHandler(socket, client_address, server)
    handler = RPCHandler(transport)
    handler.provide('shared', SINGLETON_MODEL)
    handler.provide('private', Model())
    try:
        transport.handle()
    finally:
        transport.finish()
    return handler

class ThreadingTCPServer(ThreadingMixIn, TCPServer):
    allow_reuse_address = True

def startServer():
    """Run server in Python REPL."""
    server = ThreadingTCPServer(("localhost", 9999), makeRPCHandler)
    tid = thread.start_new_thread(server.serve_forever, ())
    print 'thread id:', tid
    return server

if __name__ == '__main__':
    server = ThreadingTCPServer(('', 9999), makeRPCHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close();
        print '\nBye'
