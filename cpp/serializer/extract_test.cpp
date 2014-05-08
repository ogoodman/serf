#include <serf/serializer/extract.h>
#include <cxxtest/TestSuite.h>

#include <serf/debug.h>

using namespace serf;

class ExtractTest : public CxxTest::TestSuite
{
public:
    void testExtract() {
        std::vector<Var> vv;
        vv.push_back(1);
        vv.push_back(3);

        std::vector<int> iv;

        extract(iv, vv);

        TS_ASSERT_EQUALS(iv.size(), 2);
        TS_ASSERT_EQUALS(iv[1], 3);

        std::map<std::string, Var> mv;
        mv["builder"] = std::string("tom");
        mv["plumber"] = std::string("dick");

        std::map<std::string, std::string> ms;

        extract(ms, mv);

        TS_ASSERT_EQUALS(ms.size(), 2);
        TS_ASSERT_EQUALS(ms["builder"], std::string("tom"));

        // Try a nested homogeneous structure.
        mv.clear();
        mv["inner"] = vv;

        std::map<std::string, std::vector<int> > mvi;
        extract(mvi, Var(mv));

        TS_ASSERT_EQUALS(mvi.size(), 1);
        TS_ASSERT_EQUALS(mvi["inner"].size(), 2);
        TS_ASSERT_EQUALS(mvi["inner"][0], 1);

        std::vector<Var> vv1;
        extract(vv1, vv);

        TS_ASSERT_EQUALS(vv1.size(), 2);
        TS_ASSERT_EQUALS(boost::get<int>(vv1[0]), 1);
    }

    void testSetVar() {
        std::vector<int> iv;
        iv.push_back(1);
        iv.push_back(3);

        Var v;
        setVar(v, iv);

        TS_ASSERT_EQUALS(V(v).size(), 2);
        TS_ASSERT_EQUALS(boost::get<int>(V(v)[1]), 3);

        std::map<std::string, bool> msb;

        msb["home"] = true;
        msb["work"] = false;

        setVar(v, msb);

        TS_ASSERT_EQUALS(M(v).size(), 2);
        TS_ASSERT_EQUALS(boost::get<bool>(M(v)["work"]), false);
    }
};
