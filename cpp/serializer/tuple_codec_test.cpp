#include <serf/serializer/tuple_codec.h>
#include <cxxtest/TestSuite.h>

#include <sstream>

using namespace serf;

class TupleCodecTest : public CxxTest::TestSuite
{
public:
    void testTupleCodec() {
        TupleCodec::Factory tcf;
        std::string tup_ia("\0\0\0\x02iA", 6); // tuple(int32,any)
        istringstream in(tup_ia);
        Context ctx;
        CodecP tc = tcf.decodeType(in, ctx);

        // Check in consumed exactly.
        char ch;
        TS_ASSERT(in);
        TS_ASSERT(!in.get(ch));

        ostringstream out;
        tc->encodeType(out);
        TS_ASSERT_EQUALS(out.str(), string("T") + tup_ia);

        std::vector<Var> vv(2);
        vv[0] = 42;
        // vv[1] is null.
        Var val(vv);
        std::string enc("\0\0\0*-", 5);
        TS_ASSERT_EQUALS(tc->encodes(val), enc);
        TS_ASSERT_EQUALS(tc->decodes(enc), val);
    }
};
