#ifndef ANY_CODEC_HGUARD_
#define ANY_CODEC_HGUARD_

#include <codec.h>

namespace serf {

    class AnyCodec;
    
    class AnyCodec : public Codec {
    public:
        virtual std::string typeName();
        virtual void encodeType(std::ostream& out);
        virtual void encode(std::ostream& out, Var const& value, Context& ctx);
        virtual void decode(std::istream& in, Var& value, Context& ctx);
    
        class Factory : public CodecFactory {
        public:
            virtual CodecP decodeType(std::istream& in, Context& ctx);
            virtual char typeByte() const;
        };
    };
}

#endif // ANY_CODEC_HGUARD_
