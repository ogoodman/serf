#include <line_handler.h>

namespace demo {

    void LineHandler::handle(std::string const& data) {
        acc_ += data;
        size_t pos = 0, next_pos;
        while (true) {
            next_pos = acc_.find('\n', pos);
            if (next_pos == std::string::npos) break;
            ++next_pos; // go past the '\n'
            child_->handle(acc_.substr(pos, next_pos - pos));
            pos = next_pos;
        }
        acc_.erase(0, pos);
    }

}
