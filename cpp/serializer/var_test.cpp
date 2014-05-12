#include <serf/serializer/var.h>
#include <cxxtest/TestSuite.h>

#include <serf/serializer/null_codec.h>
#include <serf/util/debug.h>

using namespace boost;
using namespace std;
using namespace serf;

class VarTest : public CxxTest::TestSuite
{
public:
    void testVar() {
        Var v1(string("hi"));
        Var v2(3.5);

        TS_ASSERT_EQUALS(get<string>(v1), "hi");
        TS_ASSERT_EQUALS(get<double>(v2), 3.5);

        TS_ASSERT_EQUALS(toStr(v1), "\"hi\"");
        TS_ASSERT_EQUALS(toStr(v2), "3.5");

        Var n;
        TS_ASSERT_EQUALS(toStr(n), "null");

        Var ch(byte('\xA9'));
        TS_ASSERT_EQUALS(toStr(ch), "'\\xA9'");

        vector<Var> sub;
        sub.push_back(-1);
        sub.push_back(string("hi"));
        sub.push_back(false);
        vector<Var> v;
        v.push_back(1);
        v.push_back(4);
        v.push_back(sub);
        v.push_back(blank());
        v.push_back(byte('X'));
        Var vv(v);

        TS_ASSERT_EQUALS(toStr(vv), "[1, 4, [-1, \"hi\", false], null, 'X']");

        TS_ASSERT_EQUALS(get<int>(V(vv)[0]), 1);

        V(vv)[0] = 2;
        TS_ASSERT_EQUALS(get<int>(V(vv)[0]), 2);

        map<string,Var> mv;
        mv["num"] = 1;
        mv["name"] = string("Fred");
        mv["caveman"] = true;
        Var m(mv);
        TS_ASSERT_EQUALS(get<int>(M(m)["num"]), 1);
        TS_ASSERT(get<bool>(M(m)["caveman"]));
        M(m)["name"] = string("Barney");
        TS_ASSERT_EQUALS(get<string>(M(m)["name"]), "Barney");

        TS_ASSERT_EQUALS(
            toStr(m),
            "{\"caveman\": true, \"name\": \"Barney\", \"num\": 1}");

        Var t(CodecP(new NullCodec()));
        TS_ASSERT_EQUALS(toStr(t), "NULL");
    }
};
