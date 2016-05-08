import weakref
import json
from serf.traverse import traverse_ctx
from serf.serializer import POD_TYPES

class JSONCodec(object):
    """Codec for JSON with context for custom serialization."""

    def preEncodeFn(self, data, ctx):
        if isinstance(data, Exception):
            return [type(data).__name__, data.args]
        if type(data) in POD_TYPES:
            return None
        name, value = ctx.record(data)
        return {'__ext__name_': name, '__ext__args_': value}

    def encode(self, data, ctx=None):
        return json.dumps(traverse_ctx(data, self.preEncodeFn, ctx))

    def postDecodeFn(self, data, ctx):
        if type(data) is dict and '__ext__name_' in data and '__ext__args_' in data:
            if ctx is not None:
                return ctx.custom(data['__ext__name_'], data['__ext__args_'])
        return None

    def decode(self, message, ctx=None):
        return traverse_ctx(json.loads(message), self.postDecodeFn, ctx)

JSON_CODEC = JSONCodec()
