#include <any_codec.h>
#include <cxxtest/TestSuite.h>

using namespace boost::posix_time;
using namespace boost::gregorian;

class AnyCodecTest : public CxxTest::TestSuite
{
public:
    void testAnyCodec() {
        Var n;
        AnyCodec ac;

        n = blank();
        TS_ASSERT_EQUALS(ac.encodes(n), "-");

        n = false;
        TS_ASSERT_EQUALS(ac.encodes(n), string("b\x00", 2));
        n = byte('e');
        TS_ASSERT_EQUALS(ac.encodes(n), "Be");
        n = 42;
        TS_ASSERT_EQUALS(ac.encodes(n), string("i\x00\x00\x00*", 5));
        n = int64_t(42);
        TS_ASSERT_EQUALS(ac.encodes(n), string("q\x00\x00\x00\x00\x00\x00\x00*", 9));
        n = 3.5;
        TS_ASSERT_EQUALS(ac.encodes(n), string("d\x00\x00\x00\x00\x00\x00\x0c@", 9));
        n = ptime(date(2000,1,1), time_duration(0,0,1));
        TS_ASSERT_EQUALS(ac.encodes(n), string("t\x00\x03]\x01;G\"@", 9));

        map<string, Var> mv;
        mv["fred"] = byte('M');
        n = mv;
        TS_ASSERT_EQUALS(ac.encodes(n), string("MkA\x00\x00\x00\x01\x00\x04""fredBM", 15));

        string a("A nice friendly string\n");
        string r("\x00\x80""AllSortsOfRu\xBBish", 18);
        TS_ASSERT_EQUALS(ac.encodes(a), string("a\x00\x00\x00\x17", 5) + a);
        TS_ASSERT_EQUALS(ac.encodes(r), string("r\x00\x00\x00\x12", 5) + r);
    }
};
