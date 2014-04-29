#include <var.h>

#include <stdexcept>
#include <debug.h>
#include <boost/date_time/posix_time/posix_time.hpp>
#include <codec.h>

using namespace std;
using namespace boost;

namespace serf {

    class Printer : public static_visitor<void>
    {
    public:
        Printer(ostream& out) : out_(&out) {}
    
        void operator() (blank value) const;
        void operator() (bool value) const;
        void operator() (byte value) const;
        void operator() (int32_t value) const;
        void operator() (int64_t value) const;
        void operator() (double value) const;
        void operator() (posix_time::ptime value) const;
        void operator() (string const& value) const;
        void operator() (vector<Var> const& value) const;
        void operator() (map<string,Var> const& value) const;
        void operator() (CodecP value) const;
    
    private:
        ostream* out_;
    };
    
    ostream& operator<< (ostream& out, Var const& value) {
        apply_visitor(Printer(out), value);
        return out;
    }
    
    void Printer::operator() (blank value) const {
        (*out_) << "null";
    }
    void Printer::operator() (bool value) const {
        (*out_) << (value ? "true" : "false");
    }
    void Printer::operator() (byte value) const {
        (*out_) << repr(value);
    }
    void Printer::operator() (int64_t value) const {
        (*out_) << value;
    }
    void Printer::operator() (int32_t value) const {
        (*out_) << value;
    }
    void Printer::operator() (double value) const {
        (*out_) << value;
    }
    void Printer::operator() (posix_time::ptime value) const {
        (*out_) << "time(\"" << value << "\")";
    }
    void Printer::operator() (string const& value) const {
        (*out_) << repr(value);
    }
    void Printer::operator() (vector<Var> const& value) const {
        size_t i, n = value.size();
        (*out_) << '[';
        for (i = 0; i < n; ++i) {
            if (i) (*out_) << ", ";
            apply_visitor(*this, value[i]);
        }
        (*out_) << ']';
    }
    void Printer::operator() (map<string,Var> const& value) const {
        (*out_) << '{';
        map<string,Var>::const_iterator i, e=value.end();
        bool first = true;
        for (i = value.begin(); i != e; ++i) {
            if (!first) (*out_) << ", ";
            (*out_) << repr(i->first) << ": " << i->second;
            first = false;
        }
        (*out_) << '}';
    }
    void Printer::operator() (CodecP value) const {
        (*out_) << value->typeName();
    }
    
    string toStr(Var const& value) {
        ostringstream result;
        result << value;
        return result.str();
    }
}
