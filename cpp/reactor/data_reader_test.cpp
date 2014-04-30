#include <data_reader.h>
#include <cxxtest/TestSuite.h>
#include <debug.h>

// using namespace demo;

class DataReaderTest : public CxxTest::TestSuite
{
public:
    void testDataReader() {
        SAY("Hello from test");
        TS_ASSERT(true);
    }
};
