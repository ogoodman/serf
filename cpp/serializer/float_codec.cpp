#include <serf/serializer/float_codec.h>

#include <algorithm>
#include <stdexcept>
#include <boost/static_assert.hpp>

namespace serf {

    BOOST_STATIC_ASSERT(sizeof(double) == 8);
    const double ONE = 1.0;
    const bool LITTLE_ENDIAN_ = bool(((char*)&ONE)[7]);

    inline void reverse(char buf[8]) {
        std::swap(buf[0], buf[7]);
        std::swap(buf[1], buf[6]);
        std::swap(buf[2], buf[5]);
        std::swap(buf[3], buf[4]);
    }
    
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
        if (LITTLE_ENDIAN_) reverse(buf);
        value = *(double*)(buf);
    }
    
    void FloatCodec::encode(std::ostream& out, double value) {
        char buf[8];
        *(double*)buf = value;
        if (LITTLE_ENDIAN_) reverse(buf);
        out.write(buf, 8);
    }
    
    CodecP FloatCodec::Factory::decodeType(std::istream& in, Context& ctx) {
        return CodecP(new FloatCodec());
    }
    char FloatCodec::Factory::typeByte() const {
        return 'd';
    }
}
