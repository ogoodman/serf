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

    FVarP Example::varCall_a_(std::string const& method, std::vector<Var> const& args) {
        FVarP result(new Future<Var>());
        try {
            result->resolve(varCall_(method, args));
        } catch (std::exception& e) {
            result->resolve(new ErrorResult<Var>(e.what()));
        }
        return result;
    }

    // The Proxy needs an object which takes an RMI call {"o":...} as
    // a Var and returns a Future<Var> containing {"r":...} or {"e":...}
    // or throwing due to some local error.


    template <typename R>
    class ProxyCallResult : public Result<R>
    {
    public:
        typedef typename add_constref<R>::type ref_type;

        ProxyCallResult(VarExceptionDecoder* prx, Result<Var>::Ptr result)
            : prx_(prx), result_(result) {}

        virtual ref_type get() const {
            return boost::get<R>(result_->get());
        }
    private:
        VarExceptionDecoder* prx_; // not owned
        Result<Var>::Ptr result_;
    };

    template <>
    class ProxyCallResult<void> : public Result<void>
    {
    public:
        ProxyCallResult(VarExceptionDecoder* prx, Result<Var>::Ptr result)
            : prx_(prx), result_(result) {}

        virtual void get() const {
            boost::get<boost::blank>(result_->get());
        }
    private:
        VarExceptionDecoder* prx_; // not owned
        Result<Var>::Ptr result_;
    };

    template <typename T>
    class Resolver : public Callback<Var>
    {
    public:
        Resolver(VarExceptionDecoder* prx, typename Future<T>::Ptr fp)
            : prx_(prx), fp_(fp) {}

        void call(Result<Var>::Ptr rv) {
            fp_->resolve(new ProxyCallResult<T>(NULL, rv));
        }
    private:
        VarExceptionDecoder* prx_; // not owned.
        typename Future<T>::Ptr fp_;
    };

    ExamplePrx::ExamplePrx(VarCallable* remote) : remote_(remote) {}

    Future<void>::Ptr ExamplePrx::fun_a(double x) {
        Future<void>::Ptr fv(new Future<void>());
        std::vector<Var> args;
        args.push_back(x);
        remote_->varCall_a_("fun_a", args)->then(new Resolver<void>(this, fv));
        return fv;
    }

    void ExamplePrx::varDecodeExc_(Var const& exc) {
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
