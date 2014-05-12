#include <serf/serializer/codec.h>

#include <sstream>
#include <serf/debug.h>

namespace serf {

    Context::~Context() {
    }

    CodecP Context::codec(int type_id, std::string& type_name) {
        return CodecP();
    }

    CodecP Context::namedCodec(std::string const& type_name, int& type_id) {
        type_id = 0;
        return CodecP();
    }

    Codec::~Codec() {
    }
    
    /*
    std::string Codec::typeName() {
        ostringstream out;
        encodeType(out);
        return "TYPE(" + repr(out.str()) + ")";
    }
    */
    
    std::string Codec::encodes(Var const& v) {
        Context ctx;
        std::ostringstream result;
        encode(result, v, ctx);
        return result.str();
    }
    
    Var Codec::decodes(std::string const& data) {
        Context ctx;
        Var v;
        std::istringstream in(data);
        decode(in, v, ctx);
        return v;
    }
    
    CodecFactory::~CodecFactory() {
    }
}

