#include <serf/rpc/var_callable_example.h>

#include <serf/serializer/extract.h>
#include <serf/rpc/var_caller.h>
#include <serf/rpc/var_proxy.h>
#include <serf/debug.h>

namespace serf {

    // Generated code.
    Var Example::varCall_(std::string const& method, std::vector<Var> const& args) {
        Var result;
        if (method == "fun_a") {
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
        return result;
    }

    FVarP Example::varCall_a_(std::string const& method, std::vector<Var> const& args) {
        FVarP result(new Future<Var>());
        try {
            // AMD example.
            if (method == "getitem") {
                if (args.size() < 1) throw NotEnoughArgs(method, args.size(), 1);
                result = getitem(boost::get<std::string const&>(args.at(0)));
            } else {
                result->resolve(varCall_(method, args));
            }
        } catch (std::exception& e) {
            result->resolve(new ErrorResult<Var>(e.what()));
        }
        return result;
    }

    ExamplePrx::ExamplePrx(VarCaller* remote, std::string const& node, std::string const& addr)
        : VarProxy(remote, node, addr) {}

    Future<void>::Ptr ExamplePrx::fun_a(double x) {
        std::vector<Var> args;
        args.push_back(x);
        return toFuture<void>(remoteCall_a_("fun_a", args));
    }

    Future<int>::Ptr ExamplePrx::fun_b(int n) {
        std::vector<Var> args;
        args.push_back(n);
        return toFuture<int>(remoteCall_a_("fun_b", args));
    }

    Future<Var>::Ptr ExamplePrx::getitem(std::string const& key) {
        std::vector<Var> args;
        args.push_back(key);
        return toFuture<Var>(remoteCall_a_("__getitem__", args));
    }

    Future<int>::Ptr ExamplePrx::sum(std::vector<int> const& nums) {
        std::vector<Var> args(1);
        setVar(args[0], nums);
        return toFuture<int>(remoteCall_a_("sum", args));
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
