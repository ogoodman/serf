Publisher = publisher.Publisher;

function ListView(elem, prefix) {
    Publisher.call(this);
    this.elem = elem;
    this.prefix = prefix || 'list-';
}

ListView.prototype = new Publisher();

ListView.prototype.set = function(id, name) {
    var self = this;
    var ch = document.getElementById(this.prefix + id);
    if (ch === null) {
	    ch = document.createElement('div');
        ch.style.padding = '3px';
	    ch.id = this.prefix + id;
	    this.elem.appendChild(ch);
	    ch.addEventListener('click', function() {
	        self.notify('click', id);
	    });
    }
	ch.innerHTML = name;
};

ListView.prototype.remove = function(id) {
	var ch = document.getElementById(this.prefix + id);
	if (ch && ch.parentElement == this.elem) {
	    this.elem.removeChild(ch);
	}
};

function MessageView(elem) {
    this.elem = elem;
}

MessageView.prototype.addMessage = function(info) {
    var from = info[1] || info[0];
    var msg = info[2];
    var date = new Date(info[3]*1000);
    var ts = date.toTimeString().substr(0, 8);
    var ch = document.createElement('div');
    ch.className = 'message';
    ch.innerHTML = '<span class="hms">' + ts + '</span> <b>' + from + ':</b> ' + msg;
    this.elem.appendChild(ch);
    try {
        ch.scrollIntoView();
    } catch(e) {}
};

// Seems like there ought to be a better way to do this:
// DivSet handles a group of divs under 'elem', switching
// visibility such that one is visible at a given time.

function DivSet(elem) {
    this.elem = elem;
    this.children = {};
    this.current = null;
}

DivSet.prototype.has = function(id) {
    return id in this.children;
};

DivSet.prototype.add = function(id) {
    if (!(id in this.children)) {
        var div = document.createElement('div');
        div.id = id;
        div.style.display = 'none';
        div.style.height = '100%';
        this.elem.appendChild(div);
        this.children[id] = true;
        return div;
    }
    return document.getElementById(id);
};

DivSet.prototype.remove = function(id) {
    var div = document.getElementById(id);
    if (div !== null && div.parentElement == this.elem) {
        this.elem.removeChild(div);
    }
    if (id in this.children) {
        delete this.children[id];
    }
    if (this.current == id) {
        this.current = null;
    }
};

DivSet.prototype.show = function(id) {
    if (this.current == id) {
        return;
    }
    var div;
    if (this.current !== null) {
        div = document.getElementById(this.current);
        div.style.display = 'none';
    }
    div = document.getElementById(id);
    if (div !== null) {
        div.style.display = 'inline';
        this.current = id;
    }
};

$(function() {

    var title = '<h2>Chat [<span id="status" style="color:orange;">connecting</span>]</h2>';
    var panel_style = 'border: 1px solid #dfdfdf; padding: 5px;';
    var rooms_div = '<div id="room-list" style="height:100%; width:100%;"></div>';
    var chat_set_html = '<div id="chat-set" style="height:100%; width:100%;"></div>';
    var people_set_html = '<div id="people-set" style="height:100%; width:100%;"></div>';
    var name_input_html = '<label>Name</label> <input type="text" id="name-input" placeholder="Your Name"/> <label>Create/Join</label> <input type="text" id="room-input" placeholder="Room Name"/>';
    var chat_style = 'background-color: #F0F0C1; border: 1px solid #dfdfdf; padding: 5px;';
    var chat_input_html = '<textarea id="chat-input" style="height:100%; width:100%;"></textarea>';

    var tabs = {
        tabs: [],
        onClick: function(event) {
            chat_set.show('room-' + event.target);
            people_set.show('people-' + event.target);
        },
        onClose: function(event) {
            closeRoom(event.target);
        }
    };

    var layout = $('#layout').w2layout({
        name: 'layout',
        panels: [
            { type: 'top', size: 50, style: panel_style, content: title },
            { type: 'left', size: 300, resizable: true, style: panel_style, content: rooms_div, title: 'Rooms' },
            { type: 'main', style: panel_style, resizable: true, tabs: tabs },
            { type: 'bottom', size: 50, style: panel_style, content: name_input_html }
        ]
    });

    // The chat_layout below will stay fixed in the 'main' panel of
    // the main layout. As the user clicks different tabs, we will
    // update the content of the 'main' and 'right' panels using
    // chat_set and people_set.

    $().w2layout({
        name: 'chat_layout',
        panels: [
            { type: 'main', style: chat_style, content: chat_set_html },
            { type: 'right', size: 300, resizable: true, style: panel_style, content: people_set_html, title: 'People' },
            { type: 'bottom', size: 100, resizable: true, style: panel_style, content: chat_input_html }
        ]
    });

    var server = new rpc.WSServer('ws://' + location.hostname + '/chat/ws/');

    // Show connection status.
    var st = $('#status')[0];
    server.onopen = function() {
        st.style.color = 'green';
        st.textContent = 'connected';
    };
    server.onclose = function() {
        st.style.color = 'red';
        st.textContent = 'disconnected';
    };

    // Exposed so you can access them in the console.
    rooms = server.getProxy('rooms', ['addPerson', 'list', 'getRoom']);
    me = server.getProxy('me', ['setName', 'say', 'leaveAll', 'leave']);
    room_map = {};

    server.connect();

    // Set/remember the name.
    var name_input = document.getElementById('name-input');
    var my_name;
    try {
        my_name = localStorage['chat.name'];
    } catch (e) {
        localStorage = {};
    }
    if (typeof my_name == 'string') {
        me.setName(my_name).done();
        name_input.value = my_name;
    }
    name_input.onchange = function() {
        my_name = name_input.value;
        me.setName(my_name).done();
        localStorage['chat.name'] = my_name;
    }

    // Create/join room input field.
    var room_input = $('#room-input')[0];
    room_input.onchange = function() {
        if (room_input.value != '') {
            setRoom(room_input.value);
        }
    };

    var chat_set = null;
    var people_set = null;
    var chat_input = null;

    function createRoom(name) {
        if (chat_set.has('room-' + name)) {
            return;
        }
        var chat_div = chat_set.add('room-' + name);
        var chat_view = new MessageView(chat_div);

        var people_div = people_set.add('people-' + name);
        var people_view = new ListView(people_div, 'pv-' + name);
        
        rooms.getRoom(name).done(function(room) {
            room_map[name] = room;
            room.addMethod('getPeople');
            room.addMethod('getHistory');
            room.getPeople().done(function(people) {
                for (var id in people) {
                    people_view.set(id, people[id]);
                }
            });
            room.getHistory().done(function(history) {
                for (var i=0, n=history.length; i < n; ++i) {
                    var h = history[i];
                    chat_view.addMessage(h);
                }
            });
            room.subscribe('message', function(ev, m) {
                chat_view.addMessage(m);
            });
            room.subscribe('enter', function(ev, info) {
                people_view.set(info[0], info[1]);
            });
            room.subscribe('leave', function(ev, id) {
                people_view.remove(id);
            });
        });
    }

    function sendMessage() {
        if (chat_set.current === null) return;
        if (chat_input.value == '') return;
        me.say(chat_set.current.substr(5), chat_input.value).done();
        chat_input.value = '';
    }

    function closeRoom(name) {
        me.leave(name).done();
        if (name in room_map) {
            var room = room_map[name];
            room.unsubscribeAll('message');
            room.unsubscribeAll('enter');
            room.unsubscribeAll('leave');
            delete room_map[name];
        }
        chat_set.remove('room-' + name);
        people_set.remove('people-' + name);
    }

    function setRoom(name) {
        var tabs = layout.get('main').tabs;
        if (tabs.get(name) === null) {
            tabs.add({id: name, text: name, closable: true});
            rooms.addPerson(name, me).done();
        }
        if (chat_set === null) {
            // The reason we do this here rather than immediately is
            // that if we do, the chat_layout doesn't shrink when the
            // first tab is created.
            w2ui['layout'].content('main', w2ui['chat_layout']);
            w2ui['chat_layout'].on('render', function(event) {
                event.onComplete = function() {
                    chat_set = new DivSet($('#chat-set')[0]);
                    people_set = new DivSet($('#people-set')[0]);

                    createRoom(name);
                    tabs.select(name);
                    chat_set.show('room-' + name);
                    people_set.show('people-' + name);

                    chat_input = document.getElementById('chat-input');
                    $(chat_input).keypress(function(e) {
                        if (e.keyCode == 13) {
                            sendMessage();
                            e.preventDefault();
                        }
                    });
                };
            });
        } else {
            createRoom(name);
            tabs.select(name);
            chat_set.show('room-' + name);
            people_set.show('people-' + name);
        }
    }

    // Set up the list of rooms.
    var rooms_view = new ListView($('#room-list')[0], 'room:');
    rooms.list().done(function(room_list) {
        for (var i=0, n=room_list.length; i < n; ++i) {
            var room = room_list[i];
            rooms_view.set(room, room);
        }
    });
    rooms.subscribe('new-room', function(ev, room) {
        rooms_view.set(room, room);
    });
    rooms_view.subscribe('click', function(ev, name) {
        setRoom(name);
    });
});
