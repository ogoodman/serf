#include <serf/rpc/var_callable_example.h>

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
        } else {
            throw NoSuchMethod(method);
        }
        return result;
    }

    FVarP Example::varCall_a_(std::string const& method, std::vector<Var> const& args) {
        FVarP result(new Future<Var>());
        try {
            result->resolve(varCall_(method, args));
        } catch (std::exception& e) {
            result->resolve(new ErrorResult<Var>(e.what()));
        }
        return result;
    }

    ExamplePrx::ExamplePrx(VarCaller* remote)
        : VarProxy(remote, "OBJ", "node") {}

    Future<void>::Ptr ExamplePrx::fun_a(double x) {
        std::vector<Var> args;
        args.push_back(x);
        return toFuture<void>(varCall_a_("fun_a", args));
    }

    Future<int>::Ptr ExamplePrx::fun_b(int n) {
        std::vector<Var> args;
        args.push_back(n);
        return toFuture<int>(varCall_a_("fun_b", args));
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
}
