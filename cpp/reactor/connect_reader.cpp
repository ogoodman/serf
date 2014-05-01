#include <serf/reactor/connect_reader.h>

#include <unistd.h>
#include <fcntl.h>
#include <arpa/inet.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <errno.h>
#include <stdexcept>

#include <serf/reactor/reactor.h>
#include <serf/debug.h>

namespace serf {
    
    /** \brief Make a reader which will connect to host:port and pass the
     *  result to handler->makeReader().
     *
     * This generally won't throw but it may if host is illegal.
     * Takes ownership of the factory.
     */
    ConnectReader::ConnectReader(std::string const& host, unsigned short port, ReaderFactory* factory) : host_(host), port_(port), factory_(factory), count_(0) {
        // Make a socket and set fd_
        fd_ = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        SHOW(fd_);

        // Construct the address.
        struct sockaddr_in socket_address;
        bzero(&socket_address, sizeof(socket_address));
        socket_address.sin_family = AF_INET;
        socket_address.sin_port = htons(port);
        int ret = inet_aton(host.c_str(), &socket_address.sin_addr);
        if (ret < 0) {
            factory_->error(host, port, errno);
            close(fd_);
            throw std::runtime_error("socket address error");
        }

        // Make the socket non-blocking.
        fcntl(fd_, F_SETFL, O_NONBLOCK);

        // Call a non-blocking connect
        ret = connect(fd_, (sockaddr*)&socket_address, sizeof(socket_address));
        if (ret < 0) {
            if (!(errno == EINPROGRESS || errno == EWOULDBLOCK)) {
                factory_->error(host, port, errno);
                close(fd_);
                throw std::runtime_error("socket connect error");
            }
        }
    }

    ConnectReader::~ConnectReader() {
        // fd_ will be zero if original fd_ passed to a new reader.
        if (fd_) close(fd_);
        delete factory_;
    }

    int ConnectReader::fd() const {
        return fd_;
    }

    void ConnectReader::run(Reactor* reactor) {
        int err = 0;
        socklen_t optlen;
        getsockopt(fd_, SOL_SOCKET, SO_ERROR, &err, &optlen);

        if (err == 0) {
            int fd = fd_;
            Reader* reader = factory_->makeReader(host_, port_, fd);
            // A side effect of either branch below will be to delete this
            // so we must not do anything else in this call.
            if (reader) {
                // Ownership of fd_ passed to the new reader.
                fd_ = 0;
                reactor->addReader(reader);
            } else {
                reactor->removeReader(fd_);
            }
        } else {
            // Connection failed somewhere.
            factory_->error(host_, port_, err);
            reactor->removeReader(fd_);
        }
    }
}
