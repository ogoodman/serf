#include <serf/serializer/time_codec.h>
#include <cxxtest/TestSuite.h>

#include <serf/util/debug.h>
#include <sstream>

using namespace boost;
using namespace boost::posix_time;
using namespace boost::gregorian;
using namespace serf;

class TimeCodecTest : public CxxTest::TestSuite
{
public:
    void testTimeCodec() {
        TimeCodec::Factory tcf;
        TS_ASSERT_EQUALS(tcf.typeByte(), 't');
        Context ctx;
        istringstream in("");
        CodecP tc = tcf.decodeType(in, ctx);
        TSM_ASSERT("Should not be at EOF", in); // Nothing read.

        ostringstream out;
        tc->encodeType(out);
        TS_ASSERT_EQUALS(out.str(), "t");
        ptime dob(date(1965, Jul, 18), time_duration(1, 23, 45));
        string enc("\xff\xff\x80\x13""e\xdc\xea@");
        TS_ASSERT_EQUALS(tc->encodes(dob), enc);
        TS_ASSERT_EQUALS(boost::get<ptime>(tc->decodes(enc)), dob);
    }

    void testMyMicroseconds() {
        // Some versions of boost::date_time have buggy microseconds func.
        int64_t n = 123456789012345678;
        time_duration d = my_microseconds(n);
        TS_ASSERT_EQUALS(d.total_microseconds(), n);
        time_duration md = my_microseconds(-n);
        TS_ASSERT_EQUALS(md.total_microseconds(), -n);
        TS_ASSERT_EQUALS(ptimeToEpochUSec(epochUSecToPtime(n)), n);
        TS_ASSERT_EQUALS(ptimeToEpochUSec(epochUSecToPtime(-n)), -n);
    }
};
