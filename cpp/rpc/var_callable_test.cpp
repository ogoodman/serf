#include <serf/rpc/example.h>
#include <cxxtest/TestSuite.h>

#include <serf/rpc/var_caller.h>
#include <serf/debug.h>

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
            std::string method = boost::get<std::string>(M(call).at("m"));
			return servant_->call_(method, V(M(call).at("a")));
        }
        
    private:
        VarCallable* servant_; // not owned.
    };
}

using namespace serf;

class VarCallableExampleTest : public CxxTest::TestSuite
{
public:
	Var getResult(FVarP enc) {
		return M(enc->get()).at("r");
	}

	std::string getExcType(FVarP enc) {
		Var exc = M(enc->get()).at("e");
		return boost::get<std::string>(V(exc)[0]);
	}

    void testVarCallableExample() {
        ExampleImpl inst;

        std::vector<Var> args;
        args.push_back(-3.14);

        Var result = getResult(inst.call_("fun_a", args));
        TS_ASSERT_THROWS_NOTHING(boost::get<boost::blank>(result));

		std::string exc_type = getExcType(inst.call_("fun_b", args));
        TS_ASSERT_EQUALS(exc_type, "TypeError");

        args[0] = 3;

		result = getResult(inst.call_("fun_b", args));
        TS_ASSERT_EQUALS(boost::get<int>(result), 8);

        TS_ASSERT_EQUALS(getExcType(inst.call_("nosuch", args)), "NoSuchMethod");

        args.resize(0);
        TS_ASSERT_EQUALS(getExcType(inst.call_("fun_a", args)), "NotEnoughArgs");
        std::vector<Var> nums;
        nums.push_back(1);
        nums.push_back(3);
        nums.push_back(5);
        args.push_back(nums);
		
		result = getResult(inst.call_("sum", args));
        TS_ASSERT_EQUALS(boost::get<int>(result), 9);
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
