#ifndef REACTOR_HPP_
#define REACTOR_HPP_

#include <map>

namespace serf {
    class Reader;

    typedef std::map<int, Reader*> ReaderMap;

    class Reactor {
    public:
        Reactor();

        /** \brief Reactor cleanup.
         *
         * Deletes any remaining readers.
         */
        ~Reactor();

        /** \brief Runs any reader whose file descriptor becomes ready.
         */
        void run();
        /** \brief Makes run() return. Must be called in the reactor loop.
         */
        void stop();

        /** \brief Add a Reader to the reactor.
         *
         * May be called before the reactor is started or from within the
         * reactor loop once it is running.
         * The Reactor takes ownership of the reader. Any existing Reader
         * owning the same descriptor is deleted.
         */
        void addReader(Reader* reader);

        /** \brief Remove the associated Reader.
         *
         * The Reader is deleted. It is up to the Reader to close the
         * file descriptor.
         */
        void removeReader(int fd);

    private:
        ReaderMap readers_;
        bool stop_;
    };
}

#endif
