define(['when/when'], function(when) {
    function traverse(data, fn) {
	var r = traverse0(data, fn);
	if (r != undefined) return r;
	return data;
    }

    function traverse0(data, fn) {
	var r = fn(data);
	if (r !== undefined) return r;

	var t = Object.prototype.toString.call(data);
	if (t == '[object Array]') {
	    var i=0, n=data.length, r;
	    for (i=0; i<n; ++i) {
		r = traverse0(data[i], fn);
		if (r !== undefined) data[i] = r;
	    }
	    return undefined;
	}
	if (t == '[object Object]') {
	    var k, r;
	    for (k in data) {
		if (data.hasOwnProperty(k)) {
		    r = traverse0(data[k], fn);
		    if (r !== undefined) data[k] = r;
		}
	    }
	    return undefined;
	}
	return undefined;
    }

    function WSServer(url) {
	this.url = url;
	this.callId = 0;
	this.pendingCalls = {};
	this.onopen = function() {};
	this.onclose = function() {};
	this.obj = {};
    };

    WSServer.prototype.hooks = {};
    
    WSServer.prototype.connect = function() {
	var that = this;

	function postDecodeFn(data) {
	    if (Object.prototype.toString.call(data) !=
		'[object Object]') return undefined;
	    if (!(data.__ext__name_ in that.hooks)) return undefined;
	    return that.hooks[data.__ext__name_](data.__ext__args_);
	}

	if (this.ws !== undefined) {
	    if (this.ws.readyState < 2) return this.conn;
	}
	this.ws = new WebSocket(that.url);
	this.conn = when.promise(function(resolve, reject) {
	    if (that.ws === undefined) {
		reject('connection closed');
	    }
	    that.ws.onopen = function(event) {
		that.onopen();
		resolve();
	    };
	});
	this.ws.onmessage = function(event) {
	    // console.log(event.data);
	    var data = traverse(JSON.parse(event.data), postDecodeFn);
	    if ('o' in data) { // reply
		// call (currently one-way only from server)
		var prx = that.obj[data.o];
		var method = prx[data.m];
		var args = data.a;
		method.apply(prx, args);
	    } else {
		var deferred = that.pendingCalls[data.i];
		delete that.pendingCalls[data.i];
		if ('e' in data) {
		    deferred.reject(data.e);
		} else {
		    deferred.resolve(data.r);
		}
	    }
	};
	this.ws.onclose = function(event) {
	    // console.log('connection closed');
	    that.ws = undefined;
	    that.onclose();
	};
	return this.conn;
    };

    // JSON extension:
    // use __ext__name_, __ext__args_ and .ext_encoding
    function preEncodeFn(data) {
	if (typeof data != 'object') return undefined;
	if (typeof data.ext_encoding != 'function') return undefined;
	var info = data.ext_encoding();
	return {__ext__name_: info.name, __ext__args_: info.args};
    }

    WSServer.prototype.callRemote = function(oid, method, args) {
	var that = this;
	this.callId += 1;
	var msg = {
	    o: oid,
	    i: that.callId,
	    m: method,
	    a: args,
	    r: 'browser'
	};
	var deferred = this.pendingCalls[that.callId] = when.defer();
	this.connect().done(function() {
	    that.ws.send(JSON.stringify(traverse(msg, preEncodeFn)));
	}, function(error) {
	    deferred.reject(['connection error', error]);
	});
	return deferred.promise;
    };

    function BoundMethod(oid, method) {
	this.oid = oid;
	this.method = method;
    };
    BoundMethod.prototype.ext_encoding = function() {
	return {name: 'BoundMethod', args:{o: this.oid, m: this.method}};
    };
    WSServer.prototype.hooks['BoundMethod'] = function(args) {
	return new BoundMethod(args.o, args.m);
    };

    function Proxy(server, objId) {
	this.server = server;
	this.objId = objId;
	this.server.obj[objId] = this; // register.
	this._subs = {};
    }

    Proxy.prototype.addMethod = function(name) {
	var that = this;
	this[name] = function() {
	    return that.server.callRemote(that.objId, name, Array.prototype.slice.call(arguments));
	}
    };

    Proxy.prototype._notify = function(event, info) {
	var subs = this._subs[event] || [];
	var i, n = subs.length;
	for (i = 0; i < n; ++i ) subs[i](event, info);
    };
    
    Proxy.prototype.subscribe = function(event, cb) {
	if (!(event in this._subs)) {
	    this._subs[event] = [cb];
	    this.server.callRemote(this.objId, 'subscribe', [event, new BoundMethod(this.objId, '_notify')]);
	} else {
	    this._subs[event].push(cb);
	}
    };

    return {
	WSServer: WSServer,
	BoundMethod: BoundMethod,
	Proxy: Proxy
    };
});
