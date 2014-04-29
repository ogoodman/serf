#include <dict_codec.h>

#include <cstring>
#include <sstream>
#include <int_codec.h>
#include <type_codec.h>
#include <string_codec.h>

namespace serf {

    typedef std::map<std::string, Var> var_dict;
    
    DictCodec::DictCodec(CodecP key_codec, CodecP elem_codec)
        : key_codec_(key_codec), elem_codec_(elem_codec)
    {
        // Check key_codec is a string type.
        std::ostringstream out;
        key_codec->encodeType(out);
        if (out.str().size() != 1) {
            throw std::runtime_error("Non-string dict keys not supported");
        }
        char key_type(out.str()[0]);
        if (!strchr(STRING_TYPES, key_type)) {
            throw std::runtime_error("Non-string dict keys not supported");
        }
    }
    
    std::string DictCodec::typeName() {
        return "DICT(" + key_codec_->typeName() + ", " + elem_codec_->typeName() + ")";
    }
    
    void DictCodec::encodeType(std::ostream& out) {
        out << 'M';
        key_codec_->encodeType(out);
        elem_codec_->encodeType(out);
    }
    void DictCodec::encode(std::ostream& out, Var const& value, Context& ctx) {
        encode(out, boost::get<var_dict const&>(value), ctx);
    }
    void DictCodec::decode(std::istream& in, Var& value, Context& ctx) {
        var_dict result;
        decode(in, result, ctx);
        value = result;
    }
    void DictCodec::encode(std::ostream& out, std::map<std::string, Var> const& value, Context& ctx) {
        IntCodec IC;
        IC.encode(out, int(value.size()), ctx);
        var_dict::const_iterator it, e = value.end();
        for (it = value.begin(); it != e; ++it) {
            key_codec_->encode(out, it->first, ctx);
            elem_codec_->encode(out, it->second, ctx);
        }
    }
    void DictCodec::decode(std::istream& in, std::map<std::string, Var>& value, Context& ctx) {
        value.clear();
        IntCodec ic;
        size_t i, n = size_t(ic.decode(in));
        Var k, v;
        for (i = 0; i < n; ++i) {
            key_codec_->decode(in, k, ctx);
            elem_codec_->decode(in, v, ctx);
            value[boost::get<std::string>(k)] = v;
        }
    }
    
    CodecP DictCodec::Factory::decodeType(std::istream& in, Context& ctx) {
        TypeCodec tc;
        CodecP key_codec = tc.decode(in, ctx);
    
        CodecP elem_codec = tc.decode(in, ctx);
        return CodecP(new DictCodec(key_codec, elem_codec));
    }
    char DictCodec::Factory::typeByte() const {
        return 'M';
    }
}
