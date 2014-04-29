#include <null_codec.h>

namespace serf {

    std::string NullCodec::typeName() {
        return "NULL";
    }
    void NullCodec::encodeType(std::ostream& out) {
        out << '-';
    }
    
    void NullCodec::encode(std::ostream& out, Var const& value, Context& ctx) {
    }
    void NullCodec::decode(std::istream& in, Var& value, Context& ctx) {
        value = boost::blank();
    }
    
    CodecP NullCodec::Factory::decodeType(std::istream& in, Context& ctx) {
        return CodecP(new NullCodec());
    }
    char NullCodec::Factory::typeByte() const {
        return '-';
    }
}
