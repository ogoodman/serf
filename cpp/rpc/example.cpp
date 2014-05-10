#include <serf/rpc/example.h>

#include <serf/debug.h>

void ExampleImpl::fun_a(double x) {
    if (x > 0) {
        SAY("fun_a(" << x << ")");
    }
}

int ExampleImpl::fun_b(int x) {
    if (x == 42) throw std::runtime_error("too big");
    return x + 5;
}

serf::Future<serf::Var>::Ptr ExampleImpl::getitem(std::string const& key) {
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
