#ifndef SERF_EXCEPTION_HGUARD_
#define SERF_EXCEPTION_HGUARD_

#include <string>
#include <stdexcept>
#include <serf/serializer/var.h>

namespace serf {

    class SerfException : public std::exception
    {
    public:
        SerfException();
        SerfException(std::string const& what);
        ~SerfException() throw() {}

        const char* what() const throw() {
            return msg_.c_str();
        }

		virtual std::string type() const {
			return "SerfException";
		}

		virtual Var encode() const {
			std::vector<Var> exc(2);
			exc[0] = type();
			exc[1] = std::string(what());
			return exc;
		}
    protected:
        mutable std::string msg_;
    };

    /** Instances throw dynamically constructed exceptions. */
    class BaseThrower {
    public:
        virtual ~BaseThrower() {}
        virtual void throw_(std::vector<serf::Var> const& args) = 0;
    };

    /** Instances throw exceptions of type E constructed with the given args. */
    template <typename E>
    class Thrower : public BaseThrower {
    public:
        void throw_(std::vector<serf::Var> const& args) {
            throw E(args);
        }
    };

    /** Registry of dynamically throwable exceptions. */
    class Exceptions
    {
    public:
        typedef std::map<std::string, boost::shared_ptr<BaseThrower> > throwers;
        static throwers& reg();
        static void add(std::string const& name, BaseThrower* thrower);
        static void throw_(std::vector<serf::Var> const& args);
    };

    class NoSuchMethod : public SerfException
    {
    public:
        NoSuchMethod(std::string const& method);
        NoSuchMethod(std::vector<Var> const& args);
		~NoSuchMethod() throw() {}

		Var encode() const;
		std::string type() const;
	public:
		std::string method;
    };

    class NotEnoughArgs : public SerfException
    {
    public:
        NotEnoughArgs(std::string const& method, int provided, int required);
        NotEnoughArgs(std::vector<Var> const& args);
		~NotEnoughArgs() throw() {}

		Var encode() const;
		std::string type() const;
	public:
		std::string method;
		int provided;
		int required;
    };

	class TypeError : public SerfException
	{
	public:
		TypeError(std::string const& what);
        TypeError(std::vector<Var> const& args);
		~TypeError() throw() {}

		std::string type() const;
	};

    class NodeOffline : public SerfException
    {
    public:
        NodeOffline(int code);
        NodeOffline(std::vector<Var> const& args);
        ~NodeOffline() throw() {}

        Var encode() const;
        std::string type() const;
    public:
        int code;
    };
}

#endif // SERF_EXCEPTION_HGUARD_
