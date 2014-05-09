#include <serf/rpc/var_callable.h>

#include <sstream>

namespace serf {

    VarCallable::~VarCallable() {}

    bool VarCallable::tryGet_(Result<void>& result, Var& exc) {
        try {
            result.get();
            return true;
        } catch (std::exception& e) {
            std::vector<Var> exc_v(2);
            exc_v[0] = std::string("Exception");
            exc_v[1] = std::string(e.what());
            exc = exc_v;
            return false;
        }
    }

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
}
