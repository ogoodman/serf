#include <float_codec.h>
#include <cxxtest/TestSuite.h>

class FloatCodecTest : public CxxTest::TestSuite
{
public:
    void testFloatCodec() {
        FloatCodec fc;
        
        string pi_data("n\x86\x1b\xf0\xf9!\t@");
        TS_ASSERT_EQUALS(fc.encodes(3.14159), pi_data);
        TS_ASSERT_EQUALS(get<double>(fc.decodes(pi_data)), 3.14159);
    }
};
