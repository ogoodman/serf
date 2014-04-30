#include <data_handler.h>
#include <cxxtest/TestSuite.h>
#include <debug.h>

// using namespace demo;

class DataHandlerTest : public CxxTest::TestSuite
{
public:
    void testDataHandler() {
        SAY("Hello from test");
        TS_ASSERT(true);
    }
};
