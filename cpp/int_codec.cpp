#include <int_codec.h>

#include <stdexcept>
#include <debug.h>

namespace serf {

    static const char* TYPE_BYTES = "-bh-i---q";
    static const char* UTYPE_BYTES = "-BH-I----";
    
    IntCodec::IntCodec(size_t width, bool sig) : width_(width), signed_(sig) {
        if (width > 8 || TYPE_BYTES[width] == '-') {
            throw std::domain_error("Invalid width for IntCodec");
        }
    }
    
    std::string IntCodec::typeName() {
        std::string s(signed_ ? "" : "U");
        switch (width_) {
        case 1:
            return s + "BYTE";
        case 2:
            return s + "INT16";
        case 4:
            return s + "INT32";
        case 8:
            return s + "INT64";
        default:
            throw std::domain_error("Invalid width for IntCodec");
        }
    }
    void IntCodec::encodeType(std::ostream& out) {
        out << (signed_ ? TYPE_BYTES : UTYPE_BYTES)[width_];
    }
    void IntCodec::encode(std::ostream& out, Var const& value, Context& ctx) {
        switch (width_) {
        case 1:
            encode(out, boost::get<byte>(value));
            break;
        case 2:
        case 4:
            encode(out, boost::get<int32_t>(value));
            break;
        case 8:
            encode(out, boost::get<int64_t>(value));
            break;
        default:
            throw std::domain_error("Invalid width for IntCodec");
        }
    }
    void IntCodec::decode(std::istream& in, Var& value, Context& ctx) {
        switch (width_) {
        case 1:
            value = byte(decode(in));
            break;
        case 2:
        case 4:
            value = int32_t(decode(in));
            break;
        case 8:
            value = decode(in);
            break;
        default:
            throw std::domain_error("Invalid width for IntCodec");
        }
    }
    void IntCodec::encode(std::ostream& out, int64_t value) {
        for (int i = int(width_) - 1; i >= 0; --i) {
            out << char((value >> 8*i) & 0xFF);
        }
    }
    int64_t IntCodec::decode(std::istream& in) {
        char ch;
        int64_t result = 0;
        for (size_t i = 0; i < width_; ++i) {
            if (!in.get(ch)) throw std::runtime_error("premature EOF");
            result <<= 8;
            if (i == 0 && signed_) {
                result += (signed char)ch;
            } else {
                result += (unsigned char)ch;
            }
        }
        return result;
    }
    size_t IntCodec::decodeSize(std::istream& in) {
        int64_t slen = decode(in);
        if (slen < 0) throw std::runtime_error("negative size");
        return size_t(slen);
    }
    
    IntCodec::Factory::Factory(size_t width, bool sig)
        : width_(width), signed_(sig) {
        if (width > 8 || TYPE_BYTES[width] == '-') {
            throw std::domain_error("Invalid width for IntCodecFactory");
        }
    }
    CodecP IntCodec::Factory::decodeType(std::istream& in, Context& ctx) {
        return CodecP(new IntCodec(width_, signed_));
    }
    char IntCodec::Factory::typeByte() const {
        return (signed_ ? TYPE_BYTES : UTYPE_BYTES)[width_];
    }
}
