#ifndef SYSTEM_CLOCK_HGUARD_
#define SYSTEM_CLOCK_HGUARD_

#include <serf/reactor/task.h>

namespace serf {

    class SystemClock : public Clock
    {
    public:
        virtual int64_t time() const;
    };
}

#endif // SYSTEM_CLOCK_HGUARD_
