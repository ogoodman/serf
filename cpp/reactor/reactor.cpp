#include <serf/reactor/reactor.h>

#include <cstddef>
#include <vector>
#include <sys/select.h>
#include <sys/time.h>
#include <serf/reactor/reader.h>

namespace serf {
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
        delete readers_[reader->fd()];
        readers_[reader->fd()] = reader;
    }
    void Reactor::removeReader(int fd) {
        delete readers_[fd];
        readers_.erase(fd);
    }
    void Reactor::run() {
        while (!stop_) {
            fd_set desc_r, desc_w;
            FD_ZERO(&desc_r);
            FD_ZERO(&desc_w);
            ReaderMap::const_iterator i, e=readers_.end();
            int fd_max = 0;
            for (i=readers_.begin(); i != e; ++i) {
                int fd = i->first;
                FD_SET(fd, &desc_r);
                if (i->second->wantWrite()) FD_SET(fd, &desc_w);
                if (fd > fd_max) fd_max = fd;
            }
            select(fd_max + 1, &desc_r, &desc_w, NULL, NULL);

            // Make a list of ready descriptors. We don't want to be
            // iterating over readers_ while running them since they
            // might make changes to it.
            std::vector<int> ready;
            for (i=readers_.begin(); i != e; ++i) {
                int fd = i->first;
                if (FD_ISSET(fd, &desc_r) || FD_ISSET(fd, &desc_w)) {
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
