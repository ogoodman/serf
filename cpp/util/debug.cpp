#include <serf/util/debug.h>

#include <sstream>
#include <iomanip>

using namespace std;

std::string repr(std::string const& s, char delim) {
    ostringstream result;
    result << hex;
    result << delim;
    for (size_t i = 0, n = s.length(); i < n; ++i) {
        if (s[i] < ' ' || ((unsigned char)s[i]) > 0x7E) {
            result << "\\x" << setfill('0') << setw(2) <<
                uppercase << int((unsigned char)s[i]);
        } else {
            result << s[i];
        }
    }
    result << delim;
    return result.str();
}

std::string repr(std::vector<unsigned char> const& data) {
    return repr(string((char*)&*data.begin(), data.size()));
}

std::string repr(unsigned char ch) {
    return repr(string(1, char(ch)), '\'');
}

std::string repr(bool b) {
    return b ? "true" : "false";
}
