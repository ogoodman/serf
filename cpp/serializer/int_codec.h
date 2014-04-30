#ifndef INT_CODEC_HGUARD_
#define INT_CODEC_HGUARD_

#include <serf/serializer/codec.h>

namespace serf {

    class IntCodec : public Codec {
    public:
        IntCodec(size_t width=4, bool signd=true);
    
        virtual std::string typeName();
        virtual void encodeType(std::ostream& out);
        virtual void encode(std::ostream& out, Var const& value, Context& ctx);
        virtual void decode(std::istream& in, Var& value, Context& ctx);
    
        void encode(std::ostream& out, int64_t value);
        int64_t decode(std::istream& in);
        size_t decodeSize(std::istream& in); // Checks >= 0.
    
    private:
        size_t width_;
        bool signed_;
    
    public:
        class Factory : public CodecFactory {
        public:
            Factory(size_t width=4, bool signd=true);
    
            virtual CodecP decodeType(std::istream& in, Context& ctx);
            virtual char typeByte() const;
        private:
            size_t width_;
            bool signed_;
        };
    };
}

#endif // INT_CODEC_HGUARD_
