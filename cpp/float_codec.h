#ifndef FLOAT_CODEC_HGUARD_
#define FLOAT_CODEC_HGUARD_

#include <codec.h>

class FloatCodec : public Codec {
public:
    virtual std::string typeName();
    virtual void encodeType(std::ostream& out);
    virtual void encode(std::ostream& out, Var const& value, Context& ctx);
    virtual void decode(std::istream& in, Var& value, Context& ctx);

    void encode(std::ostream& out, double value);

    class Factory : public CodecFactory {
    public:
        virtual CodecP decodeType(std::istream& in, Context& ctx);
        virtual char typeByte() const;
    };
};

#endif // FLOAT_CODEC_HGUARD_
