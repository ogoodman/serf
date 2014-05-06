#ifndef VAR_CALLABLE_EXAMPLE_HGUARD_
#define VAR_CALLABLE_EXAMPLE_HGUARD_

#include <serf/rpc/var_callable.h>

namespace serf {

    // Base class generated from IDL file.
    class Example : public VarCallable
    {
    public:
        virtual void fun_a(double x) = 0;
        virtual int fun_b(int x) = 0;

        virtual Var varCall_(std::string const& method, std::vector<Var> const& args);
        virtual FVarP varCall_a_(std::string const& method, std::vector<Var> const& args);
    };

    class ExamplePrx : public VarExceptionDecoder
    {
    public:
        ExamplePrx(VarCallable* remote);

        Future<void>::Ptr fun_a(double x);
        Future<int>::Ptr fun_b(int x);

        void varDecodeExc_(Var const& exc);
    private:
        VarCallable* remote_;
    };

    // Our implementation.
    class ExampleImpl : public Example
    {
    public:
        void fun_a(double x);
        int fun_b(int x);
    };
}

#endif // VAR_CALLABLE_EXAMPLE_HGUARD_
