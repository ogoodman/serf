#include <accept_reader.h>

#include <stdexcept>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <reactor.h>
#include <debug.h>

namespace demo {

    const int MAX_QUEUED = 10;

    AcceptReader::AcceptReader(unsigned short port, ReaderFactory* factory) :
        factory_(factory)
    {
        fd_ = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        SHOW(fd_);

        struct in_addr address;
        int ret = inet_aton("0.0.0.0", &address);

        // Looks like addr, of type sockaddr_storage can be reinterpreted
        // as sockaddr and passed to bind.
        // size will be sizeof(sockaddr(in)).

        struct sockaddr_in socket_address;
        bzero(&socket_address, sizeof(socket_address));
        socket_address.sin_family = AF_INET;
        socket_address.sin_port = htons(port);
        socket_address.sin_addr.s_addr = address.s_addr;

        ret = bind(fd_, (struct sockaddr*)&socket_address,
                   sizeof(struct sockaddr_in));
        if (ret) throw std::runtime_error("bind failed");

        if (!port) {
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
        SAY("closing fd: " << fd_);
        close(fd_);
        delete factory_;
    }
    
    void AcceptReader::run(Reactor* reactor) {
        struct sockaddr client_address;
        socklen_t client_address_len;
        int conn_fd = accept(fd_, &client_address, &client_address_len);
        Reader* reader = factory_->makeReader(conn_fd);
        if (reader) reactor->addReader(reader);
    }
}
