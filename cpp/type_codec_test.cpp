#include <type_codec.h>
#include <cxxtest/TestSuite.h>

#include <sstream>

using namespace std;
using namespace boost::posix_time;
using namespace boost::gregorian;
using namespace serf;

class TypeCodecTest : public CxxTest::TestSuite
{
public:
    void testTypeCodec() {
        Var val;
        CodecP c;

        c = getCodec("-"); // null codec.
        TS_ASSERT_EQUALS(c->encodes(val), "");
        val = true;
        c = getCodec("b"); // bool codec.
        TS_ASSERT_EQUALS(c->encodes(val), "\x01");
        val = byte(42);
        c = getCodec("B"); // unsigned byte codec.
        TS_ASSERT_EQUALS(c->encodes(val), "*");
        val = 42;
        c = getCodec("i"); // int32 codec.
        TS_ASSERT_EQUALS(c->encodes(val), string("\x00\x00\x00*", 4));
        c = getCodec("A"); // any codec (prefixes encoding with type)
        TS_ASSERT_EQUALS(c->encodes(val), string("i\x00\x00\x00*", 5));
        val = int64_t(123456789012345678);
        c = getCodec("q"); // int64 codec.
        TS_ASSERT_EQUALS(c->encodes(val), "\x01\xb6\x9bK\xa6""0\xf3N");
        val = -16;
        c = getCodec("h"); // int16 codec.
        TS_ASSERT_EQUALS(c->encodes(val), string("\xFF\xF0", 2));
        val = 6.02e23;
        c = getCodec("d"); // float (double) codec
        TS_ASSERT_EQUALS(c->encodes(val), "a\xd3\xa8\x10\x9f\xde\xdf""D");
        val = string("data");
        c = getCodec("r"); // raw data codec.
        TS_ASSERT_EQUALS(c->encodes(val), string("\x00\x00\x00\x04""data", 8));
        c = getCodec("a"); // ascii codec.
        TS_ASSERT_EQUALS(c->encodes(val), string("\x00\x00\x00\x04""data", 8));
        c = getCodec("u"); // unicode (utf-8) codec.
        TS_ASSERT_EQUALS(c->encodes(val), string("\x00\x00\x00\x04""data", 8));
        c = getCodec("k"); // token codec
        TS_ASSERT_EQUALS(c->encodes(val), string("\x00\x04""data", 6));
        val = vector<Var>(3);
        c = getCodec("L-"); // array (list) of null.
        TS_ASSERT_EQUALS(c->encodes(val), string("\x00\x00\x00\x03", 4));
        TS_ASSERT_EQUALS(c->typeName(), "ARRAY(NULL)");
        c = getCodec("t"); // time
        val = ptime(date(1970, Jan, 1));
        TS_ASSERT_EQUALS(c->encodes(val), string(8, '\x00'));
        c = getCodec("MrB"); // map string -> byte.
        map<string, Var> mv;
        mv["fred"] = byte('M');
        val = mv;
        TS_ASSERT_EQUALS(c->encodes(val), string("\x00\x00\x00\x01\x00\x00\x00\x04""fredM", 13));
        TS_ASSERT_EQUALS(c->typeName(), "DICT(DATA, UBYTE)");
        val = vector<Var>(1); // [null]
        c = getCodec(string("T\0\0\0\x01""A", 6)); // tuple of one any
        TS_ASSERT_EQUALS(c->encodes(val), "-");
    }

    void testTypeAsVar() {
        TypeCodec tc;
        Var tv(tc.decodes("MkY"));
        CodecP t(boost::get<CodecP>(tv));
        TS_ASSERT_EQUALS(t->typeName(), "DICT(TOKEN, TYPE)");
        TS_ASSERT_EQUALS(tc.encodes(tv), "MkY");
    }
};
