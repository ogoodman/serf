#include <serf/rpc/connection_factory.h>

#include <serf/reactor/data_reader.h>
#include <serf/rpc/message_router.h>
#include <serf/rpc/connection.h>
#include <serf/util/debug.h>

namespace serf {

    /** \brief Makes a ReaderFactory whose handler is a Connection.
     *
     * When we make a client connection, i.e. when we are about to pass
     * this to a ConnectReader, we will want to install a ready-made
     * Connection because this will be needed by the MessageRouter
     * before the connection is actually established; hence the optional
     * Connection argument.
     */
    ConnectionFactory::ConnectionFactory(MessageRouter* router, Reactor* reactor, Connection* conn)
        : router_(router), reactor_(reactor), conn_(conn) {}

    ConnectionFactory::~ConnectionFactory() {
        delete conn_;
    }

    /** \brief Deals with failed client connection attempts.
     */
    void ConnectionFactory::error(std::string const& host, unsigned short port, int code) {
        // We get here when a connection we tried to make doesn't work out.
        // Messages might already have been buffered in the Connection
        // and some MessageHandler may be waiting for a response. We tell
        // the MessageRouter that the node has gone offline so it can tell
        // the MessageHandler that. That allows the MessageHandler to
        // make a suitable error callback on anything waiting for a
        // response from the node of this connection.
        router_->closing(conn_, code);
    }

    /** \brief Makes a DataReader configured with a Connection handler.
     *
     * If a Connection was passed in the constructor, that is used.
     * Otherwise a new Connection is made.
     */
    Reader* ConnectionFactory::makeReader(std::string const& host, unsigned short port, int fd) {
        Connection* conn;
        if (conn_) {
            // This is the client case. Should perhaps make it explicit
            // when constructing this factory.
            conn = conn_;
            conn_ = NULL;
            conn->connected(fd);
        } else {
            // Server case.
            conn = new Connection(router_, reactor_, fd, SERVER_WAIT_SSL_CHOICE);
            conn->send(SSL_OPTIONS, "P"); // TODO: enable "SP".
        }
        return new DataReader(fd, conn);
    }
}
