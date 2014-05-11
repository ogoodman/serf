#ifndef EXAMPLE_HGUARD_
#define EXAMPLE_HGUARD_

#include <serf/rpc/example_gen.h>

class ExampleImpl : public Example
{
public:
    void fun_a(double x);
    int fun_b(int x);
    int sum(std::vector<int> const& nums);
    serf::Future<serf::Var>::Ptr getitem(std::string const& key);
    std::vector<int32_t> graph(boost::posix_time::ptime t);

public:
    boost::shared_ptr<ExamplePrx> proxy;
};

#endif // EXAMPLE_HGUARD_
