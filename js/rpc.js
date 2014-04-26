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
	    return that.hooks[data.__ext__name_](that, data.__ext__args_);
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
	    if ('m' in data) { // call (currently one-way only from server)
		var prx = that.obj[data.o];
		var method = prx[data.m];
		var args = data.a;
		// FIXME: this should eventually handle promises too.
		// If result were known to be a promise, we'd just
		// call the sendRemote in a .done callback.
		var msg;
		try {
		    var result = method.apply(prx, args);
		    if (data.N && data.O) {
			that.sendRemote({
			    n: data.N, // reply node
			    o: data.O, // reply object (callback id)
			    r: result || null
			});
		    }
		} catch (ex) {
		    if (data.N && data.O) {
			that.sendRemote({
			    n: data.N, // reply node
			    o: data.O, // reply object (callback id)
			    e: [ex.constructor.name, [ex.message]]
			});
		    } else {
			// FIXME: What can we do here? Ignoring it means the
			// one-way call silently swallows exceptions.
		    }
		}
	    } else { // reply
		var deferred = that.pendingCalls[data.o];
		delete that.pendingCalls[data.o];
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
	if (data === null) return undefined;
	var t = typeof data;
	if ((t != 'object') && (t != 'function')) return undefined;
	if (typeof data.ext_encoding != 'function') return undefined;
	var info = data.ext_encoding();
	return {__ext__name_: info.name, __ext__args_: info.args};
    }

    WSServer.prototype.sendRemote = function(msg) {
	var that = this;
	this.connect().done(function() {
	    that.ws.send(JSON.stringify(traverse(msg, preEncodeFn)));
	});
    };

    WSServer.prototype.callRemote = function(oid, method, args) {
	var that = this;
	this.callId += 1;
	var msg = {
	    o: oid,
	    m: method,
	    a: args,
	    O: this.callId,
	    N: 'browser'
	};
	var deferred = this.pendingCalls[this.callId] = when.defer();
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
    WSServer.prototype.hooks['BoundMethod'] = function(server, args) {
	return makeBoundMethod(server, args.o, args.m, args.n, args.t);
	// return new BoundMethod(args.o, args.m);
    };

    function makeBoundMethod(server, oid, method, node, twoway) {
	function mcall() {
	    if (node == 'browser') {
		var ob = server.obj[oid];
		return ob[method].apply(ob, arguments);
	    } else {
		var args = Array.prototype.slice.call(arguments);
		if (twoway) {
		    return server.callRemote(oid, method, args);
		} else {
		    return server.sendRemote({o: oid, m: method, a:args});
		}
	    }
	}
	mcall.ext_encoding = function() {
	    return {name: 'BoundMethod', args:{o: oid, m: method, n: node}};
	}
	return mcall;
    }

    function Proxy(server, objId, node) {
	this.server = server;
	this.objId = objId;
	this.node = node || 'server';
	if (this.node == 'server') {
	    this.server.obj[objId] = this; // register.
	}
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

    Proxy.prototype.ext_encoding = function() {
	return {name: 'Proxy', args:{o: this.objId, n:this.node}}
    };

    WSServer.prototype.hooks['Proxy'] = function(server, args) {
	// Unlikely that server would send us proxy to our own object
	// but nonetheless there should be no harm in resolving it
	// to a direct reference to the object.
	if (args.n == 'browser') return this.obj[args.o];
	return new Proxy(server, args.o);
    };

    return {
	WSServer: WSServer,
	BoundMethod: BoundMethod,
	makeBoundMethod: makeBoundMethod,
	Proxy: Proxy
    };
});
