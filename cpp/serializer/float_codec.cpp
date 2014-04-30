#include <serf/serializer/float_codec.h>

#include <stdexcept>
#include <boost/static_assert.hpp>

namespace serf {

    BOOST_STATIC_ASSERT(sizeof(double) == 8);
    
    std::string FloatCodec::typeName() {
        return "DOUBLE";
    }
    
    void FloatCodec::encodeType(std::ostream& out) {
        out << 'd';
    }
    void FloatCodec::encode(std::ostream& out, Var const& value, Context& ctx) {
        encode(out, boost::get<double>(value));
    }
    void FloatCodec::decode(std::istream& in, Var& value, Context& ctx) {
        char buf[8];
        if (!in.read(buf, 8)) throw std::runtime_error("premature EOF");
        value = *(double*)(buf);
    }
    
    void FloatCodec::encode(std::ostream& out, double value) {
        char buf[8];
        *(double*)buf = value;
        out.write(buf, 8);
    }
    
    CodecP FloatCodec::Factory::decodeType(std::istream& in, Context& ctx) {
        return CodecP(new FloatCodec());
    }
    char FloatCodec::Factory::typeByte() const {
        return 'd';
    }
}
