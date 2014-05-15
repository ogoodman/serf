#ifndef NEXTGRID_DEBUG_H_
#define NEXTGRID_DEBUG_H_

#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <list>
#include <map>

#define SAY(a) std::cout << a << std::endl;
#define SHOW(a) std::cout << #a << " = " << a << std::endl

std::string repr(std::string const& s, char delim='"');
std::string repr(std::vector<unsigned char> const& data);
std::string repr(unsigned char ch);
std::string repr(bool b);

template <typename T>
std::string repr(T const& value) {
    std::ostringstream out;
    out << value;
    return out.str();
}

template <class T>
std::ostream& operator << (std::ostream& out, std::vector<T> vec) {
    out << "[";
    for (size_t i = 0, n = vec.size(); i < n; ++i) {
        if (i) out << ", ";
        out << repr(vec[i]);
    }
    return out << "]";
}

template <class T, class U>
std::ostream& operator << (std::ostream& out, std::map<T, U> const& m) {
    out << "{";
    typename std::map<T, U>::const_iterator i = m.begin(), e = m.end();
    bool first = true;
    for (; i != e; ++i) {
        if (!first) out << ", ";
        first = false;
        out << repr(i->first) << ": " << repr(i->second);
    }
    return out << "}";
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
