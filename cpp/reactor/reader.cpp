#include <serf/reactor/reader.h>

#include <serf/util/debug.h>

namespace serf {

    Reader::~Reader() {
    }
    
    bool Reader::wantWrite() const {
        return false;
    }

    ReaderFactory::~ReaderFactory() {
    }

    void ReaderFactory::error(std::string const& host, unsigned short port, int code) {
        SAY("Socket error " << code << " " << host << ":" << port);
    }
}
