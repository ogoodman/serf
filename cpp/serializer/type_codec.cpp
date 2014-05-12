#include <serf/serializer/type_codec.h>

#include <serf/serializer/null_codec.h>
#include <serf/serializer/bool_codec.h>
#include <serf/serializer/int_codec.h>
#include <serf/serializer/float_codec.h>
#include <serf/serializer/time_codec.h>
#include <serf/serializer/string_codec.h>
#include <serf/serializer/array_codec.h>
#include <serf/serializer/dict_codec.h>
#include <serf/serializer/tuple_codec.h>
#include <serf/serializer/type_codec.h>
#include <serf/serializer/any_codec.h>
#include <serf/serializer/struct_codec.h>
#include <serf/serializer/record_codec.h>

#include <serf/debug.h>

using namespace std;

namespace serf {

    std::string TypeCodec::typeName() {
        return "TYPE";
    }
    
    void TypeCodec::encodeType(std::ostream& out) {
        out << 'Y';
    }
    void TypeCodec::encode(std::ostream& out, Var const& value, Context& ctx) {
        boost::get<CodecP>(value)->encodeType(out);
    }
    void TypeCodec::decode(std::istream& in, Var& value, Context& ctx) {
        value = decode(in, ctx);
    }
    
    CodecP TypeCodec::decode(std::istream& in, Context& ctx) {
        char type_byte;
        if (!in.get(type_byte)) throw runtime_error("premature EOF");
        return TypeRegistry::inst().get(type_byte)->decodeType(in, ctx);
    }
    
    CodecP TypeCodec::Factory::decodeType(std::istream& in, Context& ctx) {
        return CodecP(new TypeCodec());
    }
    
    char TypeCodec::Factory::typeByte() const {
        return 'Y';
    }
    
    CodecP getCodec(string s) {
        TypeCodec tc;
        Context ctx;
        istringstream in(s);
        return tc.decode(in, ctx);
    }
    
    TypeRegistry& TypeRegistry::inst() {
        static TypeRegistry r;
        return r;
    }
    CodecFactoryP TypeRegistry::get(char type_byte) {
        return reg_.at(type_byte);
    }
    void TypeRegistry::reg(CodecFactoryP cfac) {
        reg_[cfac->typeByte()] = cfac;
    }
    TypeRegistry::TypeRegistry() {
        reg(CodecFactoryP(new NullCodec::Factory()));
        reg(CodecFactoryP(new BoolCodec::Factory()));
        reg(CodecFactoryP(new IntCodec::Factory(1, false))); // Unsigned Byte.
        reg(CodecFactoryP(new IntCodec::Factory(2)));
        reg(CodecFactoryP(new IntCodec::Factory(4)));
        reg(CodecFactoryP(new IntCodec::Factory(8)));
        reg(CodecFactoryP(new TimeCodec::Factory()));
        reg(CodecFactoryP(new FloatCodec::Factory()));
        reg(CodecFactoryP(new StringCodec::Factory('r')));
        reg(CodecFactoryP(new StringCodec::Factory('a')));
        reg(CodecFactoryP(new StringCodec::Factory('u')));
        reg(CodecFactoryP(new StringCodec::Factory('k')));
        reg(CodecFactoryP(new AnyCodec::Factory()));
        reg(CodecFactoryP(new ArrayCodec::Factory()));
        reg(CodecFactoryP(new DictCodec::Factory()));
        reg(CodecFactoryP(new TupleCodec::Factory()));
        reg(CodecFactoryP(new TypeCodec::Factory()));
        reg(CodecFactoryP(new StructCodec::Factory()));
        reg(CodecFactoryP(new RecordCodec::Factory()));
        reg(CodecFactoryP(new MessageCodec::Factory()));
    }
    TypeRegistry::~TypeRegistry() {
    }
}
