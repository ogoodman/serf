#ifndef DATA_READER_HPP_
#define DATA_READER_HPP_

#include <reader.h>

namespace demo {

    class DataHandler;
    class Reactor;

    /** \brief Moves data from a socket to a handler.
     *
     * Readers are added to the reactor and each time their socket
     * becomes ready to read, their run function is called. The
     * run function of a DataReader simply reads a chunk of up to 4k
     * of data from its socket and passes it to its handler. If the
     * socket return 0 bytes, i.e. if it has been closed, the reader
     * will remove itself from the reactor, which will, in turn,
     * cause it and its DataHandler to be deleted.
     */
    class DataReader : public Reader {
    public:
        DataReader(int fd, DataHandler* handler);
        ~DataReader();

        int fd() const;
        void run(Reactor* reactor);
    private:
        int fd_;
        DataHandler* handler_;
    };
}

#endif
