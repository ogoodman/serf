Persistence and Remote Procedure Calls (RPC)
============================================

In this demo we explore these two features of Serf, as supported by
the Serf serialization protocol.

Object Persistence
------------------

### Backing stores

Start a python shell in this directory. Enter:

    from demo import *

The `DATA_DIR` variable should have been set to `'.serf-data/client'`
under your home directory. We will store some persistent objects
there. 

First we create a simple wrapper for the contents of this directory
which enables us to use it like a python dict.

    store = FSDict(DATA_DIR)
    store['name'] = 'Fred'

Then:

    store['name']  # --> 'Fred'

should return `'Fred'`. We can quit the shell and examine the contents
of the `DATA_DIR` directory. We should see a file called `'name'` whose
contents consist just of the word `'Fred'` (without any newline).

Return to the python shell. The `demo` module in fact already defines
store for us:

    from demo import *
    store['name']

To remove a value:

    'name' in store  # --> True

    del store['name']

    'name' in store  # --> False

`FSDict` gives a very simple wrapper on the file system enabling us to
treat it like a dict whose keys and values are strings. There are some
restrictions on what keys we can use: they must be valid file-system
paths. `FSDict` should prevent us from using keys that might take us
outside its root directory.

Other objects can implement this same simple interface. We will return
to this point shortly.

### Storing data

To store values other than just strings we can now do:

    storage = Storage(store)
    storage['n'] = 42
    storage['list'] = [1, 2.5, None, 'Fred']
    storage['dict'] = {'a': 1, 'b': -1}

and so on. We can retrieve the values in the obvious way:

    storage['n']     # --> 42
    storage['list']  # --> [1, 2.5, None, 'Fred']
    storage['dict']  # --> {'a': 1, 'b': -1}

When we quit the shell and start over, our values will still be there.

Each object has been encoded using the Serf serialization
protocol. To see what it looks like you can read from the backing
store:

    store['n']    # --> 'i\x00\x00\x00*'
    store['list'] # --> 'LA\x00\x00 ... \x00\x00\x04Fred'

The `Storage` object doesn't care what backing store we use. In unit
tests we can use a dict:

    store = {}
    storage = Storage(store)
    storage['n'] = 99

    storage = Storage(store)
    storage['n']  # --> 99

Persistence is still happening. Object lifetimes are determined by the
backing store.

Depending on the use-case, other backing stores are possible: just
about any kind of key-value store, local or networked, can readily be
adapted to the dict-like interface required by `Storage`. (We would have
to change things slightly to retrieve objects asynchronously; this is
not currently supported.)

Even with plain-old-data, the Serf protocol handles a few things which
JSON won't. You can store `datetime` instances and dictionaries whose
keys are not just strings. The distinction between `str` (binary) and
`unicode` (text) is preserved and there is no restriction on what a
binary string can contain.

### Storing objects

We would like to store more than just data. Persistent objects are
often layered over databases; this technique has names like *ORM* or
*active-record*.

Python `pickle` and `shelve` allow us to save python objects and
retrieve them. We don't want to underestimate what these tools can do
but we're going to go a slightly different path. We want more
control over how object-graphs (multiple objects linked by references)
are stored, and a bit more control over versioning.

In `demo.py` there is a `Person` class:

    class Person(object):
        serialize = ('name', 'age', 'friends')
    
        def __init__(self, name, age, friends=None):
            self.name = name
            self.age = age
            self.friends = friends or []
        #...

Unlike with `pickle`, we have to explicitly name all the members that
make up the state of an object. When the object is stored, the named
properties will be read from the object; the object must have
members exactly matching the serialize list (actually a `tuple`).

When the object is recreated from storage, the values in the
serialize list are passed to the `__init__` method in the order they
appear.

The serialize list names the constructor arguments required to
construct this kind of object. The arguments required to re-construct
the object must be present as members.

We can have as many other members as we want not in the serialize
list. As with any python class, we will normally set them in the
`__init__` method. 

In case you are worried at this point that program-wide resources like
logging can only be accessed by via global variables, don't be.
References to such things can be added to the `Storage` instance as
resources:

    storage.resources['#log'] = the_logger

then:

    class Person(object):
        serialize = ('#log', 'name', 'age', 'friends')
    
        def __init__(self, log, name, age, friends=None):
            self.log = log
            # etc ...

enables `the_logger` to be passed to each instance that needs it. The
leading `#` indicates that the serialize list member is to be
provided to `__init__` from the resources dictionary, but ignored when
storing the object.

You could use global variables but they are best avoided as they tend
to play badly with tests and make code harder to reason about.

If you change a class definition to add a new serialize list member,
instances which were saved before the addition will receive the value
`None` for the newly added member. If you remove a serialize list
member it will simply be ignored when loading previously stored
instances. More complex versioning is also supported and will be
discussed later.

**NOTE:** you can change serialized member names by adding or removing
a leading underscore without changing the serialization: the
dictionary of values to be serialized uses member names with leading
underscores stripped. The names in the serializer list must still
match the member variable names however. A serializer list must not
include two names which differ only by leading underscores.

Let's store a `Person`:

    storage['fred'] = Person('fred', 19)
    storage['fred']  # --> Person('fred',19,[])

Let's give *fred* a birthday:

    f = storage['fred']
    f.haveBirthday()
    f  # --> Person('fred',20,[])

At this point *fred* hasn't been saved. The `Storage` object has no way
of knowing that the internals of *fred* have changed, and in any case,
we might want to make a number of changes before writing back to
storage. We have to do it explicitly:

    storage['fred'] = f

**NOTE:** if you examine `storage['fred']` rather than `f` before saving, you
will see that they look identical and both have an age of 20 now. They
are both references to the same object in memory. `Storage` instances
cache what they return so as not to create multiple instances. But
the object won't be written to the backing store until it is assigned
back to the `Storage` slot.

The same issue arises with mutable plain-old-data like lists and
dicts: after changing their contents we must explicitly save.

For classes with a serialize list we have a second option for saving
back to the store, namely `f.ref._save()`.

#### The ref member

Whenever instances of a class with a serialize list are saved or
retrieved from `Storage` they have a special `ref` member added. If we
examine it we will see this:

    f.ref  # --> ~Person('fred',20,[]) @ fred

The `ref`, which is an instance of `serf.ref.Ref`, contains a reference to
the storage and the slot key. It functions as a proxy to *fred* in
that attribute access delegates back to the *fred* instance:

    f.age     # --> 20
    f.ref.age # --> 20

Because it is attached to the `Person` instance,
`Person` methods can call `self.ref._save()` to write the object back into
the backing store.

**NOTE:** we have to be careful to check that `self.ref` exists before using
it to save. See 'the `_save` trick' below for a better solution.

You can think of a `Ref` as a single slot, detached from the storage. The
`Ref` doesn't directly reference any *fred* instance. We can create a
`Ref` to `storage['fred']` without causing *fred* to be
instantiated. Of course, as soon as we do anything with it, the store
will be called upon to instantiate the stored object.

#### Nested objects v.s. object references

Now we will give *fred* a friend and save:

    f = storage['fred']
    f.addFriend(Person('george', 19))
    
    f  # --> Person('fred',19,[Person('george',19,[])])
    
    storage['fred'] = f

Now we have a `Person` instance with another `Person` nested inside it.
That's fine and sometimes it is exactly what you want. 

But perhaps you were going to store *george* and retrieve him via the
`'george'` slot, a person in his own right. Don't do it just yet!

    g = f.friends[0]

Now `g` and `f.friends[0]` are references to the same python object. If
*george* has a birthday:

    g.haveBirthday()
    g  # --> Person('george',21,[])
    f  # --> Person('fred',20,[Person('george',21,[])])

there is only one *george* and this is just what we want. Now let's save
everything, and reload from backing store. Save *fred* first, then
*george*:

    storage['fred'] = f
    storage['george'] = g

    del f, g  # See discussion of caching below.

    f = storage['fred']
    g = storage['george']

If you have done things in the order given you should see this:

    f  # --> Person('fred',20,[Person('george',21,[])])
    g  # --> Person('george',21)

but now we have cloned *george* which is not really what we wanted:

    f.friends[0] == g  # --> False

If we give one of the *georges* a birthday, the other one will not
change.

    g.haveBirthday()
    f  # --> Person('fred',20,[Person('george',21,[])])
    g  # --> Person('george',22)

We actually had to try quite hard to cause this problem: it is only
a problem because we want one shared object rather than two separate
ones.

Suppose instead that we made *george* and saved him *before* we added
him as a friend of *fred*. Now *george* has a `ref` member and when we
save *fred*, instead of storing a copy of the entire referenced
*george* object we will store a `Ref`.

    storage['fred'] = f = Person('fred', 20)
    storage['george'] = g = Person('george', 20)
    
    f.addFriend(g)
    storage['fred'] = f
    
    del f, g
    storage['fred']  # --> Person('fred',20,[~Person('george',20,[]) @ george])
    
    g = storage['george']
    g.haveBirthday()
    
    storage['fred']  # --> Person('fred',20,[~Person('george',21,[]) @ george])
  
To recap, if we want to nest one entire serializable instance inside
another and have it come back that way, we can just do it. As long as
the nested object has not itself been stored (has no `ref` member) it
will be stored in its entirety.

If we store an object and its referenced sub-objects are themselves
persistent objects (they have been stored and have a `ref` member) they
will be saved and recreated as `Refs`.

**NOTE:** why are they not recreated as instances with `ref` members,
as they were before they were saved? Although this would be possible,
it would create a situation where entire object networks are
instantiated eagerly: with large networks of persistent objects, this
is very undesirable. `Refs` should be usable in almost every way just
like the objects they refer to and they give us lazy instantiation.

**NOTE:** if two objects both link to a child object which has not been
made persistent, then saving and restoring the two parent objects will
result in duplication of the child. This may or may not be a problem,
but if sharing is what is wanted, the child object should be saved
first.

#### The `_save` trick

As we have noted, persistent objects can call `self.ref._save()` to
ensure that their persistent state is saved whenever it changes.

Unfortunately this approach has the drawback that it won't work until the
object gets its `ref` member. Since we might want to do various things
with a new persistent object before we first save it, it seems we
should write a `_save` method which checks for the `ref` member first.

In fact, we can simply write a do-nothing `_save` method and `Storage`
will automatically replace it with a working one whenever the object
is saved or instantiated.

A `_save` method will also be added to any nested persisted instances
that have a `_save` method place-holder, even though they won't get
their own `ref`. The added method will save the persistent object (the
one with the `ref`) in which it is contained. This enables it to ensure
that changes to its own persistent state do not go unsaved.

Because writing

    def _save(self):
        pass

is highly confusing, we recommend instead importing `save_fn` from
`serf.storage` and doing

    _save = save_fn

in the class. Then if the reader wonders what this method does, they
will at least see an explanation as to why it does nothing.

#### Caching

When objects own resources, we try to avoid instantiating multiple
owners for the same resource. Persistent objects own their storage so
we should not make multiple instances of one. If `Storage` simply
created a new instance each time we called `storage[]` we could easily
run into problems:

    f1 = storage['fred']
    f2 = storage['fred']

    f1.name = 'Frederick'
    f1._save()
    f2.age = 21
    f2._save()

In fact, `Storage` caches any values it instantiates in a
`WeakValueDictionary` so that both `f1` and `f2` above will be
references to the same object. A `WeakValueDictionary` forgets a value
as soon as the last normal reference goes away, so once both `f1` and
`f2` go out of scope, or are deleted or assigned new values, the cache
entry will go too.

This kind of caching has nothing to do with performance. If we want to
avoid repeatedly reinstantiating objects we should save normal
references to them for as long as is appropriate. Its purpose is to
ensure that we don't inadvertently end up with multiple instances
saving to the one storage slot.

Events and Subscriptions
------------------------

Events and subscriptions are very good for reducing coupling. If
object A knows about object B, i.e. it holds a reference to it, A can
call methods of B when A wants to. But suppose A wants to know when
something happens to B. If we give B a reference to A we have started
putting knowledge of A into B and reusability of B suffers. The
solution is to make B a *publisher*, an object which exposes a uniform
interface allowing any object that has a reference to it to be called
when *conditions of interest* arise in B.

A good example is the Model-View-Controller pattern.

* Models model something and publish events whenever
  something changes.

* Views reference models in order to read initial values and subscribe
  for changes. They produce events in response to user actions.

* Controllers reference views in order to respond to user actions and
  update models and views accordingly.

The flow of data is *cyclic*, e.g. a click on some part of a view
component results in an event to the controller, a call to the model,
and finally an event back to the view reflecting the change in the
model. But importantly, references are *acyclic*, flowing from
controllers to views to models, with the result that models and views tend to be
quite reusable.

### Subscribing to a model

Start a python shell in this directory and enter:

    from model import *

This brings in a slightly different `Person` class from
before. `Person` is now derived from `Publisher`, giving it
`subscribe`, `unsubscribe` and `notify` methods.

To send an event the `Person` calls `self.notify`:

    def haveBirthday(self):
        """Adds one to the age."""
        self.age += 1
        self.notify('info', {'age': self.age})

Make a person and a subscriber:

    tom = Person('Tom', 3)
    s = Subscriber()

    tom.subscribe('info', s.onEvent)  # --> a subscription id

We can ignore the subscription id for now. It provides one of several
different ways to unsubscribe should the need arise.

    tom.haveBirthday()

    # prints:
    # onEvent('info', {'age': 4})

The source of the subscription is not provided to the subscriber but
we can add any extra information we want at the time we make the
subscription:

    tom.subscribe('info', s.onEvent, args=('tom',))
    tom.haveBirthday()

    # prints:
    # onEvent('info', {'age': 5}, 'tom')

Subscriptions are keyed on the event name and the receiver
instance.

`Publishers` only hold weak references to their subscribers. When the
last normal reference to a subscriber goes away it is garbage
collected in the usual way and any subscriptions will be discarded.
Python uses reference counting so that, in the absence of reference
cycles, subscribers and their subscriptions will go away as soon
as the last normal reference is dropped.

    del s
    tom.haveBirthay()

    # prints nothing.

**NOTE:** this can occasionally cause unexpected behaviour. If you
create some kind of subscriber adapter, such as a lambda, for the sole
purpose of passing as the event callback, it will be immediately
discarded unless you keep a normal reference to it somewhere that will
last as long as you need it to.

In cases where an explicit unsubscribe is required, we can pass the
identical callback or the numeric subscription id that was returned from
the subscribe call.

### Persistent subscriptions

Our `Person` model is all ready to be made persistent.

    storage['t'] = tom

This does not change anything with regard to subscriptions made by
non-persistent objects. Bound methods to non-persistent objects cannot
be serialized and reinstantiated, so the subscription will last as
long as both publisher and subscriber remain in memory. If the
persistent publisher is discarded and re-instantiated, any normal
subscriptions will be gone.

    s = Subscriber()
    tom.subscribe('info', s.onEvent)

    storage['t'] = tom

    tom.haveBirthday()  # prints something.

    del s, tom
    tom = storage['t']

    tom.haveBirthday()  # prints nothing.

When both publisher and subscriber are persistent, we can make
persistent subscriptions:

    storage['s'] = s = Subscriber()

    tom.subscribe('info', s.onEvent, how=PERSISTENT)

    tom.haveBirthday()  # prints something

    del s, tom
    tom = storage['t']

    tom.haveBirthday()  # prints something!

We can quit the python shell, restart, give *tom* another birthday and
once again the message will be printed.

    from model import *

    storage['t'].haveBirthday()  # prints something.

**NOTE:** although this is straightforward and works, this is not the
recommended way to make persistent subscriptions in a serious
application. See the section on Notifier objects for a better
solution in such cases.

> What are persistent subscriptions good for? 

Suppose in our application we want to maintain a collection of
users. We want the collection to behave like a database table over
which we can query by name or age. We want the collection to publish
an event when the details of a user change so that UI code can bind to
the collection and show all users in a grid which tracks the changes.

We can implement this using persistent subscriptions. When a user
object is added to the collection, the collection makes a persistent
subscription to the object. When user details change the collection is
then notified and updates itself accordingly.

Serf has such a `Collection` class, based on the `Table` class.
We will look at how this works rather than trying to design a
collection class from scratch.

First a quick look at the `Table` class:

    tbl = Table()
    tbl.insert({'name': 'Tom', 'age': 10})  # -> [4], a primary key
    tbl.get(4)  # -> {'age': 10, 'name': 'Tom'}
    
    tbl.values()  # -> [{'age': 10, 'name': 'Tom'}]
    tbl.values(QTerm(':name', 'eq', 'Tom'))  # as above
    tbl.values(QTerm(':name', 'eq', 'Dick'))  # -> []
    
    q = QTerm(':name', 'eq', 'Tom')
    tbl.update(q, [FieldValue(':age', 11)])
    tbl.get(4)  # -> {'age': 11, 'name': 'Tom'}

`Tables` are `Publishers`:

    ts = Subscriber()
    tbl.subscribe('change', ts.onEvent)
    
    tbl.update(q, [FieldValue(':age', 12)])
    # prints:
    # onEvent('change', (key=4, value={'age': 12, 'name': 'Tom'}, old={'age': 11,...}))
    
A `Collection` contains a `Table` and exposes most of its methods. In
order to be able to add an object to a collection the object must have a
method giving the information about itself to be inserted into the
table, and another one which gives a unique id for itself.

    storage['t'] = t = Person('Tom', 10)
    
    t.getInfo()  # -> {'age': 10, 'name': 'Tom'}
    t.getId()    # -> 't' - the storage path

We will go ahead and add *tom* and another person to a collection.

    storage['d'] = d = Person('Dick', 9)
    storage['c'] = c = Collection()
    
    c.add(t)
    c.add(d)
    
    c.values()  # -> [{'id': 't', 'age': 10, 'name': 'Tom', 'sid': ...}, ...]
    
    # with q as before..
    c.values(q)  # -> {'id': 't', 'age': 10, 'name': 'Tom', 'sid': ...}
    
    t.haveBirthday()
    c.values(q)  # -> {'id': 't', 'age': 11, 'name': 'Tom', 'sid': ...}

The subscription has caused our `Collection` to be updated when
*tom's* age changed. If you subscribe to the `Collection` `'change'`
event, you will effectively be subscribed to `'info'` events from
all the objects in the collection.

#### Notifier objects

Subscribing by event name and callback method is fine in simple cases,
but for persistent subscriptions it is actually not ideal. Suppose we
have a subscription like this:

    publisher.subscribe('info', sub.onInfoChange)

If we later decide that we also need so subscribe to `'size'` events
and that an `onChange` method should handle both events we can just
turn that into:

    publisher.subscribe('info', sub.onChange)
    publisher.subscribe('size', sub.onChange)

We restart the program and all subscriptions are made afresh.

But if the original subscription was persistent, we aren't going to be
subscribing again just because we restarted the server. We need to
write migration code to go through all existing subscriptions,
unsubscribe the old ones, and make the new ones we want.

A partial solution is to use catch-all event handlers:

    publisher.subscribe('*', sub.onEvent)

Now `onEvent` can filter the events it receives and respond
appropriately. If we want it to handle a new event, a code change and
a restart is all that is required.

The down-side to this is that `publisher` might produce a lot of
events that are of no interest to `sub` and it might be costly for it
to produce them all. If `sub` is remote (which we will come to soon)
there is also the cost of delivering the redundant events.

A better solution is to use a *notifier* object. Instead of calling
`publisher.subscribe` with the event name and the rest, we call
`publisher.addSub` passing a single notifier object.

For persistent subscriptions the simplest way to make a notifier is to
inherit from `serf.publisher.NotifierMixin`. Here is what
the `serf.tables.collection.Notifier` looks like:

    class Notifier(NotifierMixin):
        def wants(self, event):
            return event == 'info'
    
        def notify(self, event, info):
            update = [FieldValue(':' + k, v) for k, v in info.iteritems()]
            self.receiver.update(Key(':id str', self.arg), update)

In this code `self.receiver` is the collection, while `self.arg` is
the object id. These are set by the inherited `NotifierMixin`
constructor which we will come to in a moment.

The `wants` method returns `True` if it is interested in a particular
event. If it returns `False` the publisher may not even need to
generate info for the event.
The `notify` method delivers the event to the receiver.

The `NotifierMixin` constructor looks like this:

    notifier = NotifierMixin(receiver, arg, sid=None)

If no `sid` (subscriber id) is given, a random number will be
generated and exposed as `notifier.sid`. When an object is added to a
`Collection` a subscription is made as follows:

    id = obj.getId()
    notifier = Notifier(self, id)  # self is the Collection
    obj.addSub(notifier)

We can see that `notifier.notify` uses the object's unique id
(stored in `notifier.arg`) to look up the correct row of the table,
and updates it using key-value pairs from the event info.

The subscriber id generated when the notifier was made is stored in
the table. When the time comes to remove the object:

    notifier = Notifier(self, id, sid)
    obj.removeSub(notifier)

`NotifierMixin` objects use the subscriber id to determine object
equality.

Returning to our motivating example, we would have started with a
notifier like this:

    class Notifier(NotifierMixin):
        def want(self, event):
            return event == 'info'
        def notify(self, event, info):
            self.receiver.onInfoChange(event, info)

We can deal with the changed requirements by changing the code to:

    class Notifier(NotifierMixin):
        def want(self, event):
            return event in ('info', 'size')
        def notify(self, event, info):
            self.receiver.onChange(event, info)

**NOTE:** although this is initially a bit more work than
method-based subscriptions, it is a picnic compared to the trouble you
will unleash if you use the latter for persistent subscriptions.

**NOTE:** another advantage of notifier based subscriptions is that
you don't necessarily have to add any special-purpose event handling
methods to your subscriber class. You can see this in the `Collection`
case: only the existing table `update` method is needed handle the
event.

