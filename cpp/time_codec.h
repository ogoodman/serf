#ifndef TIME_CODEC_HGUARD_
#define TIME_CODEC_HGUARD_

#include <boost/date_time/posix_time/posix_time_types.hpp>
#include <codec.h>

namespace serf {

    class TimeCodec : public Codec {
    public:
        virtual std::string typeName();
        virtual void encodeType(std::ostream& out);
        virtual void encode(std::ostream& out, Var const& value, Context& ctx);
        virtual void decode(std::istream& in, Var& value, Context& ctx);
    
        void encode(std::ostream& out, boost::posix_time::ptime value);
    
        class Factory : public CodecFactory {
        public:
            virtual CodecP decodeType(std::istream& in, Context& ctx);
            virtual char typeByte() const;
        };
    };
    
    boost::posix_time::time_duration my_microseconds(int64_t usec);
    boost::posix_time::ptime epochUSecToPtime(int64_t usec);
    int64_t ptimeToEpochUSec(boost::posix_time::ptime t);
}



#endif // TIME_CODEC_HGUARD_
