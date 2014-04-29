#ifndef VAR_HGUARD_
#define VAR_HGUARD_

#include <stdint.h>
#include <map>
#include <string>
#include <vector>
#include <ostream>
#include <boost/variant.hpp>
#include <boost/date_time/posix_time/posix_time_types.hpp>
#include <boost/shared_ptr.hpp>

namespace serf {

    class Codec;
    
    typedef unsigned char byte;
    typedef boost::make_recursive_variant<
        boost::blank,
        bool,
        byte,
        int32_t,
        int64_t,
        double,
        boost::posix_time::ptime,
        std::string,
        std::vector<boost::recursive_variant_>,
        std::map<std::string, boost::recursive_variant_>,
        boost::shared_ptr<Codec>
    >::type Var;
    
    std::ostream& operator<< (std::ostream& out, Var const& value);
    std::string toStr(Var const& value);
    
    inline std::vector<Var>& V(Var& value) {
        return boost::get<std::vector<Var>&>(value);
    }
    inline std::vector<Var> const& V(Var const& value) {
        return boost::get<std::vector<Var> const&>(value);
    }
    inline std::map<std::string,Var>& M(Var& value) {
        return boost::get<std::map<std::string,Var>&>(value);
    }
    inline std::map<std::string,Var> const& M(Var const& value) {
        return boost::get<std::map<std::string,Var> const&>(value);
    }
}

#endif // VAR_HGUARD_
