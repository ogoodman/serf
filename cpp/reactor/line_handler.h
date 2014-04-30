#ifndef LINE_HANDLER_HPP_
#define LINE_HANDLER_HPP_

#include <serf/reactor/data_handler.h>

namespace serf {

    /** \brief Assembles fragmented input data into complete lines.
     *
     * The LineHandler assembles data, typically from a DataReader,
     * into lines which it then passes to its child handler.
     */
    class LineHandler : public DataHandler {
    public:
        LineHandler(DataHandler* child) : child_(child) {}
        ~LineHandler() { delete child_; }

        void handle(std::string const& data);

    private:
        DataHandler* child_;
        std::string acc_;
    };
}

#endif
