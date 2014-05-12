#include <serf/reactor/reactor.h>
#include <cxxtest/TestSuite.h>
#include <serf/reactor/task.h>
#include <serf/util/debug.h>

namespace serf {
    class MockClock : public Clock
    {
    public:
		MockClock() : t_(0) {}

	int64_t time() const {
	    return t_;
	}

	void advance(int64_t usec) {
	    t_ += usec;
	}
    private:
		int64_t t_;
    };
}

using namespace serf;

class ReactorTest : public CxxTest::TestSuite
{
public:
    void testReactor() {
        TS_ASSERT(true);
    }
};
