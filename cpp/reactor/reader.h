#ifndef READER_HPP_
#define READER_HPP_

namespace demo {

    class Reactor;

    class Reader {
    public:
        virtual ~Reader() {}

        virtual int fd() const = 0;
        virtual void run(Reactor* reactor) = 0;
    };

    class ReaderFactory {
    public:
        virtual ~ReaderFactory() {}

        virtual Reader* makeReader(int fd) = 0;
    };
}

#endif
