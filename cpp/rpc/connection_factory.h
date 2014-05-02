#ifndef CONNECTION_FACTORY_HGUARD_
#define CONNECTION_FACTORY_HGUARD_

#include <serf/reactor/reader.h>

namespace serf {
    class MessageRouter;
    class Reactor;
    class Connection;

    // As described for Connection, when passed to a ConnectReader
    // we want to make a Connection right away and have the
    // factory hook that up to the DataReader it makes when the connection
    // succeeds. If the connection fails a closing() call will be made
    // on the MessageRouter, enabling it to notify its MessageHandler.
    
    /** \brief Used by the MessageRouter to set up Connections.
     */
    class ConnectionFactory : public ReaderFactory
    {
    public:
        ConnectionFactory(MessageRouter* router, Reactor* reactor, Connection* conn=NULL);
        ~ConnectionFactory();

        virtual void error(std::string const& host, unsigned short port, int fd);
        virtual Reader* makeReader(std::string const& host, unsigned short port, int fd);

    private:
        MessageRouter* router_; // not owned.
        Reactor* reactor_; // not owned.
        Connection* conn_; // owned (or null).
    };
}

#endif // CONNECTION_FACTORY_HGUARD_
