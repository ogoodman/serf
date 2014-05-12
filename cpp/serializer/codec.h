#ifndef CODEC_HGUARD_
#define CODEC_HGUARD_

#include <iosfwd>
#include <boost/shared_ptr.hpp>
#include <serf/serializer/var.h>

namespace serf {

    class Codec;
    typedef boost::shared_ptr<Codec> CodecP;

    /** \brief Interface for a registry of named and numbered types (Codecs).
     *
     * This base class is a trivial implementation which will never
     * return a Codec.
     *
     * A non-trivial implementation, supplied as the Context argument of
     * an encode or decode operation, enables us to encode and decode
     * records of Message type.
     */
    class Context {
    public:
        virtual ~Context();

        /** \brief Find a Codec by its type_id.
         */
        virtual CodecP codec(int type_id, std::string& type_name);
        /** \brief Find a Codec by its type_name.
         */
        virtual CodecP namedCodec(std::string const& type_name, int& type_id);
    };
    
    /** \brief Interface for codecs which encode and decode the various
     *  Var types.
     */
    class Codec {
    public:
        virtual ~Codec();
    
        /** \brief Readable representation of the type.
         */
        virtual std::string typeName() = 0;

        /** \brief Encodes the type.
         *
         * For primitive types this writes a single byte on the stream,
         * the type_byte of the Codec.
         *
         * For compound types this writes the type_byte followed by
         * any type parameters.
         */
        virtual void encodeType(std::ostream& out) = 0;

        /** \brief Encodes a value of this Codec's type.
         */
        virtual void encode(std::ostream& out, Var const& value, Context& ctx) = 0;

        /** \brief Decodes a value of this Codec's type.
         */
        virtual void decode(std::istream& in, Var& value, Context& ctx) = 0;
    
        /** \brief Encodes a value of this Codec's type into a string.
         */
        std::string encodes(Var const& v);

        /** \brief Decodes a value of this Codec's type from a string.
         */
        Var decodes(std::string const& data);
    };

    /** \brief Interface for codec factories.
     *
     * Associated with each Codec is a CodecFactory for making Codecs
     * of that type. For primitive types such as bools numbers, the
     * factory can always return the same instance. 
     *
     * For compound types the factory is needed to decode the type 
     * paramaters and return a codec of the required type.
     */
    class CodecFactory {
    public:
        virtual ~CodecFactory();
    
        /** \brief Reads the type parameters and returns the appropriate Codec.
         *
         * For primitive types this does not read anything. The type byte
         * has presumably already been read in order to choose this
         * CodecFactory.
         */
        virtual CodecP decodeType(std::istream& in, Context& ctx) = 0;

        /** \brief The type byte of this factory and any Codecs returned by it.
         */
        virtual char typeByte() const = 0;
    };
    
    typedef boost::shared_ptr<CodecFactory> CodecFactoryP;
}

#endif // CODEC_HGUARD_
