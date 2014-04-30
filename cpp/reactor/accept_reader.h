#ifndef ACCEPT_READER_HPP_
#define ACCEPT_READER_HPP_

#include <reader.h>

namespace demo {
    class Reactor;

    /** \brief Listens on a port and creates a new reader for each connection.
     *
     * To make a server you need a Reactor and an AcceptReader configured with
     * a port number and a ReaderFactory. The factory's makeReader method
     * should return a new DataReader configured with a suitable handler.
     */
    class AcceptReader : public Reader {
    public:
        AcceptReader(unsigned short port, ReaderFactory* factory);
        ~AcceptReader();
        int fd() const { return fd_; }
        void run(Reactor* reactor);

    private:
        int fd_;
        ReaderFactory* factory_;
    };
}

#endif
