#ifndef STRUCT_CODEC_HGUARD_
#define STRUCT_CODEC_HGUARD_

#include <utility>
#include <codec.h>

class StructCodec : public Codec {
public:
    typedef std::pair<std::string,CodecP> Field;

    StructCodec(std::vector<Field> const& fields);

    static const char type_byte = 'S';

    virtual std::string typeName();
    virtual void encodeType(std::ostream& out);
    virtual void encode(std::ostream& out, Var const& value, Context& ctx);
    virtual void decode(std::istream& in, Var& value, Context& ctx);

private:
    std::vector<Field> fields_;

public:
    class Factory : public CodecFactory {
    public:
        virtual CodecP decodeType(std::istream& in, Context& ctx);
        virtual char typeByte() const;
    };
};

#endif // STRUCT_CODEC_HGUARD_
