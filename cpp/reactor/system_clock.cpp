#include <serf/reactor/system_clock.h>

#include <sys/time.h>
#include <stdexcept>

namespace serf {

    int64_t SystemClock::time() const {
        timeval result;
        int ret = gettimeofday(&result, NULL);
        if (ret != 0) throw std::runtime_error("gettimeofday failed");
        return result.tv_usec + 1000000 * result.tv_sec;
    }
}
