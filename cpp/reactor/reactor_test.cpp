#include <reactor.h>
#include <cxxtest/TestSuite.h>
#include <debug.h>

// using namespace demo;

class ReactorTest : public CxxTest::TestSuite
{
public:
    void testReactor() {
        SAY("Hello from test");
        TS_ASSERT(true);
    }
};
