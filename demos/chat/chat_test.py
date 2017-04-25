import unittest
from chat import *

class ChatTest(unittest.TestCase):
    def test(self):
        p = Person('115.187.237.215:62345')
        rl = RoomList()

        events = []
        def onEvent(e, info):
            events.append([e, info])

        rl.subscribe('new-room', onEvent)

        rl.addPerson('room', p)

        r = rl.getRoom('room')

        r.subscribe('enter', onEvent)
        r.subscribe('leave', onEvent)
        r.subscribe('message', onEvent)

        p.setName('Peter')
        self.assertEqual(r.getPeople(), {'115.187.237.215:62345': 'Peter'})
        p.say('room', 'Hi guys')
        p.leaveAll()
        expected = [
            ['new-room', 'room'],
            ['enter', ['115.187.237.215:62345', 'Peter']],
            ['message', ['115.187.237.215:62345', 'Peter', 'Hi guys']],
            ['leave', '115.187.237.215:62345']
        ]
        self.assertEqual(events, expected)

if __name__ == '__main__':
    unittest.main()
