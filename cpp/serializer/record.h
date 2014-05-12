#ifndef RECORD_HGUARD_
#define RECORD_HGUARD_

#include <string>
#include <boost/shared_ptr.hpp>

namespace serf {

    class Codec;

    template <typename T>
    class RecordT
    {
    public:
        RecordT(std::string const& type_name_, T const& value_, int type_id_=0, boost::shared_ptr<Codec> codec_=boost::shared_ptr<Codec>())
            : type_name(type_name_), value(value_), type_id(type_id_), codec(codec_) {}

        bool operator== (RecordT const& other) const {
            if (type_name == "@") {
                return type_name == other.type_name &&
                    type_id == other.type_id &&
                    value == other.value;
            }
            return type_name == other.type_name &&
                value == other.value;
        }

        bool operator != (RecordT const& other) const {
            return !(this == other);
        }
    public:
        std::string type_name;
        T value;
        int type_id;
        boost::shared_ptr<Codec> codec;
    };
}

#endif // RECORD_HGUARD_
