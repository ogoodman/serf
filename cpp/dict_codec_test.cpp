#include <dict_codec.h>
#include <cxxtest/TestSuite.h>

#include <sstream>
#include <type_codec.h>

using namespace std;

class DictCodecTest : public CxxTest::TestSuite
{
public:
    void testDictCodec() {
        DictCodec dc(getCodec("r"), getCodec("h"));
        map<string,Var> msv;
        msv["x"] = 0x3A61;
        msv["y"] = 0x3A62;
        msv["z"] = 0x3A63;
        Var dv(msv);
        string enc("\x00\x00\x00\x03\x00\x00\x00\x01x:a\x00\x00\x00\x01y:b\x00\x00\x00\x01z:c", 25);
        TS_ASSERT_EQUALS(dc.encodes(dv), enc);
        TS_ASSERT_EQUALS(dc.decodes(enc), dv);

        DictCodec::Factory dcf;
        TS_ASSERT_EQUALS(dcf.typeByte(), 'M');
        
        Context ctx;
        istringstream in("rh");
        CodecP cp = dcf.decodeType(in, ctx);
        ostringstream out;
        cp->encodeType(out);
        TS_ASSERT_EQUALS(out.str(), "Mrh");

        TS_ASSERT_EQUALS(cp->typeName(), "DICT(DATA, INT16)");
    }
};
