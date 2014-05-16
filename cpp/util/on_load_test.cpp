#include <serf/util/on_load.h>
#include <cxxtest/TestSuite.h>

using namespace serf;

static int counter = 0;

static void begin() {
    ++counter;
}

static void end() {
    --counter;
}

class OnLoadTest : public CxxTest::TestSuite
{
public:
    void testOnLoad() {
        TS_ASSERT_EQUALS(counter, 0);

        {
            OnLoad scope(begin, end);
            TS_ASSERT_EQUALS(counter, 1);
        }

        TS_ASSERT_EQUALS(counter, 0);
    }
};
