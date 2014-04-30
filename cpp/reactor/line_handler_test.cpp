#include <line_handler.h>
#include <cxxtest/TestSuite.h>
#include <debug.h>

// using namespace demo;

class LineHandlerTest : public CxxTest::TestSuite
{
public:
    void testLineHandler() {
        SAY("Hello from test");
        TS_ASSERT(true);
    }
};
