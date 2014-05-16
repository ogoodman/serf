#include <serf/rpc/serf_exception.h>

#include <serf/util/on_load.h>
#include <serf/util/debug.h>

namespace serf {
    SerfException::SerfException() {}
    SerfException::SerfException(std::string const& what) : msg_(what) {}

    /** Use Meyers singleton to provide a collection of Throwers. */
    Exceptions::throwers& Exceptions::reg() {
        static throwers reg_;
        return reg_;
    }

    /** Add a Thrower to the registry. */
    void Exceptions::add(std::string const& name, BaseThrower* thrower) {
        reg()[name] = boost::shared_ptr<BaseThrower>(thrower);
    }

    /** Throw one of the registered exceptions. */
    void Exceptions::throw_(std::vector<serf::Var> const& args) {
        std::string name(boost::get<std::string const&>(args[0]));
        throwers::const_iterator pos = reg().find(name);
        if (pos != reg().end()) {
            pos->second->throw_(args);
        }
        throw SerfException(repr(args));
    }

    NoSuchMethod::NoSuchMethod(std::string const& method_)
		: method(method_)
	{
        msg_ = "no method: " + method;
    }

    NoSuchMethod::NoSuchMethod(std::vector<Var> const& args)
        : method(boost::get<std::string const&>(args.at(1)))
    {
        msg_ = "no method: " + method;
    }

	Var NoSuchMethod::encode() const {
		std::vector<Var> enc(2);
		enc[0] = type();
		enc[1] = method;
		return enc;
	}

	std::string NoSuchMethod::type() const {
		return "NoSuchMethod";
	}

    NotEnoughArgs::NotEnoughArgs(std::string const& method_, int provided_, int required_)
		: method(method_), provided(provided_), required(required_)
	{
        std::ostringstream out;
        out << "method \"" << method << "\" called with " << provided << " arg(s). " << required << " required.";
        msg_ = out.str();
    }

    NotEnoughArgs::NotEnoughArgs(std::vector<Var> const& args)
        : method(boost::get<std::string const&>(args.at(1))),
          provided(boost::get<int32_t>(args.at(2))),
          required(boost::get<int32_t>(args.at(3))) {}

	std::string NotEnoughArgs::type() const {
		return "NotEnoughArgs";
	}

	Var NotEnoughArgs::encode() const {
		std::vector<Var> enc(4);
		enc[0] = type();
		enc[1] = method;
		enc[2] = provided;
		enc[3] = required;
		return enc;
	}

	TypeError::TypeError(std::string const& what) : SerfException(what) {
	}

    TypeError::TypeError(std::vector<Var> const& args)
        : SerfException(boost::get<std::string const&>(args.at(1))) {}

	std::string TypeError::type() const {
		return "TypeError";
	}

    NodeOffline::NodeOffline(int code_) : code(code_) {
        std::ostringstream out;
        out << "errno = " << code;
        msg_ = out.str();
    }

    NodeOffline::NodeOffline(std::vector<Var> const& args)
        : code(boost::get<int>(args.at(1))) {
        std::ostringstream out;
        out << "errno = " << code;
        msg_ = out.str();
    }

    Var NodeOffline::encode() const {
        std::vector<Var> exc_v(2);
        exc_v[0] = type();
        exc_v[1] = code;
        return exc_v;
    }
    
    std::string NodeOffline::type() const {
        return "NodeOffline";
    }

    static void registerExc() {
        Exceptions::add("NoSuchMethod", new Thrower<NoSuchMethod>);
        Exceptions::add("NotEnoughArgs", new Thrower<NotEnoughArgs>);
        Exceptions::add("TypeError", new Thrower<TypeError>);
        Exceptions::add("NodeOffline", new Thrower<NodeOffline>);
    }

    static OnLoad call(registerExc);
}
