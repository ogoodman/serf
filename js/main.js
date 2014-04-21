require(['when/when'], function(when) {

    var pendingCalls = {};
    var callId = 0;
    function callRemote(oid, method, args) {
	callId += 1;
	var msg = {
	    o: oid,
	    i: callId,
	    m: method,
	    a: args
	};
	var deferred = pendingCalls[callId] = when.defer();
	connect().done(function() {
	    window.ws.send(JSON.stringify(traverse(msg, preEncodeFn)));
	}, function(error) {
	    deferred.reject(['connection error', error]);
	});
	return deferred.promise;
    };

    function bindInput(elem, model, name) {
	elem.addEventListener('change', function(e) {
	    model.set(name, elem.value);
	});
	model.subscribe('change', function(e, info) {
	    if (info.key == name) {
		elem.value = info["new"];
	    }
	});
	model.get(name).done(function(value) {
	    elem.value = value || '';
	});
    };
    window.bindInput = bindInput;
    
    var obj = {};

    function Proxy(objId) {
	this.objId = objId;
	obj[objId] = this; // register.
	this._subs = {};
    }

    Proxy.prototype.addMethod = function(name) {
	this[name] = function() {
	    return callRemote(this.objId, name, Array.prototype.slice.call(arguments));
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
	    callRemote(this.objId, 'subscribe', [event, new BoundMethod(this.objId, '_notify')]);
	} else {
	    this._subs[event].push(cb);
	}
    };

    function logEvent(event, info) {
	console.log('notified:', event, info);
    };
    window.logEvent = logEvent;

    window.model = new Proxy('shared');
    window.model.addMethod('get');
    window.model.addMethod('set');
    window.model.addMethod('notify');
    window.model.addMethod('subscribers');

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
    window.traverse = traverse;

    function HookCls(val) {
	this.val = val;
    };

    HookCls.prototype.ext_encoding = function() {
	return {name: 'HookCls', args: [this.val]};
    };

    var hooks = {};
    hooks['HookCls'] = function(args) {
	return new HookCls(args[0]);
    };

    function BoundMethod(oid, method) {
	this.oid = oid;
	this.method = method;
    };

    BoundMethod.prototype.ext_encoding = function() {
	return {name: 'BoundMethod', args:{o: this.oid, m: this.method}};
    };

    hooks['BoundMethod'] = function(args) {
	return new BoundMethod(args.o, args.m);
    };

    // JSON extension:
    // use __ext__name_, __ext__args_ and .ext_encoding
    function preEncodeFn(data) {
	if (typeof data != 'object') return undefined;
	if (typeof data.ext_encoding != 'function') return undefined;
	var info = data.ext_encoding();
	return {__ext__name_: info.name, __ext__args_: info.args};
    }

    function postDecodeFn(data) {
	if (Object.prototype.toString.call(data) != '[object Object]') return undefined;
	if (!(data.__ext__name_ in hooks)) return undefined;
	return hooks[data.__ext__name_](data.__ext__args_);
    }

    window.preEncodeFn = preEncodeFn;
    window.postDecodeFn = postDecodeFn;

    window.HookCls = HookCls;
    window.BoundMethod = BoundMethod;
    window.Proxy = Proxy;

    window.h = new HookCls("hi");

    var conn;
    function connect() {
	if (window.ws !== undefined) {
	    if (ws.readyState < 2) return conn;
	}
	window.ws = new WebSocket('ws://' + location.hostname + '/ws/');
	conn = when.promise(function(resolve) {
	    ws.onopen = function(event) {
		console.log('connected');
		resolve();
	    };
	});
	ws.onmessage = function(event) {
	    // console.log(event.data);
	    var data = traverse(JSON.parse(event.data), postDecodeFn);
	    if ('o' in data) { // reply
		// call (currently one-way only from server)
		var prx = obj[data.o];
		var method = prx[data.m];
		var args = data.a;
		method.apply(prx, args);
	    } else {
		var deferred = pendingCalls[data.i];
		delete pendingCalls[data.i];
		if ('e' in data) {
		    deferred.reject(data.e);
		} else {
		    deferred.resolve(data.r);
		}
	    }
	};
	return conn;
    };
    window.rlog = function(result) { console.log('got:', result); }
    window.elog = function(err) { console.log('error:', err); }

    // set up binding.
    var input = document.getElementsByName('name')[0];
    var bound = false;
    function doBind() {
	if (!bound) {
	    bindInput(input, model, 'name');
	    bound = true;
	} else {
	    console.log('already bound');
	}
    }
    window.doBind = doBind;
});
