#ifndef RPC_HANDLER_HGUARD_
#define RPC_HANDLER_HGUARD_

#include <map>
#include <serf/rpc/var_caller.h>
#include <serf/rpc/message_handler.h>

namespace serf {

    class MessageRouter;
    class VarCallable;

    /** \brief Container for remotely callable objects.
     *
     * This implements the MessageHandler interface so as to receive
     * method calls from remote nodes via a MessageRouter. It must 
     * be configured with (the same) MessageRouter in order to send
     * return values and exceptions to remote nodes
     *
     * It also implements VarCaller in order to provide proxies
     * with the means to make outbound calls.
     */
    class RPCHandler : public MessageHandler, public VarCaller
    {
    public:
        RPCHandler(MessageRouter* router=NULL);
        ~RPCHandler();

        /** \brief Configure with a MessageRouter if one was not provided
         *  to the constructor.
         */
        void setRouter(MessageRouter* router);

        void offline(std::string const& node, int code);
        void handle(std::string const& node, std::string const& msg);

        Future<Var>::Ptr callRemote(std::string const& node, Var& call);
    private:
        MessageRouter* router_; // not owned.
        VarCallable* servant_; // owned.
        std::map<std::string, Future<Var>::Ptr> callbacks_;
    };

    std::string randomString(size_t len);
}

#endif // RPC_HANDLER_HGUARD_
