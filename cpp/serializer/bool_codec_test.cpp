#include <serf/serializer/bool_codec.h>
#include <cxxtest/TestSuite.h>

#include <sstream>

using namespace serf;

class BoolCodecTest : public CxxTest::TestSuite
{
public:
    void testBoolCodec() {
        BoolCodec bc;

        ostringstream tb;
        bc.encodeType(tb);
        TS_ASSERT_EQUALS(tb.str(), "b");

        TS_ASSERT_EQUALS(bc.encodes(true), "\x01");
        TS_ASSERT_EQUALS(bc.encodes(false), string("\x00", 1));

        TS_ASSERT_EQUALS(get<bool>(bc.decodes("\x01")), true);
        TS_ASSERT_EQUALS(get<bool>(bc.decodes(string("\x00", 1))), false);

        BoolCodec::Factory bf;
        TS_ASSERT_EQUALS(bf.typeByte(), 'b');

        istringstream in("");
        Context ctx;
        CodecP cp = bf.decodeType(in, ctx); // Nothing read.
        TSM_ASSERT("Should not be at EOF", in);
        Var bv = cp->decodes("\x01");
        TS_ASSERT_THROWS_NOTHING(get<bool>(bv)); // It is a bool.
    }
};
