#include <serf/rpc/var_callable_example.h>

#include <serf/serializer/extract.h>
#include <serf/rpc/var_caller.h>
#include <serf/rpc/var_proxy.h>
#include <serf/rpc/serf_exception.h>
#include <serf/debug.h>

namespace serf {

    // We make a protected call to varCall_a_ at the top level.
    FVarP Example::varCall_a_(std::string const& method, std::vector<Var> const& args) {
        Var result;

        if (method == "getitem") { // AMD example.
            if (args.size() < 1) throw NotEnoughArgs(method, args.size(), 1);
			std::string a0 = boost::get<std::string const&>(args.at(0));
            return toFuture<Var>(getitem(a0));
		} else if (method == "fun_a") {
            if (args.size() < 1) throw NotEnoughArgs(method, args.size(), 1);
            fun_a(boost::get<double>(args.at(0)));
        } else if (method == "fun_b") {
            if (args.size() < 1) throw NotEnoughArgs(method, args.size(), 1);
            result = fun_b(boost::get<int>(args.at(0)));
        } else if (method == "sum") {
            if (args.size() < 1) throw NotEnoughArgs(method, args.size(), 1);
            std::vector<int> nums;
            extract(nums, args.at(0));
            result = sum(nums);
        } else {
            throw NoSuchMethod(method);
        }

		std::map<std::string, Var> m_var;
		m_var["r"] = result;
		FVarP f_res(new Future<Var>());
		f_res->resolve(Var(m_var));
        return f_res;
    }

    ExamplePrx::ExamplePrx(VarCaller* remote, std::string const& node, std::string const& addr)
        : VarProxy(remote, node, addr) {}

    Future<void>::Ptr ExamplePrx::fun_a(double x) {
        std::vector<Var> args;
        args.push_back(x);
        return toFuture<void>(call_("fun_a", args));
    }

    Future<int>::Ptr ExamplePrx::fun_b(int n) {
        std::vector<Var> args;
        args.push_back(n);
        return toFuture<int>(call_("fun_b", args));
    }

    Future<Var>::Ptr ExamplePrx::getitem(std::string const& key) {
        std::vector<Var> args;
        args.push_back(key);
        return toFuture<Var>(call_("__getitem__", args));
    }

    Future<int>::Ptr ExamplePrx::sum(std::vector<int> const& nums) {
        std::vector<Var> args(1);
        setVar(args[0], nums);
        return toFuture<int>(call_("sum", args));
    }

    // Our implementation.

    void ExampleImpl::fun_a(double x) {
        if (x > 0) {
            SAY("fun_a(" << x << ")");
        }
    }

    int ExampleImpl::fun_b(int x) {
        if (x == 42) throw std::runtime_error("too big");
        return x + 5;
    }

    Future<Var>::Ptr ExampleImpl::getitem(std::string const& key) {
        return proxy->getitem(key);
    }

    int ExampleImpl::sum(std::vector<int> const& nums) {
        int total = 0;
        size_t i = 0, n = nums.size();
        for (i = 0; i < n; ++i) {
            total += nums[i];
        }
        return total;
    }

}
