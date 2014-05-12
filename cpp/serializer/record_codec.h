#ifndef RECORD_CODEC_HGUARD_
#define RECORD_CODEC_HGUARD_

#include <serf/serializer/codec.h>

namespace serf {

    /** \brief Decoder for Records with type-byte 'R'.
     */
    class RecordCodec : public Codec
    {
    public:
        static const char type_byte = 'R';

        virtual std::string typeName();
        virtual void encodeType(std::ostream& out);
        virtual void encode(std::ostream& out, Var const& value, Context& ctx);
        virtual void decode(std::istream& in, Var& value, Context& ctx);
    public:
        class Factory : public CodecFactory {
        public:
            virtual CodecP decodeType(std::istream& in, Context& ctx);
            virtual char typeByte() const;
        };
    };

    /** \brief Decoder for Records with type-byte '@' (messages).
     */
    class MessageCodec : public Codec
    {
    public:
        static const char type_byte = '@';

        virtual std::string typeName();
        virtual void encodeType(std::ostream& out);
        virtual void encode(std::ostream& out, Var const& value, Context& ctx);
        virtual void decode(std::istream& in, Var& value, Context& ctx);
    public:
        class Factory : public CodecFactory {
        public:
            virtual CodecP decodeType(std::istream& in, Context& ctx);
            virtual char typeByte() const;
        };
    };
}

#endif // RECORD_CODEC_HGUARD_
