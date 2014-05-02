#ifndef MESSAGE_ROUTER_HGUARD_
#define MESSAGE_ROUTER_HGUARD_

#include <map>
#include <string>

namespace serf {

    class Connection;
    class MessageHandler;
    class Reactor;

    enum {
        MSG = 0,
        NODE_NAME = 1,
        CLOSE = 2
    };

    /** \brief Hides peer connections behind a send-to-node abstraction.
     *
     * When we send a message, a connection is made to the named node
     * if we don't already have one.
     *
     * Incoming messages will be passed to the configured MessageHandler
     * together with the name of the node they came from.
     *
     * Although the message sending interface is basically fire-and-forget
     * we do want the MessageHandler to be reliably informed of any
     * connection errors we can detect. The way it works is that as soon
     * as we detect an error we call offline() on the MessageHandler.
     * If we have a useful error code (errno), such as 61 meaning
     * "connection refused", we pass it along with the offline() call.
     */
    class MessageRouter
    {
    public:
        MessageRouter(MessageHandler* handler, Reactor* reactor);

        void send(std::string const& node, std::string const& msg);

        void handle(Connection* conn, int what, std::string const& msg);
        void closing(Connection* conn, int code=0);
    private:
        typedef std::map<Connection*, std::string> node_map;
        typedef std::map<std::string, Connection*> conn_map;

        MessageHandler* handler_; // not owned.
        Reactor* reactor_; // not owned.

        node_map node_;
        conn_map conn_;
    };
}

#endif // MESSAGE_ROUTER_HGUARD_
