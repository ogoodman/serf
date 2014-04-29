#ifndef BOOL_CODEC_HGUARD_
#define BOOL_CODEC_HGUARD_

#include <codec.h>

namespace serf {

    class BoolCodec : public Codec {
    public:
        static const char type_byte = 'b';
    
        virtual std::string typeName();
        virtual void encodeType(std::ostream& out);
        virtual void encode(std::ostream& out, Var const& value, Context& ctx);
        virtual void decode(std::istream& in, Var& value, Context& ctx);
    
        void encode(std::ostream& out, bool value);
    
        class Factory : public CodecFactory {
        public:
            virtual CodecP decodeType(std::istream& in, Context& ctx);
            virtual char typeByte() const;
        };
    };
}

#endif // BOOL_CODEC_HGUARD_
