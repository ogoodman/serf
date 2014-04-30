#include <serf/serializer/struct_codec.h>
#include <cxxtest/TestSuite.h>

#include <serf/serializer/type_codec.h>
#include <sstream>

using namespace serf;

class StructCodecTest : public CxxTest::TestSuite
{
public:
    void testStructCodec() {
        std::string s_type("S\0\0\0\2\0\4nameu\0\3ageh", 18);
        CodecP sc = getCodec(s_type);
        TS_ASSERT_EQUALS(
            sc->typeName(), "STRUCT((\"name\", TEXT), (\"age\", INT16))");
        ostringstream out;
        sc->encodeType(out);
        TS_ASSERT_EQUALS(out.str(), s_type);

        // Make a value to encode.
        std::map<std::string, Var> vmap;
        vmap["name"] = string("Fred");
        vmap["age"] = 42;
        Var value(vmap);

        std::string enc("\0\0\0\4Fred\0*", 10);
        TS_ASSERT_EQUALS(sc->encodes(value), enc);
        TS_ASSERT_EQUALS(sc->decodes(enc), value);
    }
};
