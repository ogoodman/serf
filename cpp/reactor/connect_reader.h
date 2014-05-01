#ifndef CONNECT_READER_HGUARD_
#define CONNECT_READER_HGUARD_

#include <serf/reactor/reader.h>

namespace serf {

    class ConnectReader : public Reader
    {
    public:
        ConnectReader(std::string const& host, unsigned short port, ReaderFactory* factory);
        ~ConnectReader();

        int fd() const;
        void run(Reactor* reactor);

    private:
        std::string host_;
        unsigned short port_;
        int fd_;
        ReaderFactory* factory_;
        int count_;
    };
}

#endif // CONNECT_READER_HGUARD_
