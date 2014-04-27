#ifndef STRING_CODEC_HGUARD_
#define STRING_CODEC_HGUARD_

#include <codec.h>

extern const char* STRING_TYPES;

class StringCodec : public Codec {
public:
    StringCodec(char type_byte='r');

    virtual std::string typeName();
    virtual void encodeType(std::ostream& out);
    virtual void encode(std::ostream& out, Var const& value, Context& ctx);
    virtual void decode(std::istream& in, Var& value, Context& ctx);

    void encode(std::ostream& out, std::string const& value);
    void decode(std::istream& in, std::string& value);
private:
    char type_byte_;

public:
    class Factory : public CodecFactory {
    public:
        Factory(char type_byte='r');

        virtual CodecP decodeType(std::istream& in, Context& ctx);
        virtual char typeByte() const;
    private:
        char type_byte_;
    };
};

bool isAscii(std::string const& s);

#endif // STRING_CODEC_HGUARD_
