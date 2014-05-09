#include <serf/rpc/var_callable_example.h>
#include <cxxtest/TestSuite.h>

#include <serf/rpc/var_caller.h>

namespace serf {
    /** \brief Implements VarCaller for the benefit of tests.
     *
     * Rather than implementing a realistic VarCaller from scratch
     * we take a (synchronously callable) VarCallable and wrap a bit
     * of extra code around it to implement the expected callRemote
     * protocol.
     */
    class MockVarCaller : public VarCaller
    {
    public:
        MockVarCaller(VarCallable* servant) : servant_(servant) {}
        
        // We get {"o":.., "m":.., "a":..}.
        Future<Var>::Ptr callRemote(std::string const& node, Var& call) {
            Future<Var>::Ptr reply(new Future<Var>);
            std::string method = boost::get<std::string>(M(call).at("m"));
        
            std::map<std::string, Var> reply_m;
            try {
                reply_m["r"] = servant_->varCall_(method, V(M(call).at("a")));
            } catch (std::exception& e) {
                std::vector<Var> e_info;
                e_info.push_back(std::string("Exception"));
                e_info.push_back(std::string(e.what()));
                reply_m["e"] = e_info;
            }
            reply->resolve(Var(reply_m));
            return reply;
        }
        
    private:
        VarCallable* servant_; // not owned.
    };
}

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

        std::vector<Var> nums;
        nums.push_back(1);
        nums.push_back(3);
        nums.push_back(5);
        args.push_back(nums);
        TS_ASSERT_EQUALS(boost::get<int>(inst.varCall_("sum", args)), 9);
    }

    void callbackv(Result<void>::Ptr r) {
        r->get();
        n = 1;
    }

    void callbacki(Result<int>::Ptr r) {
        try {
            n = r->get();
        } catch (std::exception& e) {
            e_what = e.what();
        }
    }

    void testVarCallableExamplePrx() {
        n = 0;
        e_what = "";

        ExampleImpl inst;
        MockVarCaller caller(&inst);
        ExamplePrx prx(&caller, "", "");

        prx.fun_a(-3.5)->then(this, &VarCallableExampleTest::callbackv);
        TS_ASSERT_EQUALS(n, 1);

        prx.fun_b(5)->then(this, &VarCallableExampleTest::callbacki);
        TS_ASSERT_EQUALS(n, 10);

        prx.fun_b(42)->then(this, &VarCallableExampleTest::callbacki);
        TS_ASSERT_EQUALS(e_what, "too big");

        std::vector<int> nums;
        nums.push_back(1);
        nums.push_back(4);
        nums.push_back(9);
        prx.sum(nums)->then(this, &VarCallableExampleTest::callbacki);
        TS_ASSERT_EQUALS(n, 14);
    }

private:
    int n;
    std::string e_what;
};
