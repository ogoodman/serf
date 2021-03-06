#include <serf/rpc/example.h>

#include <serf/util/debug.h>

void ExampleImpl::fun_a(double x) {
    if (x > 0) {
        SAY("fun_a(" << x << ")");
    }
}

int ExampleImpl::fun_b(int x) {
    if (x == 42) throw TooBig(42);
    return x + 5;
}

serf::Future<serf::Var>::Ptr ExampleImpl::getitem(std::string const& key) {
    return proxy.getitem(key);
}

int ExampleImpl::sum(std::vector<int> const& nums) {
    int total = 0;
    size_t i = 0, n = nums.size();
    for (i = 0; i < n; ++i) {
        total += nums[i];
    }
    return total;
}

std::vector<int32_t> ExampleImpl::graph(boost::posix_time::ptime t) {
	std::vector<int32_t> nums;
	nums.push_back(3);
	nums.push_back(6);
	nums.push_back(5);
	return nums;
}

void ExampleImpl::print(serf::Var const& value) {
    SAY(value);
}

void ExampleImpl::setProxy(ExamplePrx const& ep) {
    proxy = ep;
}

serf::Future<ExamplePrx>::Ptr ExampleImpl::getProxy() {
    serf::Future<ExamplePrx>::Ptr f(new serf::Future<ExamplePrx>);
    f->resolve(proxy);
    return f;
}
