#include <serf/rpc/message_router.h>

#include <sstream>
#include <serf/reactor/reactor.h>
#include <serf/reactor/connect_reader.h>
#include <serf/rpc/connection_factory.h>
#include <serf/rpc/connection.h>
#include <serf/rpc/message_handler.h>
#include <serf/util/debug.h>

namespace serf {

    MessageRouter::MessageRouter(MessageHandler* handler, Reactor* reactor)
        : handler_(handler), reactor_(reactor), shutdown_(false) {}

    void MessageRouter::handle(Connection* conn, int what, std::string const& msg) {
        if (what == MSG) {
            node_map::const_iterator pos = node_.find(conn);
            if (pos == node_.end()) {
                SAY("ignoring message from unknown node");
            } else {
                try {
                    handler_->handle(pos->second, msg);
                } catch (std::exception& e) {
                    SAY("handler threw exception " << e.what() << " on message " << repr(msg));
                } catch (...) { // An exception would kill the reactor.
                    SAY("handler threw an unknown exception on message " << repr(msg));
                }
            }
        } else if (what == NODE_NAME) {
            // FIXME: what is the protocol for establishing identity here?
            if (conn_.find(msg) != conn_.end()) {
                SAY("node " << msg << " is already connected!");
            } else {
                node_[conn] = msg;
                conn_[msg] = conn;
            }
        } else if (what == CLOSE) {
            // Notify the MessageHandler.
            closing(conn);
            // Removes reader from the reactor which causes reader and
            // Connection to be deleted and the socket closed.
            reactor_->removeReader(conn->fd());
        }
    }

    void MessageRouter::shutdown() {
        shutdown_ = true;
        std::map<Connection*, std::string>::iterator it, e = node_.end();
        for (it = node_.begin(); it != e; ++it) {
            it->first->send(CLOSE, "");
        }
        if (!node_.size()) {
            reactor_->stop();
        }
    }

    void MessageRouter::closing(Connection* conn, int code) {
        std::string node = node_[conn];
        if (node_.size()) handler_->offline(node, code);
        conn_.erase(node);
        node_.erase(conn);
        if (shutdown_ && conn_.size() == 0) {
            reactor_->stop();
        }
    }

    void MessageRouter::send(std::string const& node, std::string const& msg) {
        if (conn_.find(node) == conn_.end()) {
            Connection* conn = new Connection(this, reactor_);
            conn_[node] = conn;
            node_[conn] = node;
            ConnectionFactory* f = new ConnectionFactory(this, reactor_, conn);
            
            std::string host = node;
            unsigned short port = 6502;
            size_t pos = node.find(':');
            if (pos != std::string::npos) {
                host = node.substr(0, pos);
                std::istringstream num(node.substr(pos + 1));
                num >> port;
            }

            ConnectReader* cr = new ConnectReader(host, port, f);
            reactor_->addReader(cr);

            // FIXME: this is not always my node name!
            conn->send(int(NODE_NAME), "127.0.0.1:6504");
        }
        conn_[node]->send(int(MSG), msg);
    }

}
