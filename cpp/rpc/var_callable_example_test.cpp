#include <serf/rpc/var_callable_example.h>
#include <cxxtest/TestSuite.h>

using namespace serf;

class VarCallableExampleTest : public CxxTest::TestSuite
{
public:
    void testVarCallableExample() {
        ExampleImpl inst;

        std::vector<Var> args;
        args.push_back(-3.14);
        Var result = inst.varCall_("fun_a", args);
 
        TS_ASSERT_THROWS_NOTHING(boost::get<boost::blank>(result));
 
        TS_ASSERT_THROWS(inst.varCall_("fun_b", args), boost::bad_get);

        args[0] = 3;

        TS_ASSERT_EQUALS(boost::get<int>(inst.varCall_("fun_b", args)), 8);

        TS_ASSERT_THROWS(inst.varCall_("nosuch", args), NoSuchMethod);

        args.resize(0);
        TS_ASSERT_THROWS(inst.varCall_("fun_a", args), NotEnoughArgs);
    }

    void callback(Result<void>::Ptr r) {
        r->get();
        n = 1;
    }

    void testVarCallableExamplePrx() {
        n = 0;
        ExampleImpl inst;
        ExamplePrx prx(&inst);

        prx.fun_a(-3.5)->then(this, &VarCallableExampleTest::callback);
        TS_ASSERT_EQUALS(n, 1);
    }

private:
    int n;
};
