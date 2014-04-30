#ifndef TYPE_CODEC_HGUARD_
#define TYPE_CODEC_HGUARD_

#include <serf/serializer/codec.h>

namespace serf {

    class TypeCodec : public Codec {
    public:
        virtual std::string typeName();
        virtual void encodeType(std::ostream& out);
        virtual void encode(std::ostream& out, Var const& value, Context& ctx);
        virtual void decode(std::istream& in, Var& value, Context& ctx);
    
        CodecP decode(std::istream& in, Context& ctx);
    
        class Factory : public CodecFactory {
        public:
            virtual CodecP decodeType(std::istream& in, Context& ctx);
            virtual char typeByte() const;
        };
    };
    
    CodecP getCodec(std::string s);
    
    class TypeRegistry {
    public:
        static TypeRegistry& inst();
    
        CodecFactoryP get(char type_char);
        void reg(CodecFactoryP cfac);
    
    private:
        TypeRegistry();
        ~TypeRegistry();
    
        std::map<char,CodecFactoryP> reg_;
    };
}

#endif // TYPE_CODEC_HGUARD_
