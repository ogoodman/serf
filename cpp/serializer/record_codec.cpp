#include <serf/serializer/record_codec.h>

#include <serf/serializer/int_codec.h>
#include <serf/serializer/string_codec.h>
#include <serf/serializer/any_codec.h>

namespace serf {

    std::string RecordCodec::typeName() {
        return "RECORD";
    }

    void RecordCodec::encodeType(std::ostream& out) {
        out << type_byte;
    }

    void RecordCodec::encode(std::ostream& out, Var const& value, Context& ctx) {
        throw std::runtime_error("Use AnyCodec to encode Records.");
    }

    void RecordCodec::decode(std::istream& in, Var& value, Context& ctx) {
        StringCodec token('k');
        std::string type_name;
        token.decode(in, type_name);
        AnyCodec ac;
        Var body;
        ac.decode(in, body, ctx);
        value = Record(type_name, body);
    }

    CodecP RecordCodec::Factory::decodeType(std::istream& in, Context& ctx) {
        return CodecP(new RecordCodec);
    }

    char RecordCodec::Factory::typeByte() const {
        return type_byte;
    }

    std::string MessageCodec::typeName() {
        return "MESSAGE";
    }

    void MessageCodec::encodeType(std::ostream& out) {
        out << type_byte;
    }

    void MessageCodec::encode(std::ostream& out, Var const& value, Context& ctx) {
        throw std::runtime_error("Use AnyCodec to encode Records.");
    }

    void MessageCodec::decode(std::istream& in, Var& value, Context& ctx) {
        IntCodec ic;
        int type_id = ic.decode(in);
        StringCodec data('r');
        std::string tmp;
        data.decode(in, tmp);
        std::string type_name;
        CodecP codec = ctx.codec(type_id, type_name);
        if (codec) {
            std::istringstream in(tmp);
            Var body;
            codec->decode(in, body, ctx);
            value = Record(type_name, body, type_id, codec);
        } else {
            value = Record("@", tmp, type_id);
        }
    }

    CodecP MessageCodec::Factory::decodeType(std::istream& in, Context& ctx) {
        return CodecP(new MessageCodec);
    }

    char MessageCodec::Factory::typeByte() const {
        return type_byte;
    }
}
