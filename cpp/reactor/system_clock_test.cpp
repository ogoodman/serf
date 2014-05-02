#include <serf/reactor/system_clock.h>
#include <cxxtest/TestSuite.h>

using namespace serf;

class SystemClockTest : public CxxTest::TestSuite
{
public:
    void testSystemClock() {
        SystemClock clock;
        int64_t t = clock.time();
        TS_ASSERT(t > 1399021504000000LL);
        TS_ASSERT(t < 2399021504000000LL);
    }
};
