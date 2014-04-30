#ifndef TUPLE_CODEC_HGUARD_
#define TUPLE_CODEC_HGUARD_

#include <vector>
#include <serf/serializer/codec.h>

namespace serf {

    class TupleCodec : public Codec
    {
    public:
        TupleCodec(std::vector<CodecP> const& codecs);
    
        virtual std::string typeName();
        virtual void encodeType(std::ostream& out);
        virtual void encode(std::ostream& out, Var const& value, Context& ctx);
        virtual void decode(std::istream& in, Var& value, Context& ctx);
    
        void encode(std::ostream& out, std::vector<Var> const& value, Context& ctx);
    
        static const char type_byte = 'T';
    
    private:
        std::vector<CodecP> codecs_;
    
    public:
        class Factory : public CodecFactory {
        public:
            virtual CodecP decodeType(std::istream& in, Context& ctx);
            virtual char typeByte() const;
        };
    };
}

#endif // TUPLE_CODEC_HGUARD_
