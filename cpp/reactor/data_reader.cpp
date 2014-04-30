#include <data_reader.h>

#include <errno.h>
#include <sys/types.h>
#include <unistd.h>
#include <data_handler.h>
#include <reactor.h>
#include <debug.h>

using namespace std;

namespace demo {

    const size_t BSIZE=4096;
    char buf[BSIZE];

    DataReader::DataReader(int fd, DataHandler* handler)
        : fd_(fd), handler_(handler) {
    }

    DataReader::~DataReader() {
        delete handler_;
        close(fd_);
    }

    void DataReader::run(Reactor* reactor) {
        ssize_t n_read = read(fd_, buf, BSIZE);
        if (n_read >= 0) {
            handler_->handle(std::string(buf, n_read));
        }
        if (n_read <= 0) {
            reactor->removeReader(fd_);
        }
    }

    int DataReader::fd() const {
        return fd_;
    }
}
