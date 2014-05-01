#include <serf/reactor/reader.h>

#include <serf/debug.h>

namespace serf {

    Reader::~Reader() {
    }

    ReaderFactory::~ReaderFactory() {
    }

    void ReaderFactory::error(std::string const& host, unsigned short port, int code) {
        SAY("Socket error " << code << " " << host << ":" << port);
    }
}
