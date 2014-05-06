#ifndef VAR_CALLER_HGUARD_
#define VAR_CALLER_HGUARD_

#include <serf/serializer/var.h>
#include <serf/reactor/future.h>

namespace serf {

    class VarCaller
    {
    public:
        ~VarCaller();

        /** \brief Interface for making remote calls.
         *
         * Takes an RMI call {"o":...} as a Var and returns a Future<Var>
         * containing {"r":...} or {"e":...} or throws due to some local
         * error. It is the responsibility of the VarCaller to add
         * the reply address to the outgoing message.
         */
        virtual Future<Var>::Ptr callRemote(std::string const& node, Var const& call) = 0;
    };
}

#endif // VAR_CALLER_HGUARD_
