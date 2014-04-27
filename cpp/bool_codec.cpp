#include <bool_codec.h>

#include <stdexcept>

std::string BoolCodec::typeName() {
    return "BOOL";
}

void BoolCodec::encodeType(std::ostream& out) {
    out << type_byte;
}

void BoolCodec::encode(std::ostream& out, Var const& value, Context& ctx) {
    encode(out, boost::get<bool>(value));
}

void BoolCodec::decode(std::istream& in, Var& value, Context& ctx) {
    char ch;
    if (!in.get(ch)) throw std::runtime_error("premature EOF");
    value = bool(ch);
}

void BoolCodec::encode(std::ostream& out, bool value) {
    out << (value ? '\x01' : '\x00');
}

CodecP BoolCodec::Factory::decodeType(std::istream& in, Context& ctx) {
    return CodecP(new BoolCodec());
}

char BoolCodec::Factory::typeByte() const {
    return type_byte;
}
