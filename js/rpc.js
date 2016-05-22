//#include promise.js

var rpc = (function() {

    var Promise = promise.Promise;

    /**
     * Provides RPC between client-side javascript and a Serf-WS server.
     * @module serf/rpc
     */

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
            var i=0, n=data.length;
            for (i=0; i<n; ++i) {
                r = traverse0(data[i], fn);
                if (r !== undefined) data[i] = r;
            }
            return undefined;
        }
        if (t == '[object Object]') {
            var k;
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

    /**
     * Represents a Serf/WS server connection.
     * @constructor
     * @param {string} url Websocket URL for the server
     */
    function WSServer(url) {
        this.url = url;
        this.callId = 0;
        this.pendingCalls = {};
        this.onopen = function() {};
        this.onclose = function() {};
        this.obj = {};
    };

    /**
     * Factory functions for embedded records.
     */
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
        this.conn = new Promise();
        this.ws = new WebSocket(that.url);
        this.ws.onopen = e => {
            that.onopen();
            that.conn.resolve();
        };
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
                    if (data.O) {
                        that.sendRemote({
                            o: data.O, // reply object (callback id)
                            r: result || null
                        });
                    }
                } catch (ex) {
                    if (data.O) {
                        that.sendRemote({
                            o: data.O, // reply object (callback id)
                            e: [ex.constructor.name, ex.message]
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
            O: this.callId
        };
        var promise = this.pendingCalls[this.callId] = new Promise();
        this.connect().done(function() {
            that.ws.send(JSON.stringify(traverse(msg, preEncodeFn)));
        }, function(error) {
            promise.reject(['connection error', error]);
        });
        return promise;
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
        };
        return mcall;
    }

    let handler = {
        get(remote, name) {
            if (name === 'then') {
                // Automatically adding 'then' confuses Promise.isPromise.
                return undefined;
            }
            if (!remote[name]) {
                remote.addMethod(name);
            }
            return remote[name];
        }
    };

    /**
     * Represents a server-side object.
     * @constructor
     * @param {WSServer} server Server where the object resides
     * @param {string} objId Id of a server-side object
     */
    function Ref(server, objId, node) {
        this.server = server;
        this.objId = objId;
        this.node = node || 'server';
        if (this.node == 'server') {
            this.server.obj[objId] = this; // register.
        }
        this._subs = {};
    }

    /**
     * Makes a proxy for the named server-side object.
     * @param {string} objId Id of a server-side object
     */
    WSServer.prototype.getProxy = function(objId, node) {
        return new Proxy(new Ref(this, objId, node), handler);
    };

    /**
     * Add a method stub to the proxy.
     *
     * A newly created Ref does not know what server-side
     * methods are available. We have to add method stubs for
     * each method we want to be able to call.
     *
     * @param {string} name Method name to add
     */
    Ref.prototype.addMethod = function(name) {
        var that = this;
        this[name] = function() {
            return that.server.callRemote(that.objId, name, Array.prototype.slice.call(arguments));
        };
    };

    Ref.prototype._notify = function(event, info) {
        var subs = this._subs[event] || [];
        var i, n = subs.length;
        for (i = 0; i < n; ++i ) subs[i](event, info);
    };
    
    /**
     * Subscribe to an event of the server-side object.
     * <p>The callback function will be passed (event-name, event-info).
     *
     * @param {string} event Event name
     * @param {function} cb Callback
     */
    Ref.prototype.subscribe = function(event, cb) {
        if (!(event in this._subs)) {
            this._subs[event] = [cb];
            this.server.callRemote(this.objId, 'subscribe', [event, new BoundMethod(this.objId, '_notify')]);
        } else {
            this._subs[event].push(cb);
        }
    };

    Ref.prototype.ext_encoding = function() {
        return {name: 'Proxy', args:{o: this.objId, n:this.node}};
    };

    WSServer.prototype.hooks['Proxy'] = function(server, args) {
        // Unlikely that server would send us proxy to our own object
        // but nonetheless there should be no harm in resolving it
        // to a direct reference to the object.
        if (args.n == 'browser') return this.obj[args.o];
        return new Proxy(new Ref(server, args.o), handler);
    };

    /**
     * Creates and adds hooks for a new POD (plain old data) class.
     * 
     * For this to work the server must register a class having the same
     * name and constructor argument list.
     * 
     * Example:
     *   // Having registered QTerm we can send one to the server.
     *   QTerm = makePODClass('QTerm', ['field', 'condition', 'value']);
     *   res_p = tproxy.select(QTerm(':name', 'eq', 'Fred'));
     *
     * @param {string} name Name for matching class on server
     * @param {array} params Argument and member names
     */
    function makePODClass(name, params) {
        var Cls = function() {
            for (var i = 0, n = params.length; i < n; ++i) {
                this[params[i]] = arguments[i];
            }
        };
        Cls.prototype.ext_encoding = function() {
            var values = [];
            for (var i = 0, n = params.length; i < n; ++i) {
                values[i] = this[params[i]];
            }
            return {name: name, args: values};
        }
        rpc.WSServer.prototype.hooks[name] = function(server, args) {
            function ClsB() {
                return Cls.apply(this, args);
            }
            ClsB.prototype = Cls.prototype;
            return new ClsB;
        };
        return Cls;
    }

    return {
        WSServer: WSServer,
        BoundMethod: BoundMethod,
        makeBoundMethod: makeBoundMethod,
        makePODClass: makePODClass
    };
})();
