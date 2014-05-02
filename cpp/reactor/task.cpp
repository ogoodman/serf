#include <serf/reactor/task.h>

namespace serf {

    Clock::~Clock() {}

    Task::~Task() {}

    int64_t Clock::days(int64_t n) {
        return n * 1000000 * 3600 * 24;
    }
    
    int64_t Clock::seconds(int64_t n) {
        return n * 1000000;
    }

    int64_t Clock::milliseconds(int64_t n) {
        return n * 1000;
    }
}
