#include <reactor.h>

#include <vector>
#include <sys/select.h>
#include <sys/time.h>
#include <reader.h>

namespace demo {
    Reactor::Reactor() : stop_(false) {
    }
    Reactor::~Reactor() {
        ReaderMap::const_iterator i, e=readers_.end();
        for (i=readers_.begin(); i != e; ++i) {
            delete i->second;
        }
    }
    void Reactor::stop() {
        stop_ = true;
    }
    void Reactor::addReader(Reader* reader) {
        readers_[reader->fd()] = reader;
    }
    void Reactor::removeReader(int fd) {
        delete readers_[fd];
        readers_.erase(fd);
    }
    void Reactor::run() {
        while (!stop_) {
            fd_set descriptors;
            FD_ZERO(&descriptors);
            ReaderMap::const_iterator i, e=readers_.end();
            int fd_max = 0;
            for (i=readers_.begin(); i != e; ++i) {
                int fd = i->first;
                FD_SET(fd, &descriptors);
                if (fd > fd_max) fd_max = fd;
            }
            select(fd_max + 1, &descriptors, NULL, NULL, NULL);

            // Copy list of ready descriptors: we don't want to be
            // iterating over readers_ while running them since they
            // might make changes to it.
            std::vector<int> ready;
            for (i=readers_.begin(); i != e; ++i) {
                int fd = i->first;
                if (FD_ISSET(fd, &descriptors)) {
                    ready.push_back(fd);
                }
            }

            for (size_t i=0, n=ready.size(); i < n && !stop_; ++i) {
                int fd = ready[i];
                ReaderMap::const_iterator p = readers_.find(fd);
                if (p != readers_.end()) {
                    p->second->run(this);
                }
            }
        }
    }

}
