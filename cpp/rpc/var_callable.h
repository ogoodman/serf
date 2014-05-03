#ifndef VAR_CALLABLE_HGUARD_
#define VAR_CALLABLE_HGUARD_

#include <stdexcept>
#include <serf/serializer/var.h>

namespace serf {

    /** \brief Interface which remotely callable instances must implement.
     */
    class VarCallable
    {
    public:
        virtual ~VarCallable();

        virtual Var varCall_(std::string const& method, std::vector<Var> const& args) = 0;
    };

    class VarCallException : public std::exception
    {
    public:
        VarCallException();
        VarCallException(std::string const& what);
        ~VarCallException() throw() {}

        const char* what() const throw() {
            return msg_.c_str();
        }
    protected:
        std::string msg_;
    };

    class NoSuchMethod : public VarCallException
    {
    public:
        NoSuchMethod(std::string const& method);
    };

    class NotEnoughArgs : public VarCallException
    {
    public:
        NotEnoughArgs(std::string const& method, int provided, int required);
    };
}

#endif // VAR_CALLABLE_HGUARD_
