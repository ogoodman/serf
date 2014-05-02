#ifndef CONNECTION_HGUARD_
#define CONNECTION_HGUARD_

#include <string>
#include <vector>
#include <serf/reactor/reader.h>
#include <serf/reactor/data_handler.h>

namespace serf {
    class MessageRouter;
    class Reactor;

    /** \brief Encapsulates peer connections for a MessageRouter.
     *
     * Defragments incoming data getting the control byte and message
     * body and passing them to its message router. It also handles
     * outbound data, encoding control byte and body into the outbound
     * stream.
     *
     * The actual stream protocol is repeats of a single control byte,
     * a four byte message-length, and then the message data.
     */
    class Connection : public DataHandler
    {
    public:
        Connection(MessageRouter* handler, Reactor* reactor, int fd=-1);
        ~Connection();

        virtual void handle(std::string const& data);

        void send(int what, std::string const& msg);
        void connected(int fd);
        int fd() const;

    private:
        void send_(std::string const& data);

        MessageRouter* router_; // not owned.
        Reactor* reactor_; // not owned.
        int fd_;
        std::string buffer_;
        // If fd_ is not yet set messages to be sent are queued.
        std::vector<std::string> queued_;
    };
}

#endif // CONNECTION_HGUARD_
