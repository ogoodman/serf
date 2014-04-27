#include <codec.h>

#include <sstream>
#include <debug.h>

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

