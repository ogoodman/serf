#include <serf/rpc/connection.h>

#include <sys/socket.h>
#include <serf/reactor/reactor.h>
#include <serf/rpc/message_router.h>
#include <serf/debug.h>

static uint32_t decode_uint32(std::string const& data) {
    // Approximately duplicates code in int_codec.cpp.
    char ch;
    uint32_t result = 0;
    for (size_t i = 0; i < 4; ++i) {
        ch = data[i];
        result <<= 8;
        result += (unsigned char)ch;
    }
    return result;
}

static std::string encode_uint32(uint32_t value) {
    std::string result = "";
    for (int i = 3; i >= 0; --i) {
        result += char((value >> 8*i) & 0xFF);
    }
    return result;
}


namespace serf {

    Connection::Connection(MessageRouter* router, Reactor* reactor, int fd)
        : router_(router), reactor_(reactor), fd_(fd) {}

    Connection::~Connection() {
        router_->closing(this);
    }

    /** \brief Receive incoming data from our owning DataReader.
     *
     * Once suitably defragmented, each control byte, message pair
     * are passed to the MessageRouter.
     */
    void Connection::handle(std::string const& data) {
        buffer_ += data;
        while (buffer_.size() >= 5) {
            int what = int(buffer_[0]);
            size_t len = decode_uint32(buffer_.substr(1, 4));

            if (buffer_.size() < len + 5) break;

            router_->handle(this, what, buffer_.substr(5, len));
            buffer_.erase(0, len + 5);
        }
    }
    
    void Connection::send_(std::string const& data) {
        ::send(fd_, data.data(), data.size(), 0);
    }

    /** \brief Encode and send the given control byte and message.
     *
     * This may buffer messages if the socket connection is not yet
     * established. Buffered messages will be sent when the connected()
     * function is called (by the ConnectionFactory).
     */
    void Connection::send(int what, std::string const& msg) {
        std::string header = std::string(1, char(what)) + encode_uint32(msg.size());
        if (fd_ < 0) {
            queued_.push_back(header + msg);
        } else {
            send_(header);
            send_(msg);
        }
    }

    /** \brief Update the Connection with an established socket.
     *
     * When making a client connection we use the Connection object
     * to buffer messages to be sent while the ConnectReader is doing
     * its work. When the ConnectReader tells the ConnectionFactory
     * that the socket is ready, the factory calls this function to
     * start sending all outbound messages.
     */
    void Connection::connected(int fd) {
        fd_ = fd;
        size_t i, n = queued_.size();
        for (i = 0; i < n; ++i) {
            send_(queued_[i]);
        }
        queued_.resize(0);
    }

    int Connection::fd() const {
        return fd_;
    }
}
