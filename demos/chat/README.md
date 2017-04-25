Chat Demo
=========

Overview
--------

In `chat.py` we define the models for an MVC-based chat app: `Person`,
`Room` and `RoomList`. 

Chat is an easy choice for a demo because the models don't have to do
anything other than remember a little bit of state and send
notifications when it changes.

When a client connects we provide the shared `RoomList` object and their
own `Person` object.

Rooms are auto-proxied. What that means is that when a call of `ROOM_LIST.getRoom`
returns a `Room` object on the server, a reference is automatically
added to the set of objects available on the server and a proxy is
returned.

In `chat.js` you can see how the MVC approach plays out. Our views are
`ListView` (used for room and people lists) `MessageView`, a number of
input fields, and the tab-strip.

In each case, when we create a view, we set its initial state via a
call to the model and subscribe for updates. 

Control code is that which listens for view events and updates models
accordingly. E.g. handling tab-clicks, room-list clicks and text
entry.

Running the demo
----------------

Install serf:

* Install `eventlet`.
* Symlink `serf/python` as `serf` somewhere on your python path.

Configure your web server:

* make `/js/serf` link to `serf/js`
* add `/js/jquery-2.1.1.min.js`, `/js/w2ui-1.4.3.min.js` and
  `/css/w2ui-1.4.3.min.css` - see `demos/extras`
* serve `chat/www` on `/chat/`
* add a proxy-pass from `/chat/ws/` to `ws://localhost:9903/`
* _for Nginx_, add `proxy_read_timeout 7d;`

Run the backend:

* Run `chat_server.py` or install it as a service.
