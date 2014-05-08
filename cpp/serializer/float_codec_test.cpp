#include <serf/serializer/float_codec.h>
#include <cxxtest/TestSuite.h>

using namespace serf;

class FloatCodecTest : public CxxTest::TestSuite
{
public:
    void testFloatCodec() {
        FloatCodec fc;
        
        string pi_data("@\t!\xf9\xf0\x1b\x86n");
        TS_ASSERT_EQUALS(fc.encodes(3.14159), pi_data);
        TS_ASSERT_EQUALS(get<double>(fc.decodes(pi_data)), 3.14159);
    }
};
