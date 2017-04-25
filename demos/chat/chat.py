import time
import weakref
from serf.publisher import Publisher

# Chat service models for Person, Room and RoomList.

class Person(object):
    def __init__(self, client_addr):
        self.client_addr = client_addr
        self.name = None
        self.rooms = {}

    def say(self, room_name, msg):
        room = self.rooms.get(room_name)
        if room is not None:
            room._say(self.client_addr, self.name, msg)

    def _enter(self, room_name, room):
        if room_name in self.rooms:
            return
        self.rooms[room_name] = room
        room._addPerson(self)

    def leave(self, room_name):
        room = self.rooms.pop(room_name, None)
        if room is not None:
            room._removePerson(self.client_addr)

    def leaveAll(self):
        for room_name in list(self.rooms):
            self.leave(room_name)

    def setName(self, name):
        if name == self.name:
            return
        self.name = name
        for room in self.rooms.values():
            room._addPerson(self)

class Room(Publisher):
    def __init__(self):
        Publisher.__init__(self)
        self.people = weakref.WeakValueDictionary()
        self.history = []

    def _addPerson(self, person):
        self.people[person.client_addr] = person
        self.notify('enter', [person.client_addr, person.name])

    def _removePerson(self, client_addr):
        person = self.people.pop(client_addr, None)
        if person is not None:
            self.notify('leave', person.client_addr)

    def _say(self, client_addr, name, msg):
        event = [client_addr, name, msg, time.time()]
        self.notify('message', event)
        self.history.append(event)
        if len(self.history) > 15:
            del self.history[0]

    def getPeople(self):
        info = {}
        for addr, person in self.people.items():
            info[addr] = person.name
        return info

    def getHistory(self):
        return self.history

class RoomList(Publisher):
    def __init__(self):
        Publisher.__init__(self)
        self.rooms = {}

    def getRoom(self, name):
        if name not in self.rooms:
            self.rooms[name] = Room()
            self.notify('new-room', name)
        return self.rooms[name]

    def list(self):
        return list(sorted(self.rooms))

    def addPerson(self, room_name, person):
        if type(person) is not Person:
            return
        room = self.getRoom(room_name)
        person._enter(room_name, room)
