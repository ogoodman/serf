//#include /js/serf/publisher.js

var online_view = (function() {
    var Publisher = publisher.Publisher;

    function OnlineView(model) {
	    Publisher.call(this);
	    var that = this;
	    this.elem = document.getElementById('online-list');
	    window.oe = this.elem;
	    this.model = model;
	    this.model.getPlayers().done(function(players) {
            for (k in players) {
                if (players.hasOwnProperty(k)) {
                    that.set(k, players[k])
                }
            }
	    });
	    that.model.subscribe('online', function(ev, id_name) {
	        that.set(id_name[0], id_name[1]);
	    });
	    that.model.subscribe('offline', function(ev, id) {
	        that.remove(id);
	    });
    };

    OnlineView.prototype = new Publisher();

    OnlineView.prototype.set = function(id, name) {
        this.remove(id);
	    var that = this;
	    var ch = document.createElement('div');
	    ch.id = id;
	    ch.innerHTML = name;
	    this.elem.appendChild(ch);
	    ch.addEventListener('click', function() {
	        that.notify('player-chosen', name);
	    });
    };

    OnlineView.prototype.remove = function(id) {
	    var ch = document.getElementById(id);
	    if (ch && ch.parentElement == this.elem) {
	        this.elem.removeChild(ch);
	    }
    };

    return {
	    OnlineView: OnlineView
    };
})();
