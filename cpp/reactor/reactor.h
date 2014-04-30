#ifndef REACTOR_HPP_
#define REACTOR_HPP_

#include <map>

namespace serf {
    class Reader;

    typedef std::map<int, Reader*> ReaderMap;

    class Reactor {
    public:
        Reactor();
        ~Reactor();

        void run();
        void stop();

        void addReader(Reader* reader);
        void removeReader(int fd);

    private:
        ReaderMap readers_;
        bool stop_;
    };
}

#endif
