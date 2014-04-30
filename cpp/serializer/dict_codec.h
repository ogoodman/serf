#ifndef DICT_CODEC_HGUARD_
#define DICT_CODEC_HGUARD_

#include <serf/serializer/codec.h>

namespace serf {

    class DictCodec : public Codec {
    public:
        DictCodec(CodecP key_codec, CodecP elem_codec);
    
        virtual std::string typeName();
        virtual void encodeType(std::ostream& out);
        virtual void encode(std::ostream& out, Var const& value, Context& ctx);
        virtual void decode(std::istream& in, Var& value, Context& ctx);
    
        void encode(std::ostream& out, std::map<std::string,Var> const& value, Context& ctx);
        void decode(std::istream& in, std::map<std::string,Var>& value, Context& ctx);
    
        class Factory : public CodecFactory {
        public:
            virtual CodecP decodeType(std::istream& in, Context& ctx);
            virtual char typeByte() const;
        };
    
    private:
        CodecP key_codec_;
        CodecP elem_codec_;
    };
}

#endif // DICT_CODEC_HGUARD_
