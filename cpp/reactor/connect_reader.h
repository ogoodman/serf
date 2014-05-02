#ifndef CONNECT_READER_HGUARD_
#define CONNECT_READER_HGUARD_

#include <serf/reactor/reader.h>

namespace serf {

    /** \brief Reader which creates a new client connection.
     *
     * It will call the factory once, either when the connection is successful
     * to obtain a Reader, or when it has failed to notify it of the error.
     * It will then delete the factory and itself.
     */
    class ConnectReader : public Reader
    {
    public:
        ConnectReader(std::string const& host, unsigned short port, ReaderFactory* factory);
        ~ConnectReader();

        int fd() const;
        bool wantWrite() const;
        void run(Reactor* reactor);

    private:
        std::string host_;
        unsigned short port_;
        int fd_;
        ReaderFactory* factory_;
        int count_;
        bool want_write_;
    };
}

#endif // CONNECT_READER_HGUARD_
