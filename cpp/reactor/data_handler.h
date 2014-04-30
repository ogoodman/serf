#ifndef DATA_HANDLER_HPP_
#define DATA_HANDLER_HPP_

#include <string>

namespace demo {

    /** \brief Interface for all handlers.
     *
     * Starting with the fragmented data passed by the DataReader
     * to its DataHandler, we will typically assemble the data into
     * a sequence of messages and pass them on to higher level
     * handlers. The basic example is the LineHandler which assembles
     * data into lines, terminated by the newline character.
     */
    class DataHandler {
    public:
        virtual ~DataHandler() {}
        virtual void handle(std::string const& data) = 0;
    };
}

#endif
