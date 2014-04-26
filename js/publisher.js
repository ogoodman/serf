define(function() {
    function Publisher() {
	this._subs = {};
    }

    Publisher.prototype.subscribe = function(event, cb) {
	if (this._subs[event]) {
	    this._subs.push(cb);
	} else {
	    this._subs[event] = [cb];
	}
    };

    Publisher.prototype.notify = function(event, info) {
	if (!this._subs[event]) return;
	var subs = this._subs[event];
	var i, n = subs.length;
	for (i=0; i<n; ++i) {
	    try {
		subs[i](event, info);
	    } catch (e) {
		console.log('Exception from subscriber', e);
	    }
	}
    };

    return {Publisher: Publisher};
});
