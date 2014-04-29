#ifndef CODEC_HGUARD_
#define CODEC_HGUARD_

#include <iosfwd>
#include <boost/shared_ptr.hpp>
#include <var.h>

namespace serf {

    class Context {
    };
    
    class Codec {
    public:
        virtual ~Codec();
    
        virtual std::string typeName() = 0;
        virtual void encodeType(std::ostream& out) = 0;
        virtual void encode(std::ostream& out, Var const& value, Context& ctx) = 0;
        virtual void decode(std::istream& in, Var& value, Context& ctx) = 0;
    
        std::string encodes(Var const& v);
        Var decodes(std::string const& data);
    };
    
    typedef boost::shared_ptr<Codec> CodecP;
    
    class CodecFactory {
    public:
        virtual ~CodecFactory();
    
        virtual CodecP decodeType(std::istream& in, Context& ctx) = 0;
        virtual char typeByte() const = 0;
    };
    
    typedef boost::shared_ptr<CodecFactory> CodecFactoryP;
}

#endif // CODEC_HGUARD_
