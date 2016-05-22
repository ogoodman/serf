//#include promise.js

var Promise = promise.Promise;

function listEq(a, b) {
    if (a.length != b.length) return false;
    for (var i=0, n=a.length; i < n; ++i) {
        if (a[i] != b[i]) return false;
    }
    return true;
}

// TEST1: resolving a promise causes the result to be passed
// to the callbacks added via Promise.then.

var p = new Promise();

assert(p.value === undefined);
assert(p.state === 'pending');

p.resolve(42);

assert(p.value === 42);
assert(p.state === 'resolved');

p = new Promise();

p.reject('bang');

assert(p.value === 'bang');
assert(p.state === 'rejected');

// TEST2: we can use .then to transform a Promise's result. If
// we don't handle the exception it passes through unchanged.

p = new Promise();
var q = p.then(n => n + 1); // transform the result.

p.resolve(42);

assert(q.value === 43);
assert(q.state === 'resolved');

p = new Promise();
q = p.then(n => n + 1);

p.reject('bang'); // unhandled exception reaches q.

assert(q.state === 'rejected');
assert(q.value === 'bang');

// TEST3: we can use .then to catch (transform) errors.

function handleBang(error) {
    if (error == 'bang') {
        return 0;
    }
    throw error;
}

p = new Promise();
q = p.then(null, handleBang);

p.resolve(3); // normal results are passed to q unchanged

assert(q.value === 3);

p = new Promise();
q = p.then(null, handleBang);

p.reject('bang'); // this will be converted to a normal result

assert(q.value === 0);
assert(q.state === 'resolved');

p = new Promise();
q = p.then(null, handleBang);

p.reject('boom');

assert(q.state === 'rejected');
assert(q.value === 'boom');

// TEST4: Promise.lift turns an ordinary value into a Promise.

p = Promise.lift(15);

assert(p.value === 15);
assert(p.state === 'resolved');

// TEST5: Promise.gather turns a list of promises into a promise for the list of values.

p = new Promise();
q = new Promise();

var l = Promise.gather([p, q]);

assert(l.value === undefined);

q.resolve(2);

assert(l.value === undefined);

p.resolve(1);

assert(listEq(l.value, [1, 2]));
assert(l.state === 'resolved');

// If there is an exception, we will get it.

p = new Promise();
q = new Promise();
var l = Promise.gather([p, q]);

q.reject('bang');
assert(l.state === 'pending');
p.resolve(1);
assert(l.state === 'rejected');
assert(l.value === 'bang');

// We get the first exception in list order (rather than time order).

p = new Promise();
q = new Promise();
var l = Promise.gather([p, q]);

q.reject('bang');
assert(l.state === 'pending');
p.reject('boom');
assert(l.state === 'rejected');
assert(l.value === 'boom');

// We can get an error even before all items have resolved.

p = new Promise();
q = new Promise();
var l = Promise.gather([p, q]);

p.reject('boom');
assert(l.state === 'rejected');
assert(l.value === 'boom');
q.resolve(2);
assert(l.state === 'rejected');
assert(l.value === 'boom');

// TEST6: done / uncaught exceptions.

var v;
var uncaught = null;
Promise.uncaught = e => { uncaught = e; };

p = new Promise();

p.done(val => { v = val; });
p.resolve(42);

assert(v === 42);
assert(uncaught === null);

p = new Promise();

p.resolve(43);
p.done(val => { v = val; });

assert(v === 43);
assert(uncaught === null);

p = new Promise();

p.reject('boom');
p.done(val => { v = val; });

assert(uncaught === 'boom');

p = new Promise();

p.done(val => { v = val; });
p.reject('bang');

assert(uncaught === 'bang');

p = new Promise();

p.resolve(44);
p.done(val => { throw 'oops'; });

assert(uncaught === 'oops');

p = new Promise();

p.done(val => { throw 'splat'; });
p.resolve(45);

assert(uncaught === 'splat');

uncaught = null;

p = new Promise();

p.done();
p.resolve(46);

assert(uncaught === null);

p = new Promise();

// Error handler would fail, but not called.
p.done(null, e => { throw 'ouch'; });
p.resolve(47);

assert(uncaught === null);

p = new Promise();

// Error handler would fail, but not called.
p.resolve(47);
p.done(null, e => { throw 'ouch'; });

assert(uncaught === null);

p = new Promise();

// Error handler failure.
p.done(null, e => { throw 'ouch'; });
p.reject('boom');

assert(uncaught === 'ouch');

p = new Promise();

// Error handler failure.
p.reject('boom');
p.done(null, e => { throw 'ooh'; });

assert(uncaught === 'ooh');

print("all good!");
