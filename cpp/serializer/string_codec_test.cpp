#include <serf/serializer/string_codec.h>
#include <cxxtest/TestSuite.h>

#include <sstream>
#include <stdexcept>

using namespace serf;

class StringCodecTest : public CxxTest::TestSuite
{
public:
    void testStringCodec() {
        std::string a("A nice friendly string\n");
        std::string r("\x00\x80""AllSortsOfRu\xBBish", 18);
        std::string long_s(40000, 'x');

        TS_ASSERT(isAscii(a));
        TS_ASSERT(!isAscii(r));

        // Default factory makes a raw data codec.
        StringCodec::Factory scf;
        TS_ASSERT_EQUALS(scf.typeByte(), 'r');
        Context ctx;
        istringstream in("");
        CodecP rc = scf.decodeType(in, ctx);

        ostringstream out;
        rc->encodeType(out);
        TS_ASSERT_EQUALS(out.str(), "r");
        std::string r_enc = std::string("\x00\x00\x00\x12", 4) + r;
        TS_ASSERT_EQUALS(rc->encodes(r), r_enc);
        Var rv(r);
        TS_ASSERT_EQUALS(rc->decodes(r_enc), rv);
        std::string l_len = std::string("\x00\x00\x9C\x40", 4);
        TS_ASSERT_EQUALS(rc->encodes(long_s), l_len + long_s);
        TS_ASSERT_EQUALS(boost::get<std::string>(rc->decodes(l_len + long_s)), long_s);

        // Make a token string (up to 32k bytes)
        StringCodec kc('k');
        out.str("");
        kc.encodeType(out);
        TS_ASSERT_EQUALS(out.str(), "k");

        std::string r_kenc = std::string("\x00\x12", 2) + r;
        TS_ASSERT_EQUALS(kc.encodes(r), r_kenc);
        TS_ASSERT_EQUALS(kc.decodes(r_kenc), rv);
        TS_ASSERT_THROWS(kc.encodes(long_s), std::runtime_error);

        // Make an ascii codec
        StringCodec ac('a');
        out.str("");
        ac.encodeType(out);
        TS_ASSERT_EQUALS(out.str(), "a");

        std::string a_enc = std::string("\x00\x00\x00\x17", 4) + a;
        TS_ASSERT_EQUALS(ac.encodes(a), a_enc);
        TS_ASSERT_EQUALS(boost::get<std::string>(ac.decodes(a_enc)), a);
        TS_ASSERT_THROWS(ac.encodes(r), std::runtime_error);
        TS_ASSERT_EQUALS(ac.encodes(long_s), l_len + long_s);
        TS_ASSERT_EQUALS(boost::get<std::string>(ac.decodes(l_len + long_s)), long_s);

        // Unicode is same as raw at this point (no checking done).
        StringCodec uc('u');
        out.str("");
        uc.encodeType(out);
        TS_ASSERT_EQUALS(out.str(), "u");
        TS_ASSERT_EQUALS(uc.encodes(r), r_enc); // If checked, would throw.
        TS_ASSERT_EQUALS(uc.decodes(r_enc), rv);
    }
};
