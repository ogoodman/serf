#include <accept_reader.h>
#include <cxxtest/TestSuite.h>
#include <debug.h>

// using namespace demo;

class AcceptReaderTest : public CxxTest::TestSuite
{
public:
    void testAcceptReader() {
        SAY("Hello from test");
        TS_ASSERT(true);
    }
};
