#include <string_codec.h>

#include <cstring>
#include <algorithm>
#include <stdexcept>
#include <int_codec.h>

const char* STRING_TYPES = "akru";

const size_t MAX_LEN((2 << 31) - 1);

inline bool nonascii(char c) {
    return (c & 0x80);
}

bool isAscii(std::string const& s) {
    return std::find_if(s.begin(), s.end(), nonascii) == s.end();
}

StringCodec::StringCodec(char type_byte)
    : type_byte_(type_byte) {
    if (!strchr(STRING_TYPES, type_byte)) {
        throw std::runtime_error("invalid string type");
    }
}

std::string StringCodec::typeName() {
    switch (type_byte_) {
    case 'r':
        return "DATA";
    case 'u':
        return "TEXT";
    case 'a':
        return "ASCII";
    case 'k':
        return "TOKEN";
    default:
        throw std::runtime_error("unexpected string type");
    }
}

void StringCodec::encodeType(std::ostream& out) {
    out << type_byte_;
}
void StringCodec::encode(std::ostream& out, Var const& value, Context& ctx) {
    encode(out, boost::get<std::string const&>(value));
}
void StringCodec::decode(std::istream& in, Var& value, Context& ctx) {
    std::string tmp;
    decode(in, tmp);
    value = tmp;
}
void StringCodec::encode(std::ostream& out, std::string const& value) {
    Context ctx;
    if (type_byte_ == 'a' && !isAscii(value)) {
        throw std::runtime_error("string must be ascii for type a");
    }
    if (type_byte_ == 'k') {
        IntCodec IC(2);
        if (value.size() > 32767) throw std::runtime_error("string too long for type k");
        IC.encode(out, int(value.size()), ctx);
        out << value;
    } else {
        IntCodec IC;
        if (value.size() > MAX_LEN) throw std::runtime_error("string too long");
        IC.encode(out, int(value.size()), ctx);
        out << value;
    }
}
void StringCodec::decode(std::istream& in, std::string& value) {
    IntCodec ic(type_byte_ == 'k' ? 2 : 4);
    size_t len = ic.decodeSize(in);
    char *tmpStr = new char[len];
    if (!in.read(tmpStr, len)) throw std::runtime_error("premature EOF");
    value.assign(tmpStr, len);
    delete[] tmpStr;
}

StringCodec::Factory::Factory(char type_byte)
    : type_byte_(type_byte) {
}

CodecP StringCodec::Factory::decodeType(std::istream& in, Context& ctx) {
    return CodecP(new StringCodec(type_byte_));
}
char StringCodec::Factory::typeByte() const {
    return type_byte_;
}
