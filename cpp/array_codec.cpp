#include <array_codec.h>

#include <int_codec.h>
#include <type_codec.h>

ArrayCodec::ArrayCodec(CodecP elem_codec) : elem_codec_(elem_codec) {
}

std::string ArrayCodec::typeName() {
    return "ARRAY(" + elem_codec_->typeName() + ")";
}
void ArrayCodec::encodeType(std::ostream& out) {
    out << 'L';
    elem_codec_->encodeType(out);
}
void ArrayCodec::encode(std::ostream& out, Var const& value, Context& ctx) {
    encode(out, boost::get<std::vector<Var> const&>(value), ctx);
}
void ArrayCodec::decode(std::istream& in, Var& value, Context& ctx) {
    std::vector<Var> result;
    decode(in, result, ctx);
    value = result;
}

void ArrayCodec::encode(std::ostream& out, std::vector<Var> const& value, Context& ctx) {
    IntCodec IC;
    IC.encode(out, int(value.size()), ctx);
    size_t i, n=value.size();
    for (i = 0; i < n; ++i) {
        elem_codec_->encode(out, value[i], ctx);
    }
}
void ArrayCodec::decode(std::istream& in, std::vector<Var>& value, Context& ctx) {
    IntCodec ic;
    size_t i, n = size_t(ic.decode(in));
    value.resize(n);
    for (i = 0; i < n; ++i) {
        elem_codec_->decode(in, value[i], ctx);
    }
}

CodecP ArrayCodec::Factory::decodeType(std::istream& in, Context& ctx) {
    TypeCodec tc;
    CodecP elem_codec = tc.decode(in, ctx);
    return CodecP(new ArrayCodec(elem_codec));
}
char ArrayCodec::Factory::typeByte() const {
    return 'L';
}
