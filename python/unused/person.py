"""Demo cap with data schema."""

from fred.obj import obj

schema = {
    'firstname': 'str',
    'lastname': 'str',
    'dob': 'date',
    'city': 'str',
    'time': 'ref',
}

# This is not so pretty, having to use .get() to get work with
# the capabilities of the env (data) object. We could use
# a variant of obj which had __getitem__ and forwarded it to
# get (or getitem maybe).

def inst(env):
    def getAge():
        age = env.get('time').date() - env.get('dob')

    def name():
        return env.get('firstname') + ' ' + env.get('lastname')

    return obj(
        model=env,
        person=obj(getAge=getAge, name=name))
