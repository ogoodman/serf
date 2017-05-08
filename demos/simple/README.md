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
leading underscore indicates that the serialize list member is to be
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
cache what they return so as not to have to keep recreating them. But
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
it to save. Some kind of `NullRef` object would simplify matters here.

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
    store.clearCache()
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

We actually had to try quite hard to cause this 'problem': it is only
a problem because we want one shared object rather than two separate
ones.

Suppose instead that we made *george* and saved him *before* we added
him as a friend of *fred*. Now *george* has a ref member and when we
save *fred*, instead of storing a copy of the entire referenced
*george* object we will store a `Ref`.

    storage['fred'] = f = Person('fred', 20)
    storage['george'] = g = Person('george', 20)
    
    f.addFriend(g)
    storage['fred'] = f
    
    storage.clearCache()
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

**NOTE:** why are they not recreated as instances with `ref` members, as
they were before they were saved? In fact, we consider it to be a
defect that this does not happen. It's not hard to make a change
so that this does happen, but then we run into trouble with reference
cycles. `Refs` should be usable in almost every way just like the objects
they refer to, so in practice this should not present much of a
problem.

**NOTE:** if two objects both link to a child object which has not been
made persistent, then saving and restoring the two parent objects will
result in duplication of the child. This may or may not be a problem,
but if sharing is what is wanted, the child object should be saved
first.

