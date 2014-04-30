#include <serf/serializer/null_codec.h>
#include <cxxtest/TestSuite.h>

#include <sstream>

using namespace std;
using namespace serf;

class NullCodecTest : public CxxTest::TestSuite
{
public:
    void testNullCodec() {
        Context ctx;
        NullCodec::Factory ncf;
        TS_ASSERT_EQUALS(ncf.typeByte(), '-');

        istringstream in("");
        CodecP nc = ncf.decodeType(in, ctx);
        TSM_ASSERT("Should not be at EOF", in); // Nothing read.

        TS_ASSERT_EQUALS(nc->typeName(), "NULL");

        // EncodeType should write the type byte '-'.
        ostringstream out;
        nc->encodeType(out);
        TS_ASSERT_EQUALS(out.str(), "-");

        Var n;
        out.str("");
        nc->encode(out, n, ctx);
        TS_ASSERT_EQUALS(out.str(), ""); // Nothing written.

        // Decoding should reset n to blank.
        n = 14;
        TS_ASSERT_THROWS(get<blank>(n), boost::bad_get);
        nc->decode(in, n, ctx);
        TS_ASSERT_THROWS_NOTHING(get<blank>(n));
        TSM_ASSERT("Should not be at EOF", in);
    }
};
