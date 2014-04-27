#include <time_codec.h>

#include <int_codec.h>

using namespace boost;
using namespace boost::posix_time;

time_duration my_microseconds(int64_t usec) {
    // Some versions of boost_time at least suffer from overflow
    // when trying to construct a time_duration from a number
    // of microseconds bigger than 2^31. Here is a replacement.
    int64_t n_16M = 16000000;
    int64_t low = usec % n_16M;
    int64_t mid = usec / n_16M % n_16M;
    int64_t top = usec / n_16M / n_16M;
    time_duration secs(71111 * top, 6 * top, 40 * top + 16 * mid);
    return secs + microseconds(low);
}

ptime epochUSecToPtime(int64_t usec) {
    ptime t0(gregorian::date(1970,gregorian::Jan,1));
    return t0 + my_microseconds(usec);
}

int64_t ptimeToEpochUSec(ptime t) {
    ptime t0(gregorian::date(1970,gregorian::Jan,1));
    return (t - t0).total_microseconds();
}

std::string TimeCodec::typeName() {
    return "TIME";
}

void TimeCodec::encodeType(std::ostream& out) {
    out << 't';
}

void TimeCodec::encode(std::ostream& out, Var const& value, Context& ctx) {
    encode(out, boost::get<ptime>(value));
}

void TimeCodec::decode(std::istream& in, Var& value, Context& ctx) {
    IntCodec ic(8);
    value = epochUSecToPtime(ic.decode(in));
}

void TimeCodec::encode(std::ostream& out, boost::posix_time::ptime value) {
    IntCodec ic(8);
    ic.encode(out, ptimeToEpochUSec(value));
}

CodecP TimeCodec::Factory::decodeType(std::istream& in, Context& ctx) {
    return CodecP(new TimeCodec());
}

char TimeCodec::Factory::typeByte() const {
    return 't';
}
