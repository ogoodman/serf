#ifndef ARRAY_CODEC_HGUARD_
#define ARRAY_CODEC_HGUARD_

#include <codec.h>

namespace serf {

    class ArrayCodec : public Codec {
    public:
        ArrayCodec(CodecP elem_codec);
    
        virtual std::string typeName();
        virtual void encodeType(std::ostream& out);
        virtual void encode(std::ostream& out, Var const& value, Context& ctx);
        virtual void decode(std::istream& in, Var& value, Context& ctx);
    
        void encode(std::ostream& out, std::vector<Var> const& value, Context& ctx);
        void decode(std::istream& in, std::vector<Var>& value, Context& ctx);
    
        class Factory : public CodecFactory {
        public:
            virtual CodecP decodeType(std::istream& in, Context& ctx);
            virtual char typeByte() const;
        };
    
    private:
        CodecP elem_codec_;
    };
}

#endif // ARRAY_CODEC_HGUARD_
