#ifndef READER_HPP_
#define READER_HPP_

#include <string>

namespace serf {

    class Reactor;

    class Reader {
    public:
        virtual ~Reader();

        virtual int fd() const = 0;
        virtual void run(Reactor* reactor) = 0;
    };

    class ReaderFactory {
    public:
        virtual ~ReaderFactory();

        virtual void error(std::string const& host, unsigned short port, int code);
        virtual Reader* makeReader(std::string const& host, unsigned short port, int fd) = 0;
    };
}

#endif
