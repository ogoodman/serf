#include <serf/reactor/accept_reader.h>

#include <stdexcept>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <strings.h>
#include <unistd.h>
#include <serf/reactor/reactor.h>
#include <serf/debug.h>

namespace serf {

    const int MAX_QUEUED = 10;

    AcceptReader::AcceptReader(unsigned short port, ReaderFactory* factory) :
        factory_(factory)
    {
        fd_ = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

        struct sockaddr_in socket_address;
        bzero(&socket_address, sizeof(socket_address));
        socket_address.sin_family = AF_INET;
        socket_address.sin_port = htons(port);
        int ret = inet_aton("0.0.0.0", &socket_address.sin_addr);

        ret = bind(fd_, (struct sockaddr*)&socket_address,
                   sizeof(struct sockaddr_in));
        if (ret) throw std::runtime_error("bind failed");

        if (!port) {
            // Not sure this works.
            struct sockaddr_storage sock_addr;
            socklen_t len;
            getsockname(fd_, (struct sockaddr*)&sock_addr, &len);
            port = ntohs(((struct sockaddr_in&)sock_addr).sin_port);
            SHOW(port);
        }

        ret = listen(fd_, MAX_QUEUED);
        if (ret) throw std::runtime_error("listen failed");
    }

    AcceptReader::~AcceptReader() {
        close(fd_);
        delete factory_;
    }
    
    void AcceptReader::run(Reactor* reactor) {
        struct sockaddr client_address;
        socklen_t client_address_len;
        int conn_fd = accept(fd_, &client_address, &client_address_len);
        // FIXME: extract the client address here..
        Reader* reader = factory_->makeReader("", 0, conn_fd);
        if (reader) reactor->addReader(reader);
    }
}
