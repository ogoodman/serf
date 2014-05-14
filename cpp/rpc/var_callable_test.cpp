#include <serf/rpc/example.h>
#include <cxxtest/TestSuite.h>

#include <serf/rpc/var_caller.h>
#include <serf/util/debug.h>

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
			return servant_->call_(method, V(M(call).at("a")), this);
        }
        
    private:
        VarCallable* servant_; // not owned.
    };
}

using namespace serf;

class VarCallableTest : public CxxTest::TestSuite
{
public:
	Var getResult(FVarP enc) {
		return M(enc->get()).at("r");
	}

	std::string getExcType(FVarP enc) {
		Var exc = M(enc->get()).at("e");
		return boost::get<std::string>(V(exc)[0]);
	}

    void testExampleImpl() {
        ExampleImpl inst;

        std::vector<Var> args;
        args.push_back(-3.14);

        Var result = getResult(inst.call_("fun_a", args, NULL));
        TS_ASSERT_THROWS_NOTHING(boost::get<boost::blank>(result));

		std::string exc_type = getExcType(inst.call_("fun_b", args, NULL));
        TS_ASSERT_EQUALS(exc_type, "TypeError");

        args[0] = 3;

		result = getResult(inst.call_("fun_b", args, NULL));
        TS_ASSERT_EQUALS(boost::get<int>(result), 8);

        TS_ASSERT_EQUALS(getExcType(inst.call_("nosuch", args, NULL)), "NoSuchMethod");

        args.resize(0);
        TS_ASSERT_EQUALS(getExcType(inst.call_("fun_a", args, NULL)), "NotEnoughArgs");
        std::vector<Var> nums;
        nums.push_back(1);
        nums.push_back(3);
        nums.push_back(5);
        args.push_back(nums);
		
		result = getResult(inst.call_("sum", args, NULL));
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

    void callbackvi(Result<std::vector<int> >::Ptr r) {
        std::vector<int> nums(r->get());
        n = nums[0];
    }

    void testExamplePrx() {
        n = 0;
        e_what = "";

        ExampleImpl inst;
        MockVarCaller caller(&inst);
        ExamplePrx prx(&caller, "node", "path");

        prx.fun_a(-3.5)->then(this, &VarCallableTest::callbackv);
        TS_ASSERT_EQUALS(n, 1);

        prx.fun_b(5)->then(this, &VarCallableTest::callbacki);
        TS_ASSERT_EQUALS(n, 10);

        prx.fun_b(42)->then(this, &VarCallableTest::callbacki);
        TS_ASSERT_EQUALS(e_what, "too big");

        std::vector<int> nums;
        nums.push_back(1);
        nums.push_back(4);
        nums.push_back(9);
        prx.sum(nums)->then(this, &VarCallableTest::callbacki);
        TS_ASSERT_EQUALS(n, 14);

        boost::posix_time::ptime now(second_clock::universal_time());
        prx.graph(now)->then(this, &VarCallableTest::callbackvi);
        TS_ASSERT_EQUALS(n, 3);

        ExamplePrx prx2(&caller, "node", "path2");
        prx.setProxy(prx2);
    }

private:
    int n;
    std::string e_what;
};
