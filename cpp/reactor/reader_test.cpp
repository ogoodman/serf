#include <reader.h>
#include <cxxtest/TestSuite.h>
#include <debug.h>

// using namespace demo;

class ReaderTest : public CxxTest::TestSuite
{
public:
    void testReader() {
        SAY("Hello from test");
        TS_ASSERT(true);
    }
};
