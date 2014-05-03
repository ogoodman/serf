#include <serf/rpc/var_callable_example.h>

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
