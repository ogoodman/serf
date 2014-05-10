#ifndef VAR_CALLABLE_EXAMPLE_HGUARD_
#define VAR_CALLABLE_EXAMPLE_HGUARD_

#include <serf/rpc/var_callable.h>
#include <serf/rpc/var_proxy.h>

namespace serf {
    class VarCaller;

    // Base class generated from IDL file.
    class Example : public VarCallable
    {
    public:
        virtual void fun_a(double x) = 0;
        virtual int fun_b(int x) = 0;
        virtual int sum(std::vector<int> const& nums) = 0;
        virtual Future<Var>::Ptr getitem(std::string const& key) = 0;

        virtual FVarP varCall_a_(std::string const& method, std::vector<Var> const& args);
    };

    // Proxy class generated from IDL file.
    class ExamplePrx : public VarProxy
    {
    public:
        ExamplePrx(VarCaller* remote, std::string const& node, std::string const& addr);

        Future<void>::Ptr fun_a(double x);
        Future<int>::Ptr fun_b(int x);
        Future<Var>::Ptr getitem(std::string const& key);
        Future<int>::Ptr sum(std::vector<int> const& nums);
    };

    // Our implementation.
    class ExampleImpl : public Example
    {
    public:
        void fun_a(double x);
        int fun_b(int x);
        int sum(std::vector<int> const& nums);
        Future<Var>::Ptr getitem(std::string const& key);

    public:
        boost::shared_ptr<ExamplePrx> proxy;
    };
}

#endif // VAR_CALLABLE_EXAMPLE_HGUARD_
