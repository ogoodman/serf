#ifndef NEXTGRID_DEBUG_H_
#define NEXTGRID_DEBUG_H_

#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <iomanip>
#include <list>

using namespace std;

#define SAY(a) cout << a << endl;
#define SHOW(a) cout << #a << " = " << a << endl

inline std::string repr(std::string const& s, char delim='"') {
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

inline std::string repr(vector<unsigned char> const& data) {
    return repr(string((char*)&*data.begin(), data.size()));
}

inline std::string repr(unsigned char ch) {
    return repr(string(1, char(ch)), '\'');
}

template <class T>
std::ostream& operator << (std::ostream& out, std::vector<T> vec) {
    out << "[";
    for (size_t i = 0, n = vec.size(); i < n; ++i) {
        if (i) out << ", ";
        out << vec[i];
    }
    return out << "]";
}

template <class T>
std::ostream& operator << (std::ostream& out, std::list<T> const& L) {
    out << "(";
    typename std::list<T>::const_iterator i = L.begin(), e = L.end();
    bool first = true;
    for (; i != e; ++i) {
        if (!first) out << ", ";
        first = false;
        out << *i;
    }
    return out << ")";
}

#endif
