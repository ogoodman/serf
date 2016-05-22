var promise = (function() {

    function Promise() {
        this.state = 'pending';
        this.next = [];
    }

    Promise.isPromise = function(value) {
        return value && typeof value.then === 'function';
    };

    Promise.prototype.call = function(func) {
        assert(this.state === 'pending');
        // This can't throw unless this.reject throws.
        try {
            this.resolve(func());
        } catch (e) {
            this.reject(e);
        }
        return this;
    };

    Promise.prototype.resolve = function(value) {
        // This can't throw unless this.then or value.then throw.
        if (Promise.isPromise(value)) {
            value.then(null, null, this);
            return this;
        }

        this.state = 'resolved';
        this.value = value;

        for (var next of this.next) {
            this.then(next.callback, next.errback, next.next);
        }
        delete this.next;

        return this;
    };

    Promise.prototype.reject = function(reason) {
        // This can't throw unless this.then throws.
        this.state = 'rejected';
        this.value = reason;

        for (var next of this.next) {
            this.then(next.callback, next.errback, next.next);
        }
        delete this.next;

        return this;
    };

    Promise.prototype.then = function(callback, errback, next) {
        // This can't throw unless next.resolve, next.reject or
        // next.call throws.

        if (next === false) {
            this.done(callback, errback);
            return;
        }

        if (!next) {
            next = new Promise();
        }

        if (this.state === 'resolved') {
            if (callback) {
                next.call(() => callback(this.value));
            } else {
                next.resolve(this.value);
            }
        } else if (this.state === 'rejected') {
            if (errback) {
                next.call(() => errback(this.value));
            } else {
                next.reject(this.value);
            }
        } else {
            this.next.push({next: next, callback: callback, errback: errback});
        }
        return next;
    };

    Promise.prototype.done = function(callback, errback) {
        if (this.state === 'resolved') {
            if (callback) {
                try {
                    callback(this.value);
                } catch (e) {
                    Promise.uncaught(e);
                }
            }
        } else if (this.state === 'rejected') {
            if (errback) {
                try {
                    errback(this.value);
                } catch (e) {
                    Promise.uncaught(e);
                }
            } else {
                Promise.uncaught(this.value);
            }
        } else {
            this.next.push({next: false, callback: callback, errback: errback});
        }
    };

    Promise.prototype.show = function() {
        this.done(v => console.log(v));
    };

    Promise.uncaught = function(e) {
        console.log('Uncaught', e);
    };

    Promise.lift = function(value) {
        return value.then ? value : (new Promise()).resolve(value);
    }

    Promise.gather = function(promises) {
        function append(p) {
            return l => p.then(value => { l.push(value); return l; });
        }
        var l = Promise.lift([]);
        for (var p of promises) {
            l = l.then(append(p));
        }
        return l;
    }

    // Promise.funcToAsync converts a Promise-returning function
    // to regular async JS style.
    //
    // The errh is an optional error handler which takes an
    // exception and produces a result to pass to the callback.
    // If it is not provided and func_p fails, the callback
    // is never called.

    Promise.funcToAsync = function(func_p, errh) {
        return function(arg, callback) {
            var result = func_p(arg);
            if (result.then) {
                result.then(callback, e => errh && callback(errh(e)));
            } else {
                callback(result);
            }
        };
    };

    // Promise.funcFromAsync converts an async JS style function
    // to one which returns a promise.
    //
    // Any exception thrown by func will be captured.

    Promise.funcFromAsync = function(func) {
        return function(arg) {
            var promise = new Promise();
            try {
                func(arg, v => promise.resolve(v));
            } catch (e) {
                promise.reject(e);
            }
            return promise;
        };
    };

    return {Promise: Promise};
})();
