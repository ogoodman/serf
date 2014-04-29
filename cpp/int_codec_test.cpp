#include <int_codec.h>
#include <cxxtest/TestSuite.h>

#include <sstream>
#include <stdexcept>

using namespace std;
using namespace boost;
using namespace serf;

class IntCodecTest : public CxxTest::TestSuite
{
public:
    void testIntCodec() {
        IntCodec ic; // Default width is 4.

        ostringstream tb;
        ic.encodeType(tb);
        TS_ASSERT_EQUALS(tb.str(), "i");

        TS_ASSERT_EQUALS(ic.typeName(), "INT32");

        Var value;
        string s42("\x00\x00\x00*", 4);
        string sm256("\xFF\xFF\xFF\x00", 4);
        value = ic.decodes(s42);
        TS_ASSERT_EQUALS(get<int>(value), 42);
        value = ic.decodes(sm256);
        TS_ASSERT_EQUALS(get<int>(value), -256);

        TS_ASSERT_EQUALS(ic.encodes(42), s42);
        TS_ASSERT_EQUALS(ic.encodes(-256), sm256);
    }

    void testWidth8() {
        IntCodec ic(8);

        ostringstream tb;
        ic.encodeType(tb);
        TS_ASSERT_EQUALS(tb.str(), "q");

        TS_ASSERT_EQUALS(ic.typeName(), "INT64");

        Var value;
        string s42("\x00\x00\x00\x00\x00\x00\x00*", 8);
        string sm256("\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x00", 8);
        value = ic.decodes(s42);
        TS_ASSERT_EQUALS(get<int64_t>(value), 42);
        value = ic.decodes(sm256);
        TS_ASSERT_EQUALS(get<int64_t>(value), -256);

        TS_ASSERT_EQUALS(ic.encodes(int64_t(42)), s42);
        TS_ASSERT_EQUALS(ic.encodes(int64_t(-256)), sm256);
    }

    void testWidth2() {
        IntCodec ic(2);

        ostringstream tb;
        ic.encodeType(tb);
        TS_ASSERT_EQUALS(tb.str(), "h");

        TS_ASSERT_EQUALS(ic.typeName(), "INT16");

        Var value;
        string s42("\x00*", 2);
        string sm256("\xFF\x00", 2);
        value = ic.decodes(s42);
        TS_ASSERT_EQUALS(get<int>(value), 42);
        value = ic.decodes(sm256);
        TS_ASSERT_EQUALS(get<int>(value), -256);

        TS_ASSERT_EQUALS(ic.encodes(42), s42);
        TS_ASSERT_EQUALS(ic.encodes(-256), sm256);
    }

    void testBadWidth() {
        TS_ASSERT_THROWS(IntCodec(5), std::domain_error);
        TS_ASSERT_THROWS(IntCodec(12), std::domain_error);
    }

    void testUnsignedByte() {
        IntCodec ic(1, false);

        ostringstream tb;
        ic.encodeType(tb);
        TS_ASSERT_EQUALS(tb.str(), "B");

        TS_ASSERT_EQUALS(ic.typeName(), "UBYTE");

        Var value;
        string s42("*", 1);
        string s254("\xFE", 1);
        value = ic.decodes(s42);
        TS_ASSERT_EQUALS(get<byte>(value), 42);
        value = ic.decodes(s254);
        TS_ASSERT_EQUALS(get<byte>(value), 254);

        TS_ASSERT_EQUALS(ic.encodes(byte(42)), s42);
        TS_ASSERT_EQUALS(ic.encodes(byte(254)), s254);
    }

    void testFactory() {
        IntCodec::Factory f1(1);
        IntCodec::Factory f2(2);
        IntCodec::Factory f4(4);
        IntCodec::Factory f8(8);

        TS_ASSERT_EQUALS(f1.typeByte(), 'b');
        TS_ASSERT_EQUALS(f2.typeByte(), 'h');
        TS_ASSERT_EQUALS(f4.typeByte(), 'i');
        TS_ASSERT_EQUALS(f8.typeByte(), 'q');

        Context ctx;
        istringstream in("");
        CodecP c = f2.decodeType(in, ctx); // Does not read anything.
        TS_ASSERT_EQUALS(c->encodes(14023).size(), 2); // Width 2 codec.

        c = f8.decodeType(in, ctx);
        int64_t big = 123456789123456789LL;
        string big_e = c->encodes(big);
        TS_ASSERT_EQUALS(big_e.size(), 8);
        Var big_v = c->decodes(big_e);
        TS_ASSERT_EQUALS(get<int64_t>(big_v), big);
    }
};
