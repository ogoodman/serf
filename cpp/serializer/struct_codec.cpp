#include <serf/serializer/struct_codec.h>

#include <serf/debug.h>
#include <serf/serializer/int_codec.h>
#include <serf/serializer/string_codec.h>
#include <serf/serializer/type_codec.h>

namespace serf {

    StructCodec::StructCodec(std::vector<StructCodec::Field> const& fields)
        : fields_(fields) {
    }
    
    std::string StructCodec::typeName() {
        std::string name = "STRUCT(";
        size_t i, n = fields_.size();
        for (i = 0; i < n; ++i) {
            if (i) name += ", ";
            name += "(" + repr(fields_[i].first) + ", " + fields_[i].second->typeName() + ")";
        }
        name += ")";
        return name;
    }
    
    void StructCodec::encodeType(std::ostream& out) {
        out << type_byte;
        IntCodec ic;
        StringCodec sc('k');
        size_t i, n = fields_.size();
        ic.encode(out, n);
        for (i = 0; i < n; ++i) {
            sc.encode(out, fields_[i].first);
            fields_[i].second->encodeType(out);
        }
    }
    
    void StructCodec::encode(std::ostream& out, Var const& value, Context& ctx) {
        size_t i, n = fields_.size();
        for (i = 0; i < n; ++i) {
            // Encode the value at fld.first using the encoder fld.second.
            fields_[i].second->encode(out, M(value).at(fields_[i].first), ctx);
        }
    }
    
    void StructCodec::decode(std::istream& in, Var& value, Context& ctx) {
        std::map<std::string, Var> result;
        size_t i, n = fields_.size();
        for (i = 0; i < n; ++i) {
            // Decode the value into fld.first using the encoder fld.second.
            fields_[i].second->decode(in, result[fields_[i].first], ctx);
        }
        value = result;
    }
    
    CodecP StructCodec::Factory::decodeType(std::istream& in, Context& ctx) {
        IntCodec ic;
        size_t i, n = ic.decodeSize(in);
        StringCodec sc('k');
        TypeCodec tc;
        string key;
        CodecP type;
        std::vector<Field> fields;
        for (i = 0; i < n; ++i) {
            sc.decode(in, key);
            type = tc.decode(in, ctx);
            fields.push_back(Field(key, type));
        }
        return CodecP(new StructCodec(fields));
    }
    
    char StructCodec::Factory::typeByte() const {
        return StructCodec::type_byte;
    }
}
