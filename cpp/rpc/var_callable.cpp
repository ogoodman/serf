#include <serf/rpc/var_callable.h>

#include <sstream>

namespace serf {

    VarCallable::~VarCallable() {}

    VarCallException::VarCallException() {}
    VarCallException::VarCallException(std::string const& what) : msg_(what) {}

    NoSuchMethod::NoSuchMethod(std::string const& method) {
        msg_ = "no method: " + method;
    }

    NotEnoughArgs::NotEnoughArgs(std::string const& method, int provided, int required) {
        std::ostringstream out;
        out << "method \"" << method << "\" called with " << provided << " arg(s). " << required << " required.";
        msg_ = out.str();
    }

    VarExceptionDecoder::~VarExceptionDecoder() {}
}
