#include <tuple_codec.h>

#include <stdexcept>
#include <int_codec.h>
#include <type_codec.h>

namespace serf {

    typedef std::vector<Var> vec_var;
    
    TupleCodec::TupleCodec(std::vector<CodecP> const& codecs)
        : codecs_(codecs) {
    }
    
    std::string TupleCodec::typeName() {
        std::string name = "TUPLE(";
        size_t i, n = codecs_.size();
        for (i = 0; i < n; ++i) {
            if (i) name += ", ";
            name += codecs_[i]->typeName();
        }
        name += ")";
        return name;
    }
    
    void TupleCodec::encodeType(std::ostream& out) {
        out << type_byte;
        size_t i, n = codecs_.size();
        IntCodec ic;
        ic.encode(out, int64_t(n));
        for (i = 0; i < n; ++i) {
            codecs_[i]->encodeType(out);
        }
    }
    
    void TupleCodec::encode(std::ostream& out, Var const& value, Context& ctx) {
        encode(out, boost::get<vec_var>(value), ctx);
    }
    
    void TupleCodec::encode(std::ostream& out, std::vector<Var> const& value, Context& ctx) {
        if (value.size() != codecs_.size()) {
            throw std::runtime_error("tuple encoding size mismatch");
        }
        size_t i, n = codecs_.size();
        for (i = 0; i < n; ++i) {
            codecs_[i]->encode(out, value[i], ctx);
        }
    }
    
    void TupleCodec::decode(std::istream& in, Var& value, Context& ctx) {
        size_t i, n = codecs_.size();
        vec_var result(n);
        for (i = 0; i < n; ++i) {
            codecs_[i]->decode(in, result[i], ctx);
        }
        value = result;
    }
    
    CodecP TupleCodec::Factory::decodeType(std::istream& in, Context& ctx) {
        IntCodec ic;
        size_t i, n = ic.decodeSize(in);
        TypeCodec tc;
        std::vector<CodecP> codecs;
        for (i = 0; i < n; ++i) {
            codecs.push_back(tc.decode(in, ctx));
        }
        return CodecP(new TupleCodec(codecs));
    }
    
    char TupleCodec::Factory::typeByte() const {
        return TupleCodec::type_byte;
    }
}
