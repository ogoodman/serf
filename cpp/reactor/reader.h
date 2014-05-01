#ifndef READER_HPP_
#define READER_HPP_

#include <string>

namespace serf {

    class Reactor;

    /** \brief Interface for anything which should run when a file descriptor
     *  becomes readable.
     *
     * A Reader must have a selectable file descriptor. Once it is added
     * to a Reactor, its run function will be called whenever its descriptor
     * becomes readable.
     */
    class Reader {
    public:
        virtual ~Reader();

        virtual int fd() const = 0;
        virtual void run(Reactor* reactor) = 0;
    };

    /** \brief Interface for an object which creates a Reader in response
     *  to a new socket connection.
     *
     * The AcceptReader and ConnectReader each need a ReaderFactory
     * in order to do something with the new connection(s) they make.
     */
    class ReaderFactory {
    public:
        virtual ~ReaderFactory();

        virtual void error(std::string const& host, unsigned short port, int code);
        virtual Reader* makeReader(std::string const& host, unsigned short port, int fd) = 0;
    };
}

#endif
